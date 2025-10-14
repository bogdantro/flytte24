from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import SignUpForm, UserprofileForm
from apps.store.models import Bedrift_info
from apps.userprofile.models import Profile
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET



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



from apps.store.models import JobDistribution

def myaccount(request):
    business = getattr(request.user, "bedrift_info", None)
    cities_list = []
    move_type_list = []
    jobs = []

    if business:
        # Split byer
        if business.cities:
            cities_list = [city.strip() for city in business.cities.split(",") if city.strip()]

        # Split flyttetyper
        if business.move_type:
            move_type_list = [t.strip() for t in business.move_type.split(",") if t.strip()]

        # Hent jobber til dashboard
        jobs = business.received_jobs.select_related("inquiry").order_by("-created_at")

    context = {
        "business": business,
        "cities_list": cities_list,
        "move_type_list": move_type_list,
        "jobs": jobs,
    }
    return render(request, "core/myaccount.html", context)
