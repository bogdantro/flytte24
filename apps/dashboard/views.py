import csv
import json
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
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.dashboard.forms import BusinessCoreForm, BusinessPublicInfoForm
from apps.leads.models import MoveLead
from apps.pages.models import Page, PageSection, PageSectionRevision, publish_due_pages
from apps.store.models import Bedrift_info, BusinessImage, PublicBusinessInformation, Review
from apps.store.services import business_lead_entries, business_usage, parse_cap, usage_stat


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
            cache.set(attempts_key, cache.get(attempts_key, 0) + 1, LOGIN_LOCKOUT_SECONDS)
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


def _leads_csv_response(leads):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="leads.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Referanse", "Navn", "Telefon", "E-post", "Type", "Fra", "Til",
        "Boligtype", "Flyttedato", "Fleksibel", "Status", "Mottatt",
        "Bedrift 1", "Bedrift 2", "Bedrift 3",
    ])
    for lead in leads:
        writer.writerow([
            lead.reference, lead.navn, lead.telefon, lead.epost,
            lead.get_flytte_type_display(), lead.fra, lead.til,
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
    replaces what used to be one .count() query per business per metric."""
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
    """Heuristic used only to sort the "Tildel til bedrifter" dropdown —
    does NOT touch the live matching algorithm in
    apps/core/views.py send_flytteforesporsel. MoveLead stores full
    addresses (fra/til), not a separate city field like the old pipeline's
    Flytteforesporsel, so city matching is substring- rather than
    equality-based."""
    business_cities = [c.strip().lower() for c in (business.cities or "").split(",") if c.strip()]
    business_move_types = [m.strip().lower() for m in (business.move_type or "").split(",") if m.strip()]
    if not business_cities or not business_move_types:
        return False
    destination = (lead.til or "").lower()
    origin = (lead.fra or "").lower()
    city_match = any(city in destination or city in origin for city in business_cities)
    type_match = lead.flytte_type.lower() in business_move_types
    return city_match and type_match


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
    lead.delete()
    return redirect("dashboard:lead_trash")


def _notify_business_of_assignment(business, lead):
    """Emails a business when it's newly assigned a lead — previously the
    only way a business found out was logging into their own account and
    checking. fail_silently=True: a broken SMTP config shouldn't block the
    assignment itself, only the notification. SMS is not implemented (no
    SMS provider is configured anywhere in this project)."""
    subject = f"Ny flytteforespørsel tildelt — {lead.reference}"
    message = (
        f"Hei {business.company_name},\n\n"
        "Dere har blitt tildelt en ny flytteforespørsel via Kobly.\n\n"
        f"Referanse: {lead.reference}\n"
        f"Navn: {lead.navn}\n"
        f"Telefon: {lead.telefon}\n"
        f"E-post: {lead.epost}\n"
        f"Fra: {lead.fra}\n"
        f"Til: {lead.til}\n"
        f"Type: {lead.get_flytte_type_display()}\n\n"
        "Logg inn på Kobly for mer informasjon."
    )
    send_mail(subject, message, None, [business.email], fail_silently=True)


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
        _notify_business_of_assignment(business, lead)

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


@staff_required
def business_list(request):
    """Every registered business, filterable by active status and searchable by name/email/city."""
    active_filter = request.GET.get("active", "")
    query = request.GET.get("q", "").strip()

    # Annotate with MoveLead-pipeline counts so "Leads mottatt" reflects both
    # live pipelines (see _business_lead_entries) without an N+1 query per
    # row — each relation is counted with distinct=True so joining all three
    # doesn't inflate the total via row fan-out.
    businesses = Bedrift_info.objects.all().order_by("-created_at").annotate(
        movelead_primary_count=Count("assigned_leads_primary", distinct=True),
        movelead_secondary_count=Count("assigned_leads_secondary", distinct=True),
        movelead_tertiary_count=Count("assigned_leads_tertiary", distinct=True),
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

        try:
            decoded = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "Filen må være UTF-8-kodet CSV.")
            return redirect("dashboard:business_import")

        reader = csv.DictReader(decoded.splitlines())
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

    if previous_value != value:
        PageSectionRevision.objects.create(
            section=section, field=field, previous_value=previous_value, changed_by=request.user,
        )
    section.save(update_fields=[field])
    section.page.updated_by = request.user
    section.page.save(update_fields=["updated_by", "updated_at"])
    return JsonResponse({"ok": True})


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
