import csv
import io
import json
import logging
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.admin.models import CHANGE, DELETION, LogEntry
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.models import Article
from apps.dashboard.forms import ArticleForm, BusinessCoreForm, BusinessPublicInfoForm
from apps.leads.models import MoveLead
from apps.pages.models import Page, PageSection, PageSectionRevision, publish_due_pages
from apps.store.models import Bedrift_info, BusinessImage, PublicBusinessInformation, Review
from apps.store.services import (
    business_lead_entries, business_matches_move, business_usage,
    notify_business_of_assignment, parse_cap, record_business_assignment, usage_stat,
)

logger = logging.getLogger(__name__)


def staff_required(view_func):
    """Restricts a view to authenticated staff users, sending anyone else to the dashboard's own login page (not the public site's or the business-account login)."""
    decorated = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url="dashboard:login",
    )(view_func)
    return wraps(view_func)(decorated)


def superuser_required(view_func):
    """Restricts a view to superusers — for the small set of genuinely
    irreversible actions (permanent delete) that any is_staff user could
    otherwise trigger. Deliberately not built on staff_required's
    user_passes_test: an authenticated staff member who just lacks this
    extra permission should get a 403, not get bounced back to a login
    screen they already passed."""

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect(f"{reverse('dashboard:login')}?next={request.path}")
        if not request.user.is_superuser:
            return HttpResponseForbidden("Denne handlingen krever administratortilgang.")
        return view_func(request, *args, **kwargs)

    return wrapped


DASHBOARD_PAGE_SIZE = 25


def _paginate(request, queryset):
    """Shared pagination for the dashboard's list views — 25 rows/page, page
    number read from ?page= (falls back to the first/last page instead of
    404ing on an out-of-range or non-numeric value, since ?page= is a link
    a user might hand-edit or a stale bookmark)."""
    paginator = Paginator(queryset, DASHBOARD_PAGE_SIZE)
    page_number = request.GET.get("page")
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def _log_deletion(request, obj):
    """Records a permanent delete to Django's built-in LogEntry (the same
    table /admin/ writes to) before the row disappears — the dashboard's
    hard-delete actions previously left no trace of who deleted what."""
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=DELETION,
    )


def _log_change(request, obj, message):
    """Records a non-destructive change to LogEntry (same table as
    _log_deletion) — used for lead status changes, business assignment,
    and archive/restore, so a lead's own history is visible on its detail
    page (see lead_detail's `activity` context)."""
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=CHANGE,
        change_message=message,
    )


def _page_qs(request):
    """The current querystring minus ?page=, for building pagination links
    that preserve whatever filter (?status=, ?active=, ?q=) is active."""
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"&{encoded}" if encoded else ""


LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60


def _login_attempts_key(request, username):
    # Keyed by IP + username (not IP alone) so one flooded account doesn't
    # lock out every other user behind the same NAT/office IP.
    ip = request.META.get("REMOTE_ADDR", "unknown")
    return f"dashboard-login-attempts:{ip}:{username.lower()}"


