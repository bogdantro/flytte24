from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.dashboard.forms import PageForm, PageSectionForm
from apps.leads.models import MoveLead
from apps.pages.models import Page, PageSection


def staff_required(view_func):
    """Restricts a view to authenticated staff users, sending anyone else to the dashboard's own login page (not the public site's or the business-account login)."""
    decorated = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url="dashboard:login",
    )(view_func)
    return wraps(view_func)(decorated)


def dashboard_login(request):
    """Kobly-branded login page for staff-only dashboard access — a separate auth flow from the public business-account login."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard:lead_list")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect("dashboard:lead_list")
        error = "Feil brukernavn eller passord, eller ingen tilgang til dashbordet."

    return render(request, "dashboard/login.html", {"error": error})


@staff_required
def dashboard_logout(request):
    logout(request)
    return redirect("dashboard:login")


@staff_required
def lead_list(request):
    """Filterable list of every submitted lead, newest first (MoveLead's own default ordering)."""
    status_filter = request.GET.get("status", "")
    leads = MoveLead.objects.all()
    if status_filter in dict(MoveLead.STATUS_CHOICES):
        leads = leads.filter(status=status_filter)

    context = {
        "leads": leads,
        "status_filter": status_filter,
        "status_choices": MoveLead.STATUS_CHOICES,
        "total_count": MoveLead.objects.count(),
        "new_count": MoveLead.objects.filter(status="new").count(),
    }
    return render(request, "dashboard/list.html", context)


@staff_required
def lead_detail(request, pk):
    lead = get_object_or_404(MoveLead, pk=pk)
    return render(
        request,
        "dashboard/detail.html",
        {"lead": lead, "status_choices": MoveLead.STATUS_CHOICES},
    )


@staff_required
@require_POST
def update_status(request, pk):
    lead = get_object_or_404(MoveLead, pk=pk)
    new_status = request.POST.get("status")
    if new_status in dict(MoveLead.STATUS_CHOICES):
        lead.status = new_status
        lead.save(update_fields=["status"])
    return redirect("dashboard:lead_detail", pk=lead.pk)


@staff_required
@require_POST
def delete_lead(request, pk):
    lead = get_object_or_404(MoveLead, pk=pk)
    lead.delete()
    return redirect("dashboard:lead_list")


@staff_required
def page_list(request):
    """Every page on the site, newest-updated first."""
    pages = Page.objects.all().order_by("-updated_at")
    return render(request, "dashboard/page_list.html", {"pages": pages})


@staff_required
def page_edit(request, pk):
    page = get_object_or_404(Page, pk=pk)
    sections = list(page.sections.all())

    if request.method == "POST":
        page_form = PageForm(request.POST, instance=page)
        section_forms = [
            PageSectionForm(request.POST, request.FILES, instance=s, prefix=f"section-{s.pk}")
            for s in sections
        ]
        if page_form.is_valid() and all(f.is_valid() for f in section_forms):
            saved_page = page_form.save(commit=False)
            saved_page.updated_by = request.user
            saved_page.save()
            for f in section_forms:
                f.save()
            return redirect("dashboard:page_edit", pk=page.pk)
    else:
        page_form = PageForm(instance=page)
        section_forms = [
            PageSectionForm(instance=s, prefix=f"section-{s.pk}") for s in sections
        ]

    return render(
        request,
        "dashboard/page_edit.html",
        {"page": page, "page_form": page_form, "section_forms": section_forms},
    )


@staff_required
@require_POST
def page_duplicate(request, pk):
    """Clones a Page and every PageSection under it, physically copying
    image files rather than re-pointing at the same file, into a new
    draft Page with a unique slug/path."""
    source = get_object_or_404(Page, pk=pk)

    base_slug = f"{source.slug}-kopi"
    base_path = source.path.rstrip("/") + "-kopi/"
    slug, path, suffix = base_slug, base_path, 1
    while Page.objects.filter(slug=slug).exists() or Page.objects.filter(path=path).exists():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
        path = source.path.rstrip("/") + f"-kopi-{suffix}/"

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

    return redirect("dashboard:page_edit", pk=new_page.pk)


@staff_required
@require_POST
def page_delete(request, pk):
    page = get_object_or_404(Page, pk=pk)
    page.delete()
    return redirect("dashboard:page_list")
