from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import SignUpForm, UserprofileForm
from apps.store.models import Bedrift_info
from apps.userprofile.models import Profile
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, get_object_or_404
from apps.store.models import Bedrift_info

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.store.models import *
from .forms import *
from django.urls import reverse
from apps.store.models import JobDistribution

from django.db.models import Q


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

            # Link Bedrift_info (business data) if the same email exists
            if email_param:
                try:
                    business = Bedrift_info.objects.filter(email=email_param).last()
                    if business:
                        business.user = user  # assuming you add user FK in Bedrift_info
                        business.save()
                except Bedrift_info.DoesNotExist:
                    pass

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




@require_GET
def check_user_exists(request):
    username = request.GET.get("username", "").strip().lower()
    if not username:
        return JsonResponse({"exists": False, "error": "Mangler brukernavn"}, status=400)

    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({"exists": exists})




@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
def myaccount(request):
    business = getattr(request.user, "bedrift_info", None)
    cities_list = []
    move_type_list = []
    jobs = []

    if business:
        # Split cities
        if business.cities:
            cities_list = [city.strip() for city in business.cities.split(",") if city.strip()]

        # Split move types
        if business.move_type:
            move_type_list = [t.strip() for t in business.move_type.split(",") if t.strip()]

        # ✅ Get all jobs where this business is one of the 3 assigned
        from apps.store.models import JobDistribution

        jobs = JobDistribution.objects.filter(
            Q(business_1=business) | Q(business_2=business) | Q(business_3=business)
        ).select_related("inquiry").order_by("-created_at")

    context = {
        "business": business,
        "cities_list": cities_list,
        "move_type_list": move_type_list,
        "jobs": jobs,
    }
    return render(request, "core/myaccount.html", context)



@login_required
def edit_public_profile(request):
    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return redirect("myaccount")

    public_info, _ = PublicBusinessInformation.objects.get_or_create(business=business)

    if request.method == "POST":
        form = PublicBusinessInformationForm(request.POST, request.FILES, instance=public_info)
        image_form = BusinessImageForm(request.POST, request.FILES)

        # detect which field triggered the POST
        if "logo" in request.FILES:
            public_info.logo = request.FILES["logo"]
            public_info.save(update_fields=["logo"])

        elif "about_us" in request.POST:
            if form.is_valid():
                public_info.about_us = form.cleaned_data["about_us"]
                public_info.save(update_fields=["about_us"])

        elif "faq" in request.POST:
            if form.is_valid():
                public_info.faq = form.cleaned_data["faq"]
                public_info.save(update_fields=["faq"])

        elif "image" in request.FILES:
            # Safe image upload (check max 6)
            if public_info.images.count() < 6:
                img = BusinessImage(public_info=public_info, image=request.FILES["image"])
                img.save()

        return redirect("edit_public_profile")

    # normal GET
    form = PublicBusinessInformationForm(instance=public_info)
    image_form = BusinessImageForm()

    public_path = reverse('public_business_profile', args=[business.id])
    public_url = request.build_absolute_uri(public_path)

    return render(request, "core/accountPages/business_edit_profile.html", {
        "form": form,
        "image_form": image_form,
        "public_info": public_info,
        "business": business,
         "public_url": public_url,
    })




@login_required(login_url="/for-bedrifter/bruker/logg-inn/")
def foresporsel_database(request):
    business = getattr(request.user, "bedrift_info", None)
    if not business:
        return redirect("/for-bedrifter/bruker/logg-inn/")

    # ✅ Handle form submission (AJAX or normal POST)
    if request.method == "POST":
        leads_per_day = request.POST.get("leads_per_day")
        leads_per_week = request.POST.get("leads_per_week")
        leads_per_month = request.POST.get("leads_per_month")

        # Update only if fields are provided
        if leads_per_day is not None:
            business.leads_per_day = leads_per_day or None
        if leads_per_week is not None:
            business.leads_per_week = leads_per_week or None
        if leads_per_month is not None:
            business.leads_per_month = leads_per_month or None

        business.save(update_fields=["leads_per_day", "leads_per_week", "leads_per_month"])
        return JsonResponse({"success": True})

    # ✅ Show leads
    leads = JobDistribution.objects.filter(
        Q(business_1=business) | Q(business_2=business) | Q(business_3=business)
    ).select_related("inquiry").order_by("-created_at")

    return render(request, "core/accountPages/foresporsel_database.html", {
        "business": business,
        "leads": leads,
    })