def dashboard_login(request):
    """Kobly-branded login page for staff-only dashboard access — a separate
    auth flow from the public business-account login. Rate-limited via the
    cache (default LocMemCache is per-process — a multi-worker deployment
    would need a shared cache like Redis for this to actually hold across
    workers) since nothing else in this project throttles login attempts."""
    def _safe_next(url):
        if url and url_has_allowed_host_and_scheme(
            url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return url
        return None

    next_url = _safe_next(request.GET.get("next")) or reverse("dashboard:dashboard_overview")

    if request.user.is_authenticated and request.user.is_staff:
        return redirect(next_url)

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        # staff_required's user_passes_test appends ?next= to the login
        # redirect, but that only survives a GET — carry it through the
        # POST as a hidden field too (see login.html) so a staff member
        # whose session expired mid-task lands back where they were,
        # not on the dashboard overview.
        post_next = _safe_next(request.POST.get("next")) or next_url
        attempts_key = _login_attempts_key(request, username)
        if cache.get(attempts_key, 0) >= LOGIN_MAX_ATTEMPTS:
            error = "For mange mislykkede innloggingsforsøk. Prøv igjen om 15 minutter."
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_staff:
                cache.delete(attempts_key)
                login(request, user)
                return redirect(post_next)
            # cache.add() + cache.incr() instead of get()-then-set(count+1):
            # that was a read-modify-write with no atomicity, so concurrent
            # failed logins for the same username could race and under-count
            # attempts, weakening the lockout. add() only seeds the key if
            # it's not already there (a no-op otherwise), then incr() is a
            # single atomic increment.
            cache.add(attempts_key, 0, LOGIN_LOCKOUT_SECONDS)
            cache.incr(attempts_key)
            error = "Feil brukernavn eller passord, eller ingen tilgang til dashbordet."

    return render(request, "dashboard/login.html", {"error": error, "next": next_url})


@staff_required
@require_POST
def dashboard_logout(request):
    logout(request)
    return redirect("dashboard:login")


def _lead_filters(request):
    """Reads every lead_list filter from the querystring. Shared by
    lead_list and lead_export_csv so the CSV export always matches what's
    currently on screen."""
    return {
        "status": request.GET.get("status", ""),
        "q": request.GET.get("q", "").strip(),
        "business": request.GET.get("business", ""),
        "date_from": request.GET.get("from", ""),
        "date_to": request.GET.get("to", ""),
        "follow_up": request.GET.get("follow_up", ""),
    }


def _apply_lead_filters(queryset, filters):
    if filters["status"] in dict(MoveLead.STATUS_CHOICES):
        queryset = queryset.filter(status=filters["status"])
    if filters["q"]:
        q = filters["q"]
        queryset = queryset.filter(
            Q(navn__icontains=q) | Q(telefon__icontains=q) | Q(epost__icontains=q) | Q(reference__icontains=q)
        )
    if filters["business"]:
        queryset = queryset.filter(
            Q(business_1_id=filters["business"])
            | Q(business_2_id=filters["business"])
            | Q(business_3_id=filters["business"])
        )
    if filters["date_from"]:
        parsed = parse_date(filters["date_from"])
        if parsed:
            queryset = queryset.filter(created_at__date__gte=parsed)
    if filters["date_to"]:
        parsed = parse_date(filters["date_to"])
        if parsed:
            queryset = queryset.filter(created_at__date__lte=parsed)
    if filters["follow_up"] == "1":
        queryset = queryset.filter(follow_up_at__isnull=False, follow_up_at__lte=timezone.localdate())
    return queryset


def _csv_safe(value):
    """Neutralizes CSV/Excel formula injection: navn/fra/til are free text
    submitted by the public wizard (only length-validated, not character-
    restricted — unlike telefon/epost), so a value starting with =/+/-/@
    would otherwise be interpreted as a formula by Excel/LibreOffice the
    moment staff opens an exported leads.csv. Prefixing with a single quote
    is the standard mitigation — spreadsheet apps treat the cell as text
    and don't display the quote."""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        return "'" + text
    return text


def _leads_csv_response(leads):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="leads.csv"'
    # utf-8-sig (a leading BOM) so Excel — the normal way staff actually
    # open a downloaded leads.csv — detects UTF-8 instead of falling back
    # to the system codepage and mangling æ/ø/å.
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow([
        "Referanse", "Navn", "Telefon", "E-post", "Type", "Fra", "Til",
        "Boligtype", "Flyttedato", "Fleksibel", "Status", "Mottatt",
        "Bedrift 1", "Bedrift 2", "Bedrift 3",
    ])
    for lead in leads:
        writer.writerow([
            lead.reference, _csv_safe(lead.navn), lead.telefon, lead.epost,
            lead.get_flytte_type_display(), _csv_safe(lead.fra), _csv_safe(lead.til),
            lead.get_boligtype_display(),
            lead.flyttedato.isoformat() if lead.flyttedato else "",
            "Ja" if lead.fleksibel else "Nei",
            lead.get_status_display(),
            lead.created_at.strftime("%Y-%m-%d %H:%M"),
            lead.business_1.company_name if lead.business_1 else "",
            lead.business_2.company_name if lead.business_2 else "",
            lead.business_3.company_name if lead.business_3 else "",
        ])
    return response


@staff_required
def dashboard_overview(request):
    """Dashboard landing page — key numbers at a glance instead of dropping
    straight onto the raw lead table. Everything here reflects only
    non-archived leads."""
    publish_due_pages()
    today = timezone.localdate()
    active_leads = MoveLead.objects.filter(archived=False)

    context = {
        "new_today": active_leads.filter(created_at__date=today).count(),
        "new_not_contacted": active_leads.filter(status="new").count(),
        "follow_up_due": active_leads.filter(
            follow_up_at__isnull=False, follow_up_at__lte=today
        ).count(),
        "unassigned": active_leads.filter(
            business_1__isnull=True, business_2__isnull=True, business_3__isnull=True
        ).count(),
        "active_business_count": Bedrift_info.objects.filter(active=True).count(),
        "recent_leads": active_leads.order_by("-created_at")[:5],
        "businesses_near_cap": _businesses_near_cap(),
    }
    return render(request, "dashboard/overview.html", context)


def _lead_counts_by_business(queryset):
    """Tallies a MoveLead queryset per business across all 3 assignment
    slots (business_1/2/3 are separate nullable FKs, not a reverse relation
    a single .annotate(Count(...)) could group by directly) in 3 fixed
    GROUP BY queries total, regardless of how many businesses exist —
    replaces what used to be one .count() query per business per metric.
    Always excludes archived leads (every current and foreseeable caller
    wants "how many leads is this business actively dealing with", and a
    caller forgetting to filter archived=False itself is exactly how the
    dashboard overview's "near cap" figure and lead_detail's today/week
    counts used to keep counting a lead after it was archived)."""
    queryset = queryset.filter(archived=False)
    counts = {}
    for field in ("business_1", "business_2", "business_3"):
        rows = queryset.exclude(**{f"{field}__isnull": True}).values(field).annotate(n=Count("id"))
        for row in rows:
            counts[row[field]] = counts.get(row[field], 0) + row["n"]
    return counts


def _businesses_near_cap(threshold=0.8):
    """Active businesses that have used up most of their daily lead cap
    today — surfaced on the overview page so staff notice before a business
    gets overloaded, rather than only finding out from a complaint."""
    today = timezone.localdate()
    businesses = list(Bedrift_info.objects.filter(active=True))
    counts = _lead_counts_by_business(MoveLead.objects.filter(created_at__date=today))

    near = []
    for business in businesses:
        cap = _parse_cap(business.leads_per_day)
        if not cap:
            continue
        count = counts.get(business.pk, 0)
        if count / cap >= threshold:
            near.append({"business": business, "count": count, "cap": cap})
    return near


@staff_required
def global_search(request):
    """Searches leads, businesses, and pages at once from the sidebar's
    search box — previously there was no way to jump straight to a record
    without knowing which section it lived in."""
    query = request.GET.get("q", "").strip()
    leads = businesses = pages = []
    if query:
        leads = MoveLead.objects.filter(
            Q(navn__icontains=query) | Q(telefon__icontains=query)
            | Q(epost__icontains=query) | Q(reference__icontains=query)
        )[:20]
        businesses = Bedrift_info.objects.filter(
            Q(company_name__icontains=query) | Q(email__icontains=query) | Q(city__icontains=query)
        )[:20]
        pages = Page.objects.filter(Q(title__icontains=query) | Q(path__icontains=query))[:20]
    return render(request, "dashboard/search.html", {
        "query": query, "leads": leads, "businesses": businesses, "pages": pages,
    })


@staff_required
def lead_list(request):
    """Filterable, searchable list of every non-archived lead, newest first."""
    filters = _lead_filters(request)
    leads = _apply_lead_filters(MoveLead.objects.filter(archived=False), filters)
    active_base = MoveLead.objects.filter(archived=False)

    status_pill_qs = request.GET.copy()
    status_pill_qs.pop("status", None)
    status_pill_qs.pop("page", None)
    encoded_pill_qs = status_pill_qs.urlencode()

    context = {
        "leads": _paginate(request, leads),
        "page_qs": _page_qs(request),
        "status_pill_qs": f"&{encoded_pill_qs}" if encoded_pill_qs else "",
        "full_qs": request.GET.urlencode(),
        "status_filter": filters["status"],
        "query": filters["q"],
        "business_filter": filters["business"],
        "date_from": filters["date_from"],
        "date_to": filters["date_to"],
        "follow_up_filter": filters["follow_up"],
        "status_choices": MoveLead.STATUS_CHOICES,
        "businesses": Bedrift_info.objects.filter(active=True).order_by("company_name"),
        "total_count": active_base.count(),
        "new_count": active_base.filter(status="new").count(),
        "follow_up_count": active_base.filter(
            follow_up_at__isnull=False, follow_up_at__lte=timezone.localdate()
        ).count(),
    }
    return render(request, "dashboard/list.html", context)


@staff_required
def lead_export_csv(request):
    """CSV of the current filtered lead_list view (same filters, ?status=
    etc.) — separate from lead_bulk_action's "export selected" option."""
    filters = _lead_filters(request)
    leads = _apply_lead_filters(MoveLead.objects.filter(archived=False), filters).order_by("-created_at")
    return _leads_csv_response(leads)


@staff_required
@require_POST
def lead_bulk_action(request):
    """Applies one action to every checked row on the lead list: a status
    change, archiving, or a CSV export of just the selection."""
    action = request.POST.get("action", "")
    ids = request.POST.getlist("lead_ids")
    redirect_qs = request.POST.get("redirect_qs", "")
    redirect_url = reverse("dashboard:lead_list") + (f"?{redirect_qs}" if redirect_qs else "")

    if not ids:
        messages.error(request, "Ingen forespørsler valgt.")
        return redirect(redirect_url)

    leads = MoveLead.objects.filter(pk__in=ids, archived=False)

    if action == "export_csv":
        return _leads_csv_response(leads.order_by("-created_at"))

    if action in dict(MoveLead.STATUS_CHOICES):
        display = dict(MoveLead.STATUS_CHOICES)[action]
        count = 0
        for lead in leads.exclude(status=action):
            lead.status = action
            lead.save(update_fields=["status"])
            _log_change(request, lead, f"Status endret til {display} (samlehandling)")
            count += 1
        messages.success(request, f"Status oppdatert for {count} forespørsler.")
    elif action == "archive":
        count = 0
        for lead in leads:
            lead.archived = True
            lead.archived_at = timezone.now()
            lead.save(update_fields=["archived", "archived_at"])
            _log_change(request, lead, "Arkivert (samlehandling)")
            count += 1
        messages.success(request, f"{count} forespørsler arkivert.")
    else:
        messages.error(request, "Ukjent handling.")

    return redirect(redirect_url)


def _business_matches_lead(business, lead):
    """Sorts the "Tildel til bedrifter" dropdown into recommended/other —
    thin wrapper around apps.store.services.business_matches_move, the same
    heuristic apps.leads.views.wizard now uses to auto-assign a lead the
    moment it's submitted, so staff see the same "would this match?" answer
    here as whatever already ran automatically."""
    return business_matches_move(business, lead.fra, lead.til, lead.flytte_type)


@staff_required
def lead_detail(request, pk):
    lead = get_object_or_404(MoveLead, pk=pk)
    businesses = list(Bedrift_info.objects.filter(active=True).order_by("company_name"))

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    today_counts = _lead_counts_by_business(MoveLead.objects.filter(created_at__date=today))
    week_counts = _lead_counts_by_business(MoveLead.objects.filter(created_at__date__gte=week_start))
    for business in businesses:
        business.matches_lead = _business_matches_lead(business, lead)
        business.today_count = today_counts.get(business.pk, 0)
        business.week_count = week_counts.get(business.pk, 0)

    activity = LogEntry.objects.filter(
        content_type=ContentType.objects.get_for_model(MoveLead), object_id=lead.pk
    ).select_related("user").order_by("-action_time")

    return render(
        request,
        "dashboard/detail.html",
        {
            "lead": lead,
            "status_choices": MoveLead.STATUS_CHOICES,
            "matching_businesses": [b for b in businesses if b.matches_lead],
            "other_businesses": [b for b in businesses if not b.matches_lead],
            "assign_fields": [
                ("business_1", lead.business_1),
                ("business_2", lead.business_2),
                ("business_3", lead.business_3),
            ],
            "activity": activity,
        },
    )


@staff_required
@require_POST
def update_status(request, pk):
    lead = get_object_or_404(MoveLead, pk=pk)
    new_status = request.POST.get("status")
    if new_status in dict(MoveLead.STATUS_CHOICES) and new_status != lead.status:
        lead.status = new_status
        lead.save(update_fields=["status"])
        _log_change(request, lead, f"Status endret til {lead.get_status_display()}")
    return redirect("dashboard:lead_detail", pk=lead.pk)


@staff_required
@require_POST
def lead_update_internal(request, pk):
    """Saves the staff-only notes/follow-up-date panel on the lead detail
    page — separate from the customer-submitted `beskrivelse`."""
    lead = get_object_or_404(MoveLead, pk=pk)
    lead.internal_notes = request.POST.get("internal_notes", "")
    follow_up_raw = request.POST.get("follow_up_at", "")
    lead.follow_up_at = parse_date(follow_up_raw) if follow_up_raw else None
    lead.save(update_fields=["internal_notes", "follow_up_at"])
    return redirect("dashboard:lead_detail", pk=lead.pk)


@staff_required
@require_POST
def lead_archive(request, pk):
    """Soft delete: archives the lead instead of removing it outright — see
    apps/leads/models.py MoveLead.archived. Permanent removal only happens
    from the trash (lead_permanent_delete)."""
    lead = get_object_or_404(MoveLead, pk=pk, archived=False)
    lead.archived = True
    lead.archived_at = timezone.now()
    lead.save(update_fields=["archived", "archived_at"])
    _log_change(request, lead, "Arkivert")
    return redirect("dashboard:lead_list")


@staff_required
def lead_trash(request):
    """Archived leads — recoverable via lead_restore, or permanently
    removed via lead_permanent_delete."""
    leads = MoveLead.objects.filter(archived=True).order_by("-archived_at")
    return render(request, "dashboard/trash.html", {
        "leads": _paginate(request, leads),
        "page_qs": _page_qs(request),
    })


@staff_required
@require_POST
def lead_restore(request, pk):
    lead = get_object_or_404(MoveLead, pk=pk, archived=True)
    lead.archived = False
    lead.archived_at = None
    lead.save(update_fields=["archived", "archived_at"])
    _log_change(request, lead, "Gjenopprettet fra papirkurv")
    return redirect("dashboard:lead_trash")


@superuser_required
@require_POST
def lead_permanent_delete(request, pk):
    """Only reachable for an already-archived lead — permanent delete is
    deliberately not available directly from the live lead list. Restricted
    to superusers (see superuser_required) since, unlike archiving, this
    can't be undone."""
    lead = get_object_or_404(MoveLead, pk=pk, archived=True)
    _log_deletion(request, lead)
    # LeadImage.lead is on_delete=CASCADE, so lead.delete() removes the
    # LeadImage *rows* — but Django never deletes the underlying file from
    # storage on cascade (no post_delete signal/django-cleanup anywhere in
    # this project). Without this, a "permanent" deletion leaves the
    # customer's uploaded photos readable on disk indefinitely.
    for image in lead.images.all():
        image.image.delete(save=False)
    lead.delete()
    return redirect("dashboard:lead_trash")


@staff_required
@require_POST
def lead_assign_businesses(request, pk):
    """Manually assigns a lead to up to 3 businesses. MoveLead is the live
    lead pipeline; store.JobDistribution can't represent this assignment
    since its FK is hard-typed to the separate, unreachable
    core.Flytteforesporsel model (see apps/leads/models.py MoveLead's
    business_1/2/3 fields for why these live directly on the lead)."""
    lead = get_object_or_404(MoveLead, pk=pk)
    fields = ("business_1", "business_2", "business_3")
    values = [request.POST.get(field, "") for field in fields]
    selected = [v for v in values if v]
    if len(selected) != len(set(selected)):
        messages.error(request, "En bedrift kan ikke tildeles flere ganger på samme forespørsel.")
        return redirect("dashboard:lead_detail", pk=lead.pk)

    previously_assigned = {lead.business_1_id, lead.business_2_id, lead.business_3_id}
    for field, value in zip(fields, values):
        if value:
            setattr(lead, field, get_object_or_404(Bedrift_info, pk=value))
        else:
            setattr(lead, field, None)
    lead.save(update_fields=["business_1", "business_2", "business_3"])

    newly_assigned = [
        b for b in [lead.business_1, lead.business_2, lead.business_3]
        if b and b.pk not in previously_assigned
    ]
    for business in newly_assigned:
        record_business_assignment(business)
        try:
            notify_business_of_assignment(business, lead)
        except Exception:
            # A bad/blank business email (e.g. a hand-edited record) must
            # never turn an already-saved assignment into a 500 with no
            # confirmation it happened — same defensive pattern as the
            # wizard's automatic assignment path.
            logger.exception("Failed to notify business %s of lead %s", business.pk, lead.reference)

    names = [b.company_name for b in [lead.business_1, lead.business_2, lead.business_3] if b]
    _log_change(request, lead, f"Tildelt til {', '.join(names)}" if names else "Tildeling fjernet")
    return redirect("dashboard:lead_detail", pk=lead.pk)


@staff_required
def page_list(request):
    """Every page on the site, newest-updated first."""
    publish_due_pages()
    pages = Page.objects.all().order_by("-updated_at")
    context = {"pages": _paginate(request, pages), "page_qs": _page_qs(request)}
    return render(request, "dashboard/page_list.html", context)


# Page-level fields editable from the "Sideinnstillinger" panel on the live
# page (see static/js/inline-edit.js) — path/slug/template_key/status are
# deliberately excluded: status has its own dedicated toggle, and path/slug
# changes are risky enough (routing, uniqueness) to stay out of this v1.
PAGE_META_EDITABLE_FIELDS = {"title", "meta_title", "meta_description"}


@staff_required
@require_POST
def page_update_meta(request, pk):
    """Saves the Sideinnstillinger panel's fields — same shape as
    section_inline_update, but for Page rather than PageSection."""
    page = get_object_or_404(Page, pk=pk)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    update_fields = []
    for field in PAGE_META_EDITABLE_FIELDS:
        if field in data:
            setattr(page, field, data[field])
            update_fields.append(field)
    if not update_fields:
        return JsonResponse({"ok": False, "error": "no_fields"}, status=400)

    # Validate only the fields actually being touched (e.g. meta_title's
    # max_length=70) — a bare setattr()+save(update_fields=...) skips model
    # validation entirely, so without this a direct POST to this endpoint
    # (bypassing the settings panel's client-side maxlength attributes)
    # could silently store an unbounded-length value forever.
    exclude = [f.name for f in Page._meta.fields if f.name not in update_fields]
    try:
        page.full_clean(exclude=exclude, validate_unique=False)
    except ValidationError as exc:
        return JsonResponse({"ok": False, "error": "validation", "details": exc.message_dict}, status=400)

    page.updated_by = request.user
    update_fields += ["updated_by", "updated_at"]
    page.save(update_fields=update_fields)
    return JsonResponse({"ok": True})


@staff_required
@require_POST
def page_toggle_status(request, pk):
    """Publish/unpublish a page — the one page-level action that still
    needs a dashboard control, since it isn't something you'd toggle
    from within the live page itself. Content editing happens inline on
    the page (see section_inline_update); this is the last remaining
    piece of the old form-based editor."""
    page = get_object_or_404(Page, pk=pk)
    page.status = "draft" if page.status == "published" else "published"
    page.updated_by = request.user
    page.save(update_fields=["status", "updated_by", "updated_at"])
    return redirect("dashboard:page_list")


@staff_required
@require_POST
def page_duplicate(request, pk):
    """Clones a Page and every PageSection under it, physically copying
    image files rather than re-pointing at the same file, into a new
    draft Page with a unique slug/path."""
    source = get_object_or_404(Page, pk=pk)

    # path is always derived from slug (never from source.path) so it's
    # guaranteed well-formed — deriving it from source.path directly used
    # to produce a leading-slash-less "-kopi/" for the home page (whose
    # path is just "/"), which the URL router (see demo/urls.py
    # render_page) could never match, so a duplicated page could never
    # actually render. Checking slug uniqueness alone is enough, since
    # path is a deterministic function of it.
    base_slug = f"{source.slug}-kopi"
    slug, suffix = base_slug, 1
    while Page.objects.filter(slug=slug).exists():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    path = f"/{slug}/"

    new_page = Page.objects.create(
        title=f"{source.title} (kopi)",
        slug=slug,
        path=path,
        template_key=source.template_key,
        status="draft",
        updated_by=request.user,
    )

    for section in source.sections.all():
        new_section = PageSection.objects.create(
            page=new_page,
            order=section.order,
            section_type=section.section_type,
            heading=section.heading,
            subheading=section.subheading,
            body_text=section.body_text,
            button_label=section.button_label,
            button_href=section.button_href,
            extra_json=section.extra_json,
        )
        if section.image:
            new_section.image.save(
                section.image.name.rsplit("/", 1)[-1],
                ContentFile(section.image.read()),
                save=True,
            )

    return redirect("dashboard:page_list")


@superuser_required
@require_POST
def page_delete(request, pk):
    page = get_object_or_404(Page, pk=pk)
    _log_deletion(request, page)
    page.delete()
    return redirect("dashboard:page_list")


# ---------------------------------------------------------------------------
# Blog articles — previously only editable via the seed_marketing_content
# management command; no dashboard screen at all let staff add or change one.
@staff_required
def article_list(request):
    """Every blog article, newest-published first."""
    articles = Article.objects.all().order_by("-date")
    context = {"articles": _paginate(request, articles), "page_qs": _page_qs(request)}
    return render(request, "dashboard/article_list.html", context)


@staff_required
def article_add(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save()
            messages.success(request, f'Artikkelen "{article.title}" er opprettet.')
            return redirect("dashboard:article_edit", pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, "dashboard/article_form.html", {"form": form, "article": None})


@staff_required
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Endringene er lagret.")
            return redirect("dashboard:article_edit", pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, "dashboard/article_form.html", {"form": form, "article": article})


@superuser_required
@require_POST
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    _log_deletion(request, article)
    article.delete()
    return redirect("dashboard:article_list")


@staff_required
def business_list(request):
    """Every registered business, filterable by active status and searchable by name/email/city."""
    active_filter = request.GET.get("active", "")
    query = request.GET.get("q", "").strip()

    # Annotate with MoveLead-pipeline counts so "Leads mottatt" reflects both
    # live pipelines (see _business_lead_entries) without an N+1 query per
    # row — each relation is counted with distinct=True so joining all three
    # doesn't inflate the total via row fan-out. filter=Q(...archived=False)
    # excludes archived leads, matching _lead_counts_by_business/
    # business_lead_entries — without it, archiving a lead never actually
    # lowered this column.
    businesses = Bedrift_info.objects.all().order_by("-created_at").annotate(
        movelead_primary_count=Count(
            "assigned_leads_primary", filter=Q(assigned_leads_primary__archived=False), distinct=True
        ),
        movelead_secondary_count=Count(
            "assigned_leads_secondary", filter=Q(assigned_leads_secondary__archived=False), distinct=True
        ),
        movelead_tertiary_count=Count(
            "assigned_leads_tertiary", filter=Q(assigned_leads_tertiary__archived=False), distinct=True
        ),
    )
    if active_filter == "1":
        businesses = businesses.filter(active=True)
    elif active_filter == "0":
        businesses = businesses.filter(active=False)
    if query:
        businesses = businesses.filter(
            Q(company_name__icontains=query) | Q(email__icontains=query) | Q(city__icontains=query)
        )

    context = {
        "businesses": _paginate(request, businesses),
        "page_qs": _page_qs(request),
        "active_filter": active_filter,
        "query": query,
        "total_count": Bedrift_info.objects.count(),
        "active_count": Bedrift_info.objects.filter(active=True).count(),
    }
    return render(request, "dashboard/business_list.html", context)


# Column order the CSV import expects — matches BusinessCoreForm's fields
# (minus tags/internal_notes, not worth requiring for a bulk onboarding
# import) so each row can be validated/saved through the same form the
# single-business edit page uses.
BUSINESS_IMPORT_COLUMNS = [
    "company_name", "company_number", "email", "phone", "website",
    "address", "postal_code", "city", "tiltaleform", "first_name", "last_name",
    "cities", "move_type", "leads_per_day", "leads_per_week", "leads_per_month",
]
MAX_IMPORT_CSV_SIZE_BYTES = 5 * 1024 * 1024  # the whole file is read into memory as a string, unlike a streamed upload


@staff_required
def business_import(request):
    """Bulk-onboards businesses from an uploaded CSV — one row per business,
    validated/saved through BusinessCoreForm so an import can never create
    a row the single-business edit form itself would reject. Imported
    businesses start inactive (the model default), same as any business
    added one at a time."""
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Ingen fil valgt.")
            return redirect("dashboard:business_import")

        if csv_file.size > MAX_IMPORT_CSV_SIZE_BYTES:
            messages.error(request, f"Filen er for stor. Maks {MAX_IMPORT_CSV_SIZE_BYTES // (1024 * 1024)} MB.")
            return redirect("dashboard:business_import")

        try:
            decoded = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "Filen må være UTF-8-kodet CSV.")
            return redirect("dashboard:business_import")

        # csv.DictReader(decoded.splitlines()) used to pre-split the text on
        # every \n/\r *and* less obvious separators (\x0b, \x0c, U+2028,
        # U+2029) before the csv module ever saw it — so a quoted
        # multi-line cell (e.g. an address copied from a spreadsheet as a
        # wrapped cell) silently lost its embedded newline. io.StringIO
        # lets csv's own quoting-aware line reader handle that correctly.
        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        errors = []
        for row_number, row in enumerate(reader, start=2):  # row 1 is the header
            # priority_score has no blank/null option (see apps/store/models.py) —
            # an omitted or empty column shouldn't fail the whole row, so default it.
            data = {field: (row.get(field) or "") for field in BUSINESS_IMPORT_COLUMNS}
            data["priority_score"] = row.get("priority_score") or "0"
            form = BusinessCoreForm(data)
            if form.is_valid():
                form.save()
                created += 1
            else:
                errors.append(f"Rad {row_number}: {form.errors.as_text()}")

        if created:
            messages.success(request, f"{created} bedrifter importert.")
        if errors:
            shown = errors[:10]
            more = f" (og {len(errors) - 10} til)" if len(errors) > 10 else ""
            messages.error(request, f"{len(errors)} rader ble hoppet over — " + " | ".join(shown) + more)
        return redirect("dashboard:business_list")

    return render(request, "dashboard/business_import.html", {"columns": BUSINESS_IMPORT_COLUMNS})


def _business_lead_entries(business):
    """Dashboard-specific wrapper: same shared logic as the partner portal
    (apps/userprofile/views.py), but linking each lead to the dashboard's
    own lead_detail rather than the partner's leads page. See
    apps/store/services.py for the shared implementation."""
    return business_lead_entries(
        business, lead_url_resolver=lambda lead: reverse("dashboard:lead_detail", args=[lead.pk])
    )


_parse_cap = parse_cap
_usage_stat = usage_stat
_business_usage = business_usage


@staff_required
def business_detail(request, pk):
    business = get_object_or_404(Bedrift_info, pk=pk)
    public_info, _ = PublicBusinessInformation.objects.get_or_create(business=business)

    if request.method == "POST":
        core_form = BusinessCoreForm(request.POST, instance=business)
        public_form = BusinessPublicInfoForm(request.POST, request.FILES, instance=public_info)
        if core_form.is_valid() and public_form.is_valid():
            core_form.save()
            public_form.save()
            return redirect("dashboard:business_detail", pk=business.pk)
    else:
        core_form = BusinessCoreForm(instance=business)
        public_form = BusinessPublicInfoForm(instance=public_info)

    lead_entries, movelead_count = _business_lead_entries(business)

    context = {
        "business": business,
        "public_info": public_info,
        "core_form": core_form,
        "public_form": public_form,
        "images": public_info.images.all(),
        "reviews": business.reviews.all(),
        "lead_entries": lead_entries,
        # total_leads_received is only ever incremented for the JobDistribution
        # pipeline (apps/core/views.py send_flytteforesporsel) — add the
        # MoveLead-pipeline count on top so this reflects real combined volume.
        "total_received": business.total_leads_received + movelead_count,
        "usage": _business_usage(business, lead_entries),
    }
    return render(request, "dashboard/business_detail.html", context)


@staff_required
@require_POST
def business_toggle_active(request, pk):
    business = get_object_or_404(Bedrift_info, pk=pk)
    business.active = not business.active
    business.save(update_fields=["active"])
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("dashboard:business_detail", pk=business.pk)


@staff_required
@require_POST
def business_image_add(request, pk):
    business = get_object_or_404(Bedrift_info, pk=pk)
    public_info, _ = PublicBusinessInformation.objects.get_or_create(business=business)
    image_file = request.FILES.get("image")
    if image_file:
        image = BusinessImage(public_info=public_info, image=image_file)
        try:
            image.full_clean()
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            image.save()
    return redirect("dashboard:business_detail", pk=business.pk)


@superuser_required
@require_POST
def business_image_delete(request, pk, image_pk):
    business = get_object_or_404(Bedrift_info, pk=pk)
    image = get_object_or_404(BusinessImage, pk=image_pk, public_info__business=business)
    _log_deletion(request, image)
    image.delete()
    return redirect("dashboard:business_detail", pk=business.pk)


@staff_required
@require_POST
def review_add(request, pk):
    business = get_object_or_404(Bedrift_info, pk=pk)
    name = request.POST.get("name", "").strip()
    comment = request.POST.get("comment", "").strip()
    try:
        rating = int(request.POST.get("rating", 5))
    except (TypeError, ValueError):
        rating = 5
    if rating not in (1, 2, 3, 4, 5):
        rating = 5
    if name and comment:
        Review.objects.create(business=business, name=name, comment=comment, rating=rating)
    return redirect("dashboard:business_detail", pk=business.pk)


@staff_required
@require_POST
def review_edit(request, pk, review_pk):
    business = get_object_or_404(Bedrift_info, pk=pk)
    review = get_object_or_404(Review, pk=review_pk, business=business)
    review.name = request.POST.get("name", review.name).strip()
    review.comment = request.POST.get("comment", review.comment).strip()
    try:
        rating = int(request.POST.get("rating", review.rating))
    except (TypeError, ValueError):
        rating = review.rating
    if rating not in (1, 2, 3, 4, 5):
        rating = review.rating
    review.rating = rating
    review.save(update_fields=["name", "comment", "rating"])
    return redirect("dashboard:business_detail", pk=business.pk)


@superuser_required
@require_POST
def review_delete(request, pk, review_pk):
    business = get_object_or_404(Bedrift_info, pk=pk)
    review = get_object_or_404(Review, pk=review_pk, business=business)
    _log_deletion(request, review)
    review.delete()
    return redirect("dashboard:business_detail", pk=business.pk)


# Every text field a PageSection can be edited into inline, straight from the
# live page (see inline-edit.js). Whitelisted so the POST body can never
# write to a field outside this set (e.g. section_type, page, extra_json).
INLINE_EDITABLE_FIELDS = {"heading", "subheading", "body_text", "button_label", "button_href"}

# Scalar (non-list) extra_json keys that are also inline-editable, per
# section_type — e.g. the hero's eyebrow/HeroCard text and trust's secondary
# CTA, which live in extra_json rather than one of PageSection's own flat
# fields but are still single strings, not list items. Posted as
# field="extra_json.<key>" to tell them apart from INLINE_EDITABLE_FIELDS.
EXTRA_JSON_SCALAR_FIELDS = {
    "hero": {"eyebrow", "card_title", "card_body"},
    "trust": {"secondary_label", "secondary_href"},
}
MAX_EXTRA_JSON_SCALAR_LENGTH = 300


@staff_required
@require_POST
def section_inline_update(request, pk):
    """Saves one text field of one PageSection, called from a page's own
    contenteditable elements (apps/core/templates/core/home.html) rather
    than from the dashboard's own page editor."""
    section = get_object_or_404(PageSection, pk=pk)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    field = data.get("field")
    value = data.get("value", "")

    if isinstance(field, str) and field.startswith("extra_json."):
        key = field[len("extra_json."):]
        if key not in EXTRA_JSON_SCALAR_FIELDS.get(section.section_type, set()):
            return JsonResponse({"ok": False, "error": "invalid_field"}, status=400)
        if not isinstance(value, str) or len(value) > MAX_EXTRA_JSON_SCALAR_LENGTH:
            return JsonResponse({"ok": False, "error": "invalid_value"}, status=400)
        # Row-locked read-modify-write — see _locked_section docstring: two
        # concurrent edits to this section's extra_json (a scalar field here,
        # a list item elsewhere) must not let one save silently clobber the
        # other's, since both start from an in-memory copy of the whole blob.
        with transaction.atomic():
            section = _locked_section(pk)
            section.extra_json[key] = value
            section.save(update_fields=["extra_json"])
        _touch_page(section, request.user)
        return JsonResponse({"ok": True})

    if field not in INLINE_EDITABLE_FIELDS:
        return JsonResponse({"ok": False, "error": "invalid_field"}, status=400)

    # Validate just this one field (e.g. heading's max_length) before
    # writing it — setattr()+save(update_fields=[field]) alone skips model
    # validation, so an edit longer than the field allows would otherwise
    # save silently instead of being rejected.
    previous_value = getattr(section, field)
    setattr(section, field, value)
    exclude = [f.name for f in PageSection._meta.fields if f.name != field]
    try:
        section.full_clean(exclude=exclude, validate_unique=False)
    except ValidationError as exc:
        setattr(section, field, previous_value)
        return JsonResponse({"ok": False, "error": "validation", "details": exc.message_dict}, status=400)

    if field == "button_href" and value and not (value.startswith("/") or value.startswith("http://") or value.startswith("https://")):
        setattr(section, field, previous_value)
        return JsonResponse({"ok": False, "error": "validation", "details": {"button_href": ["Lenken må starte med / eller http(s)://."]}}, status=400)

    if previous_value != value:
        PageSectionRevision.objects.create(
            section=section, field=field, previous_value=previous_value, changed_by=request.user,
        )
    section.save(update_fields=[field])
    section.page.updated_by = request.user
    section.page.save(update_fields=["updated_by", "updated_at"])
    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# Per-item editing for a section's extra_json list content (stats tiles, how-
# it-works steps, testimonial cards, service cards, city links, FAQ pairs) —
# section_inline_update above only ever covered the section's own flat
# heading/subheading/body_text/button_* fields, never the list items inside
# extra_json, so e.g. an individual FAQ question or testimonial photo had no
# edit path at all. Every list-shaped section_type gets a field spec (which
# keys are editable and what kind of input they need) and a default row
# (for "legg til") — the container key ("items" vs "steps") is the one
# inconsistency inherited from how apps/pages seed_home_page_sections.py and
# core/home.html already named these two differently.
LIST_ITEM_CONTAINER_KEY = {
    "stats": "items",
    "how_it_works": "steps",
    "testimonials": "items",
    "services": "items",
    "cities": "items",
    "faq": "items",
}

LIST_ITEM_FIELD_SPECS = {
    "stats": [("value", "text", "Verdi"), ("label", "text", "Etikett")],
    "how_it_works": [("title", "text", "Tittel"), ("body", "textarea", "Tekst"), ("image", "image", "Illustrasjon")],
    "testimonials": [("quote", "textarea", "Sitat"), ("name", "text", "Navn"), ("meta", "text", "Undertekst"), ("image", "image", "Bilde")],
    "services": [("title", "text", "Tittel"), ("body", "textarea", "Tekst")],
    "cities": [("name", "text", "Bynavn"), ("href", "text", "Lenke")],
    "faq": [("question", "text", "Spørsmål"), ("answer", "textarea", "Svar")],
}

DEFAULT_LIST_ITEM = {
    "stats": {"value": "0", "label": "Ny statistikk"},
    "how_it_works": {"title": "Nytt steg", "body": "", "image": ""},
    "testimonials": {"quote": "", "name": "Nytt navn", "meta": "", "image": ""},
    "services": {"title": "Ny tjeneste", "body": ""},
    "cities": {"name": "Ny by", "href": "/"},
    "faq": {"question": "Nytt spørsmål?", "answer": ""},
}

MAX_LIST_ITEMS = 12  # sanity cap so a mis-clicked "legg til" can't be spammed into an unbounded list
MAX_ITEM_FIELD_LENGTH = 500  # generous but bounded — these are JSON strings with no model max_length to lean on


def _list_items(section):
    """The mutable list this section_type's extra_json list content lives
    under (see LIST_ITEM_CONTAINER_KEY) — creates it if missing rather than
    erroring, since a freshly-created section legitimately starts with {}."""
    key = LIST_ITEM_CONTAINER_KEY[section.section_type]
    return section.extra_json.setdefault(key, [])


def _locked_section(pk):
    """Fetches a PageSection row-locked for the rest of the current
    transaction.atomic() block — call this immediately before reading the
    extra_json you're about to read-modify-write, not the earlier,
    unlocked fetch used for upfront validation (section_type lookups, etc).

    Regression note: every extra_json edit endpoint (scalar fields here,
    and every per-item list endpoint below) used to fetch a section,
    mutate a Python dict in memory, then save(update_fields=["extra_json"])
    with no locking at all. Two concurrent edits to the same section (two
    staff tabs open on the same page, or two rapid clicks) each start from
    their own in-memory copy of the *whole* extra_json blob — whichever
    save() lands second silently overwrites whatever the first one added,
    with no error and no conflict indication.

    select_for_update() gives real row-level locking on Postgres/MySQL. On
    SQLite (this project's dev/test backend) it's a documented no-op, but
    SQLite only allows one writer at a time file-wide, so a write inside
    transaction.atomic() here still serializes against another concurrent
    write to the same row in practice — this fix holds on both backends,
    just via a coarser lock on SQLite.
    """
    return get_object_or_404(PageSection.objects.select_for_update(), pk=pk)


def _touch_page(section, user):
    section.page.updated_by = user
    section.page.save(update_fields=["updated_by", "updated_at"])


@staff_required
@require_POST
def section_list_item_update(request, pk, index):
    """Saves one or more fields of one item inside a list-shaped section's
    extra_json (e.g. one FAQ pair's question+answer, one testimonial's
    quote/name/meta) — the per-item counterpart to section_inline_update,
    which only ever reached the section's own flat fields."""
    section = get_object_or_404(PageSection, pk=pk)
    spec = LIST_ITEM_FIELD_SPECS.get(section.section_type)
    if not spec:
        return JsonResponse({"ok": False, "error": "not_a_list_section"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    allowed_fields = {name for name, kind, label in spec if kind != "image"}  # image fields go through section_list_item_image instead
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return JsonResponse({"ok": False, "error": "no_fields"}, status=400)
    for value in updates.values():
        if not isinstance(value, str) or len(value) > MAX_ITEM_FIELD_LENGTH:
            return JsonResponse({"ok": False, "error": "invalid_value"}, status=400)

    with transaction.atomic():
        section = _locked_section(pk)
        items = _list_items(section)
        if not (0 <= index < len(items)):
            return JsonResponse({"ok": False, "error": "index_out_of_range"}, status=404)
        items[index].update(updates)
        section.save(update_fields=["extra_json"])
    _touch_page(section, request.user)
    return JsonResponse({"ok": True})


@staff_required
@require_POST
def section_list_item_add(request, pk):
    """Appends one default row to a list-shaped section — the admin edits
    its real content afterward via section_list_item_update."""
    section = get_object_or_404(PageSection, pk=pk)
    if section.section_type not in LIST_ITEM_FIELD_SPECS:
        return JsonResponse({"ok": False, "error": "not_a_list_section"}, status=400)

    with transaction.atomic():
        section = _locked_section(pk)
        items = _list_items(section)
        if len(items) >= MAX_LIST_ITEMS:
            return JsonResponse({"ok": False, "error": "max_items_reached"}, status=400)
        items.append(dict(DEFAULT_LIST_ITEM[section.section_type]))
        new_index = len(items) - 1
        section.save(update_fields=["extra_json"])
    _touch_page(section, request.user)
    return JsonResponse({"ok": True, "index": new_index})


@staff_required
@require_POST
def section_list_item_delete(request, pk, index):
    """Removes one item from a list-shaped section. Deliberately not
    revision-tracked (PageSectionRevision only models the section's own flat
    fields) — deleting the wrong item just means adding it back by hand."""
    section = get_object_or_404(PageSection, pk=pk)
    if section.section_type not in LIST_ITEM_FIELD_SPECS:
        return JsonResponse({"ok": False, "error": "not_a_list_section"}, status=400)

    with transaction.atomic():
        section = _locked_section(pk)
        items = _list_items(section)
        if not (0 <= index < len(items)):
            return JsonResponse({"ok": False, "error": "index_out_of_range"}, status=404)
        items.pop(index)
        section.save(update_fields=["extra_json"])
    _touch_page(section, request.user)
    return JsonResponse({"ok": True})


@staff_required
@require_POST
def section_list_item_image(request, pk, index):
    """Uploads/replaces one list item's image — stored as a real media file
    (unlike the hardcoded step/testimonial photos this project ships with,
    which are static/ filenames referenced by extra_json.image as a bare
    filename). core/home.html tells the two apart at render time by whether
    the value starts with "/" (a real upload's media URL) or not (one of
    the shipped static/images/home/ filenames)."""
    section = get_object_or_404(PageSection, pk=pk)
    spec = LIST_ITEM_FIELD_SPECS.get(section.section_type, [])
    if not any(kind == "image" for _, kind, _ in spec):
        return JsonResponse({"ok": False, "error": "not_an_image_section"}, status=400)

    items = _list_items(section)
    if not (0 <= index < len(items)):
        return JsonResponse({"ok": False, "error": "index_out_of_range"}, status=404)

    image_file = request.FILES.get("image")
    if not image_file:
        return JsonResponse({"ok": False, "error": "no_file"}, status=400)

    from django.core.files.storage import default_storage
    from apps.store.models import validate_max_file_size
    from django.core.files.images import get_image_dimensions

    try:
        validate_max_file_size(image_file)
        get_image_dimensions(image_file)  # raises/returns None on a non-image — cheap "is this real" check, same idea as ImageField's own validation
    except ValidationError as exc:
        return JsonResponse({"ok": False, "error": "validation", "details": exc.messages}, status=400)
    if get_image_dimensions(image_file) is None:
        return JsonResponse({"ok": False, "error": "not_an_image"}, status=400)

    # File I/O happens above, outside any DB lock — only the final
    # read-modify-write of extra_json (the part actually racy against a
    # concurrent edit) needs one, and holding a row lock across a file
    # upload would only widen the contention window pointlessly.
    saved_path = default_storage.save(f"pages/section-items/{image_file.name}", image_file)
    saved_url = default_storage.url(saved_path)
    with transaction.atomic():
        section = _locked_section(pk)
        items = _list_items(section)
        if not (0 <= index < len(items)):
            return JsonResponse({"ok": False, "error": "index_out_of_range"}, status=404)
        items[index]["image"] = saved_url
        section.save(update_fields=["extra_json"])
    _touch_page(section, request.user)
    return JsonResponse({"ok": True, "url": saved_url})


@staff_required
def page_history(request, pk):
    """Every recorded edit to this page's sections (see
    section_inline_update), grouped by section, newest first — with a
    Gjenopprett (restore) action on each one."""
    page = get_object_or_404(Page, pk=pk)
    sections = page.sections.all().prefetch_related("revisions__changed_by")
    return render(request, "dashboard/page_history.html", {"page": page, "sections": sections})


@staff_required
@require_POST
def section_revision_restore(request, pk):
    """Reverts one field on a section back to a prior recorded value. The
    value it replaces is itself snapshotted first, so undoing a revert is
    just restoring the newer revision that gets created here."""
    revision = get_object_or_404(PageSectionRevision, pk=pk)
    section = revision.section
    current_value = getattr(section, revision.field)
    if current_value != revision.previous_value:
        PageSectionRevision.objects.create(
            section=section, field=revision.field, previous_value=current_value, changed_by=request.user,
        )
    setattr(section, revision.field, revision.previous_value)
    section.save(update_fields=[revision.field])
    section.page.updated_by = request.user
    section.page.save(update_fields=["updated_by", "updated_at"])
    messages.success(request, f"«{revision.get_field_display()}» gjenopprettet.")
    return redirect("dashboard:page_history", pk=section.page.pk)


@staff_required
@require_POST
def page_schedule_publish(request, pk):
    """Sets or clears a page's scheduled publish time (see
    apps/pages/models.py publish_due_pages for how it actually takes
    effect). An empty value cancels a pending schedule without touching the
    page's current status."""
    page = get_object_or_404(Page, pk=pk)
    raw = request.POST.get("publish_at", "")
    if not raw:
        page.publish_at = None
        page.save(update_fields=["publish_at"])
        messages.success(request, "Planlagt publisering avbrutt.")
        return redirect("dashboard:page_list")

    parsed = parse_datetime(raw)
    if not parsed:
        messages.error(request, "Ugyldig dato/klokkeslett.")
        return redirect("dashboard:page_list")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)

    if parsed <= timezone.now():
        # Already due — publish immediately rather than schedule a no-op.
        page.status = "published"
        page.publish_at = None
        page.updated_by = request.user
        page.save(update_fields=["status", "publish_at", "updated_by", "updated_at"])
        messages.success(request, "Siden er publisert.")
    else:
        page.publish_at = parsed
        page.save(update_fields=["publish_at"])
        messages.success(request, f"Publisering planlagt til {timezone.localtime(parsed):%d.%m.%Y %H:%M}.")
    return redirect("dashboard:page_list")


@staff_required
def activity_log(request):
    """Read-only history of permanent deletes — both from the dashboard
    (leads, pages, business images, reviews; see _log_deletion) and from
    /admin/, since both write to the same LogEntry table Django already
    ships with, rather than a new model."""
    entries = LogEntry.objects.filter(action_flag=DELETION).select_related("user", "content_type").order_by("-action_time")
    return render(request, "dashboard/activity_log.html", {"entries": _paginate(request, entries)})
