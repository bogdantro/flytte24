from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.core.forms import CITY_CHOICES, MOVE_TYPE_CHOICES
from apps.store.models import Bedrift_info, BusinessImage, PublicBusinessInformation
from apps.store.services import business_lead_entries, business_usage
from apps.userprofile.models import Profile

from .forms import BusinessSelfEditForm, BusinessImageForm, PublicBusinessInformationForm, SignUpForm, UserprofileForm


def signup(request, backend='django.contrib.auth.backends.ModelBackend'):
    # Extract email from query string (sent from the registration flow)
    email_param = request.GET.get('email')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        userprofileform = UserprofileForm(request.POST)

        if form.is_valid() and userprofileform.is_valid():
            user = form.save()
            user.backend = backend
            login(request, user)

            # Save user profile
            userprofile = userprofileform.save(commit=False)
            userprofile.user = user
            userprofile.save()

            # Create a membership profile (if you use this structure)
            profile = Profile.objects.create(user=user)

            # Link Bedrift_info (business data) by the email actually
            # submitted (form.cleaned_data['username'] — the "E-post" field
            # on core/signup.html) rather than re-reading ?email= from the
            # URL: if the user edited the pre-filled field before
            # submitting, re-reading the stale query param would either
            # link the wrong Bedrift_info row or silently link none at all.
            submitted_email = form.cleaned_data.get('username', '')
            business = Bedrift_info.objects.filter(email__iexact=submitted_email).last()
            if business:
                business.user = user
                business.save(update_fields=["user"])

            return redirect('myaccount')

    else:
        form = SignUpForm()
        userprofileform = UserprofileForm()

        # Autofill email from URL if it exists
        if email_param:
            form.fields['username'].initial = email_param

    return render(request, 'core/signup.html', {
        'form': form,
        'userprofileform': userprofileform,
    })


@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
def myaccount(request):
    """Account overview — status and its most recent leads. Combines both
    lead pipelines the same way the staff dashboard does
    (apps.store.services), so a partner's own numbers always match what
    staff see for them. No self-set daily/weekly/monthly cap UI here
    anymore — that whole "leads grense" feature was removed from the
    account portal (still exists as a staff-only field/dashboard concept,
    apps.store.services.business_usage, just no longer business-editable
    or business-visible)."""
    business = getattr(request.user, "bedrift_info", None)
    context = {"business": business, "active_nav": "overview"}

    if business:
        lead_entries, movelead_count = business_lead_entries(business, lead_url_resolver=_business_lead_url)
        context.update({
            "leads_today": business_usage(business, lead_entries)["today"]["count"],
            "recent_leads": lead_entries[:5],
            "total_received": business.total_leads_received + movelead_count,
            "review_count": business.reviews.count(),
        })

    return render(request, "core/myaccount.html", context)


@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
def edit_public_profile(request):
    """One page, two forms saved together: the business's own core info
    (BusinessSelfEditForm — company name, contact, address, cities/move
    types covered) and its public profile (logo/about/FAQ). Images and
    reviews are managed by their own small endpoints/read-only display
    below, mirroring apps.dashboard.views.business_detail's layout."""
    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return redirect("myaccount")

    public_info, _ = PublicBusinessInformation.objects.get_or_create(business=business)

    if request.method == "POST":
        core_form = BusinessSelfEditForm(request.POST, instance=business)
        public_form = PublicBusinessInformationForm(request.POST, request.FILES, instance=public_info)
        if core_form.is_valid() and public_form.is_valid():
            core_form.save()
            public_form.save()
            messages.success(request, "Endringene er lagret.")
            return redirect("edit_public_profile")
    else:
        core_form = BusinessSelfEditForm(instance=business)
        public_form = PublicBusinessInformationForm(instance=public_info)

    public_path = reverse('public_business_profile', args=[business.id])
    public_url = request.build_absolute_uri(public_path)

    current_move_types = {v.strip() for v in (business.move_type or "").split(",") if v.strip()}
    current_cities = {v.strip() for v in (business.cities or "").split(",") if v.strip()}

    return render(request, "core/accountPages/business_edit_profile.html", {
        "core_form": core_form,
        "public_form": public_form,
        "public_info": public_info,
        "business": business,
        "public_url": public_url,
        "images": public_info.images.all(),
        "reviews": business.reviews.all(),
        "move_type_choices": MOVE_TYPE_CHOICES,
        "city_choices": CITY_CHOICES,
        "current_move_types": current_move_types,
        "current_cities": current_cities,
        "active_nav": "profile",
    })


