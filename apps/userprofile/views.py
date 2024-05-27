import requests


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, UserprofileForm
from django.contrib.auth import login
from textwrap import dedent
from django.core.mail import send_mail, BadHeaderError

from .models import *
from .forms import *
from apps.core.models import *
from apps.store.models import *
from datetime import datetime, timedelta
from django.contrib import messages


@login_required
def myaccount(request):

    return render(request, 'core/myaccount.html')



@login_required
def user_info(request):
    user = request.user
    message1 = ''  # Legg til en standardverdi for 'message' øverst i funksjonen
    message2 = ''  # Legg til en standardverdi for 'message' øverst i funksjonen


    if request.method == 'POST':
        p_form =  ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if p_form.is_valid():
            old_profile_image = request.user.profile.profile_image
            p_form.save()
            new_profile_image = p_form.cleaned_data['profile_image']

            # Check if the profile image has been changed
            if old_profile_image != new_profile_image:
                message1 = 'Profil bilde har blitt endret.'
                return render(request, 'core/account/user-info.html', {'message1':message1})

        else:
            p_form = ProfileUpdateForm() 

    if request.method == 'POST':
        u_form =  UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            username = u_form.cleaned_data['username']
            first_name = u_form.cleaned_data['first_name']
            last_name = u_form.cleaned_data['last_name']
            u_form.save()
        else:
            u_form = UserUpdateForm()    


    if request.method == 'POST' and 'new_password1' in request.POST and 'new_password2' in request.POST:
        form = SetPasswordForm(user, request.POST)        
        if form.is_valid():
            form.save()
            return redirect('/logg-inn/')
        else:    
            message2 = 'Passordene var ikke like eller for svake. Prøv igjen.'
            return render(request, 'core/account/user-info.html', {'message2':message2})
      
        


    return render(request, 'core/account/user-info.html')


@login_required
def my_reviews(request):
    # Get reviews related to the currently logged-in user
    user_reviews = ProductReview.objects.filter(user=request.user)

    return render(request, 'core/account/vurderinger.html', {'user_reviews': user_reviews})


@login_required
def user_help(request):
    sucess = ''
    if request.method == 'POST':
        name = request.POST.get('name', )
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')

        sucess = 'Vi har motatt din hendvelse'

        contact = Contact.objects.create(name=name, message=message, email=email)


        data = {
            'name': name,
            'email': email,
            'message': message,
        }   


        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/16531899/30hfmle/'

        response = requests.post(zapier_webhook_url, json=data)


    context = {
        'sucess':sucess,
    }    
    return render(request, 'core/account/hjelp.html', context)

@login_required
def varslinger(request):
    return render(request, 'core/account/varslinger.html')

@login_required
def payment_info(request):
    
    return render(request, 'core/account/payment-info.html')

@login_required
def business_res(request):
    return render(request, 'core/account/business-res.html')

@login_required
def my_business(request):
    business = Product.objects.filter(user=request.user)
    categories = Category.objects.all()


    if request.method == 'POST':
        # Extract data from the request
        name = request.POST.get('name')
        category_ids = request.POST.getlist('category')  # Get a list of selected category IDs
        description = request.POST.get('description')
        seo = request.POST.get('seo')
        address = request.POST.get('address')
        mandag = request.POST.get('mandag')
        tirsdag = request.POST.get('tirsdag')
        ondsdag = request.POST.get('ondsdag')
        torsdag = request.POST.get('torsdag')
        fredag = request.POST.get('fredag')
        lørdag = request.POST.get('lørdag')
        søndag = request.POST.get('søndag')
        contact_by_website = request.POST.get('contact_by_website')
        contact_by_phone = request.POST.get('contact_by_phone')
        contact_by_email = request.POST.get('contact_by_email')
        contact_by_instagram = request.POST.get('contact_by_instagram')
        contact_by_facebook = request.POST.get('contact_by_facebook')


       

        # Create the Product object
        product = Product.objects.create(
            user=request.user,
            name=name,
            description=description,
            seo=seo,
            address=address,
            mandag=mandag,
            tirsdag=tirsdag,
            ondsdag=ondsdag,
            torsdag=torsdag,
            fredag=fredag,
            lørdag=lørdag,
            søndag=søndag,
            contact_by_website=contact_by_website,
            contact_by_phone=contact_by_phone,
            contact_by_email=contact_by_email,
            contact_by_instagram=contact_by_instagram,
            contact_by_facebook=contact_by_facebook,
            # Add other fields as needed
        )

        # Add the selected categories to the product
        product.category.set(category_ids)

        # Handle images separately, assuming you're using a form with enctype="multipart/form-data"
        image1 = request.FILES.get('image1')
        if image1:
            product.image1 = image1
        image2 = request.FILES.get('image2')
        if image2:
            product.image2 = image2

        image3 = request.FILES.get('image3')
        if image3:
            product.image3 = image3

        image4 = request.FILES.get('image4')
        if image4:
            product.image4 = image4

        image5 = request.FILES.get('image5')
        if image5:
            product.image5 = image5

        image6 = request.FILES.get('image6')
        if image6:
            product.image6 = image6
            
        # Save the Product object
            
        data = {
            'name': name,
        }   


        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/16531899/30hfwqr/'

        response = requests.post(zapier_webhook_url, json=data)

        product.save()

    context = {
        'business':business,
        'categories':categories,
    }    
    return render(request, 'core/account/my-business.html', context)


from datetime import datetime, timedelta
from django.contrib import messages

@login_required
def change_sub(request):
    profile = Profile.objects.get(user=request.user)
    message = ''
    not_allowed = False
    


    # Check the last subscription change date
    last_change_date = profile.last_subscription_change_date

    if last_change_date:
        today = datetime.now().date()
        # Check if the last change was more than a month ago
        if today.year == last_change_date.year and today.month == last_change_date.month:
           not_allowed = True

    if request.method == 'POST':
        form = ChangeSubscriptionForm(request.POST)
        if form.is_valid():
            new_subscription = form.cleaned_data['new_subscription']
            profile.medlemskap = new_subscription
            profile.last_subscription_change_date = datetime.now().date()
            profile.save()

            message = 'Medlemskap har blitt endret'
            messages.success(request, message)

            data = {
                'profile': profile.to_dict(),
                'new_subscription': new_subscription,
            }   

            zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/16531899/30hfjft/'

            response = requests.post(zapier_webhook_url, json=data)

            profile.save()

            message = 'Medlemskapet har blitt endret'

    else:
        form = ChangeSubscriptionForm(initial={'new_subscription': profile.medlemskap})

    return render(request, 'core/account/change-sub.html', {'form': form, 'message': message, 'not_allowed':not_allowed})




from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import SignUpForm, UserprofileForm
from .models import Profile

def signup(request, backend='django.contrib.auth.backends.ModelBackend'):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        userprofileform = UserprofileForm(request.POST)

        if form.is_valid() and userprofileform.is_valid():
            user = form.save()

            # Specify the authentication backend before calling login
            user.backend = backend

            login(request, user)

            userprofile = userprofileform.save(commit=False)
            userprofile.user = user
            userprofile.save()

            medlemskap = 'Bruker'

            profile = Profile.objects.create(user=user, medlemskap=medlemskap)

            return redirect('myaccount')

    else:
        form = SignUpForm()
        userprofileform = UserprofileForm()

    return render(request, 'core/signup.html', {'form': form, 'userprofileform': userprofileform})