@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
@require_POST
def update_business_coverage(request):
    """AJAX-only save for the Bedriftsprofil page's "Dekning" (coverage)
    section — services offered + cities covered, as the exact same
    pill-button checkboxes as the become-a-partner wizard's step 1/2
    (apps.core.forms MOVE_TYPE_CHOICES/CITY_CHOICES — reused directly
    rather than a second copy of the same lists), saved the instant a pill
    is toggled instead of needing the page's main form submit/reload."""
    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return JsonResponse({"ok": False}, status=403)

    move_type = request.POST.getlist("move_type")
    cities = request.POST.getlist("cities")
    valid_move_types = {value for value, _label in MOVE_TYPE_CHOICES}
    valid_cities = {value for value, _label in CITY_CHOICES}
    if not set(move_type) <= valid_move_types or not set(cities) <= valid_cities:
        return JsonResponse({"ok": False, "error": "invalid_choice"}, status=400)

    business.move_type = ", ".join(move_type)
    business.cities = ", ".join(cities)
    business.save(update_fields=["move_type", "cities"])
    return JsonResponse({"ok": True})


@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
@require_POST
def business_image_add(request):
    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return redirect("myaccount")

    public_info, _ = PublicBusinessInformation.objects.get_or_create(business=business)
    if request.FILES.get("image"):
        # Regression note: this used to build a bare BusinessImage and call
        # .full_clean() on it directly, which only runs the model field's
        # own validators (just a size check — validate_max_file_size).
        # Plain django.db.models.ImageField has no Pillow-based "is this
        # actually a decodable image" check at all; that check lives only
        # on forms.ImageField (django.forms.fields.ImageField.to_python).
        # Going through BusinessImageForm — a real ModelForm — means the
        # bound form field actually verifies the upload decodes as an
        # image before it's ever saved, instead of accepting any file
        # under the size cap (an .svg, .html, or arbitrary blob).
        form = BusinessImageForm(request.POST, request.FILES, instance=BusinessImage(public_info=public_info))
        if form.is_valid():
            form.save()
        else:
            messages.error(request, " ".join(msg for errors in form.errors.values() for msg in errors))
    return redirect("edit_public_profile")


@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
@require_POST
def business_image_delete(request, image_pk):
    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return redirect("myaccount")

    image = get_object_or_404(BusinessImage, pk=image_pk, public_info__business=business)
    image.delete()
    return redirect("edit_public_profile")


@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
def foresporsel_database(request):
    """The business's own leads list — combines both pipelines (see
    apps.store.services.business_lead_entries) so a lead assigned via
    either the old direct-form flow or the dashboard's wizard flow shows up
    here, not just one of them. Used to also handle a POST updating the
    business's self-reported daily/weekly/monthly lead cap — that whole
    "leads grense" feature was removed from the account portal, so this is
    a GET-only view now."""
    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return redirect("login")

    lead_entries, movelead_count = business_lead_entries(business, lead_url_resolver=_business_lead_url)
    return render(request, "core/accountPages/foresporsel_database.html", {
        "business": business,
        "lead_entries": lead_entries,
        "total_received": business.total_leads_received + movelead_count,
        "active_nav": "leads",
    })


def _business_lead_url(lead):
    """lead_url_resolver for business_lead_entries — where a business's own
    myaccount/foresporsel_database "recent leads" rows link to, so they can
    see the customer's contact details/description/photos rather than just
    a reference number and status badge (previously nowhere on the account
    side actually showed that information at all)."""
    return reverse("business_lead_detail", args=[lead.pk])


@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
def business_lead_detail(request, pk):
    """Full detail of one lead assigned to the logged-in business — the
    account-side counterpart of apps.dashboard.views.lead_detail, but
    read-only and scoped strictly to leads actually assigned to this
    business (never staff-only fields like internal_notes/follow_up_at/
    other businesses' assignments)."""
    from apps.leads.models import MoveLead

    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return redirect("myaccount")

    lead = get_object_or_404(
        MoveLead.objects.filter(Q(business_1=business) | Q(business_2=business) | Q(business_3=business)),
        pk=pk, archived=False,
    )
    return render(request, "core/accountPages/lead_detail.html", {
        "business": business, "lead": lead, "active_nav": "leads",
    })
