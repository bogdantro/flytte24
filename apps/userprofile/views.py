from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, UserprofileForm
from django.contrib.auth import login
from textwrap import dedent
from django.core.mail import send_mail, BadHeaderError
from .forms import *
from apps.core.models import *
from django.db.models.query_utils import Q
from django.core.mail import EmailMessage
from django.template.loader import *
from django.contrib.sites.shortcuts import *
from django.utils.encoding import *
from django.utils.http import *
from .tokens import *
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.db.models import Subquery, OuterRef
from apps.core.models import *



@login_required
def myaccount(request):
   
    return render(request, 'core/account/myaccount.html')

@login_required
def edit_user_info(request):
    if request.method == 'POST':
        u_form =  UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            username = u_form.cleaned_data['username']
            email = u_form.cleaned_data['email']
            first_name = u_form.cleaned_data['first_name']
            last_name = u_form.cleaned_data['last_name']
            
            u_form.save()

        else:
            u_form = UserUpdateForm() 
    return render(request, 'core/account/edit.html')

@login_required
def mine_bud(request):
    bud = Bud.objects.filter(user=request.user)

    context={
        'bud':bud,
    }
    return render(request, 'core/account/my-bid.html', context)


@login_required
def mine_annonser(request):
    user = request.user
    cars_with_bids = Car.objects.filter(user=user).annotate(
        highest_bid=Max('bud__bid_amount'),
        highest_bid_instance=Subquery(
            Bud.objects.filter(car=OuterRef('pk')).order_by('-bid_amount', '-expiry_date')[:1].values('status')
        ),
        highest_bid_expiry=Subquery(
            Bud.objects.filter(car=OuterRef('pk')).order_by('-bid_amount', '-expiry_date').values('expiry_date')[:1]
        ),
    )

    for car in cars_with_bids:
        if car.highest_bid_expiry:
            remaining_days = (car.highest_bid_expiry - timezone.now().date()).days
            car.remaining_days = max(remaining_days, 0)  # Ensure days left is not negative

    context = {
        'cars_with_bids': cars_with_bids,
    }
    return render(request, 'core/account/user-cars.html', context)



def mine_annonser_egenerklering(request, car_id):
    car = get_object_or_404(Car, id=car_id, user=request.user)
    egnerklæring = Egenerkeling.objects.filter(car=car, user=request.user).first()  # Assuming there's only one egnerklæring per user

    if request.method == 'POST':
        if 'contactInfo' in request.POST:
            car_id = request.POST.get('car_id')
            car = get_object_or_404(Car, id=car_id, user=request.user)

            stepOne = request.POST.get('stepOne', False) == 'on'
            name = request.POST.get('name', '')
            mobile_nr = request.POST.get('mobile_nr', '')
            adress = request.POST.get('adress', '')
            personal_number = request.POST.get('personal_number', '')
            account_number = request.POST.get('account_number', '')

            egnerklæring = Egenerkeling.objects.filter(car=car, user=request.user).first()

            if egnerklæring:
                egnerklæring.stepOne = stepOne
                egnerklæring.name = name
                egnerklæring.mobile_nr = mobile_nr
                egnerklæring.adress = adress
                egnerklæring.personal_number = personal_number
                egnerklæring.account_number = account_number
                egnerklæring.save()
            else:
                egnerklæring = Egenerkeling.objects.create(
                    car=car,
                    user=request.user,
                    stepOne=stepOne,
                    name=name,
                    mobile_nr=mobile_nr,
                    adress=adress,
                    personal_number=personal_number,
                    account_number=account_number,
                )



        elif 'carDetails' in request.POST:
                car_id = request.POST.get('car_id')
                car = get_object_or_404(Car, id=car_id, user=request.user)

                stepTwo = request.POST.get('stepTwo', False) == 'on'
                reg_nr = request.POST.get('reg_nr', '')
                km = request.POST.get('km', '')
                owners = request.POST.get('owners', '')
                bruktimportert = request.POST.get('bruktimportert', '')
                demobil = request.POST.get('demobil', '')

                egnerklæring = Egenerkeling.objects.filter(car=car, user=request.user)

                if egnerklæring:
                    egnerklæring.stepTwo = stepTwo
                    egnerklæring.reg_nr = reg_nr
                    egnerklæring.km = km
                    egnerklæring.owners = owners
                    egnerklæring.bruktimportert = bruktimportert
                    egnerklæring.demobil = demobil
                    egnerklæring.save()
                else:
                    egnerklæring = Egenerkeling.objects.create(
                    car=car,
                    user=request.user,
                    stepTwo=stepTwo,
                    reg_nr=reg_nr,
                    km=km,
                    owners=owners,
                    bruktimportert=bruktimportert,
                    demobil=demobil,
                    )


        elif 'tools' in request.POST:
                stepThree = request.POST.get('stepThree', False) == 'on'  # Convert 'on' to True and everything else to False
                file_tools = request.POST.get('file_tools', '')
                manual_tools = request.POST.get('manual_tools', '')
                
                if egnerklæring:
                    egnerklæring.stepThree = stepThree
                    egnerklæring.file_tools = file_tools
                    egnerklæring.manual_tools = manual_tools
                    egnerklæring.save()
                else:
                    egnerklæring = Egenerkeling.objects.create(
                        car=car,
                        user=request.user,
                        stepThree=stepThree,
                        file_tools=file_tools,
                        manual_tools=manual_tools,
                    )
        elif 'service' in request.POST:
            None
        elif 'garanti' in request.POST:
            None

    context = {
        'car': car,
        'egnerklæring': egnerklæring,
    }
    return render(request, 'core/account/egenerkl.html', context)



@login_required
def accept_highest_bid(request, car_id):
    car = get_object_or_404(Car, id=car_id, user=request.user)
    highest_bid = car.bud_set.order_by('-bid_amount').first()

    if highest_bid:
        highest_bid.accept_bid()  # Assuming you have an accept_bid method in your Bud model
        # Optionally, you can notify the bidder about the accepted bid

        user = highest_bid.user
        car = car

        buy = Buy.objects.create(user=user, car=car)
        return redirect('/min-bruker/mine-annonser/')

    return redirect('/min-bruker/mine-annonser/')

@login_required
def decline_highest_bid(request, car_id):
    car = get_object_or_404(Car, id=car_id, user=request.user)
    highest_bid = car.bud_set.order_by('-bid_amount').first()

    if highest_bid:
        highest_bid.decline_bid()  # Assuming you have a decline_bid method in your Bud model
        # Optionally, you can notify the bidder about the declined bid

    return redirect('/min-bruker/mine-annonser/')





@login_required
def kommende_visninger(request):
    visninger = request.user.visninger.all()

    context = {
        'visninger': visninger,
    }
    return render(request, 'core/account/timer.html', context)





@login_required
def mine_kjøp(request):
    user = request.user
    buy = Buy.objects.filter(user=user)

    context = {
        'buy':buy,
    }
    return render(request, 'core/account/buy.html', context)

@login_required
def step_one(request, buy_id):
    buy = get_object_or_404(Buy, id=buy_id)
    
    if request.user == buy.user:
        buy.step_one()
    return redirect('/min-bruker/mine-kjøp/')

@login_required
def step_one_forsikring(request, buy_id):
    buy = get_object_or_404(Buy, id=buy_id)
    
    if request.user == buy.user:
        buy.step_one()
        buy.step_one_forsikring()
    return redirect('/min-bruker/mine-kjøp/')


@login_required
def step_two(request, buy_id):
    buy = get_object_or_404(Buy, id=buy_id)
    
    if request.user == buy.user:
        buy.step_two()
    return redirect('/min-bruker/mine-kjøp/')

@login_required
def step_two_garanti(request, buy_id):
    buy = get_object_or_404(Buy, id=buy_id)
    
    if request.user == buy.user:
        buy.step_two()
        buy.step_two_garanti()
    return redirect('/min-bruker/mine-kjøp/')






@login_required
def accept_bid(request, bud_id):
    bud = get_object_or_404(Bud, id=bud_id)
    if request.user == bud.car.user:
        bud.accept_bid()
    return redirect('/min-bruker/mine-annonser/', slug=bud.car.slug)

@login_required
def decline_bid(request, bud_id):
    bud = get_object_or_404(Bud, id=bud_id)
    if request.user == bud.car.user:
        bud.decline_bid()
    return redirect('/min-bruker/mine-annonser/', slug=bud.car.slug)


def signup(request, backend='django.contrib.auth.backends.ModelBackend'):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        userprofileform = UserprofileForm(request.POST)

        if form.is_valid() and userprofileform.is_valid():
            user = form.save()

            userprofile = userprofileform.save(commit=False)
            userprofile.user = user
            userprofile.save()

            login(request, user)

            return redirect('/min-bruker/')
    else:
        form = SignUpForm()
        userprofileform = UserprofileForm()

    return render(request, 'core/signup.html', {'form': form, 'userprofileform': userprofileform})    


def pass_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = User.objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Password Reset request"
                message = render_to_string("template_reset_password.html", {
                    'user': associated_user,
                    'domain': get_current_site(request).domain,
                    'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)),
                    'token': account_activation_token.make_token(associated_user),
                    "protocol": 'https' if request.is_secure() else 'http'
                })
                email = EmailMessage(subject, message, to=[associated_user.email])
                if email.send():
                    message.success(request,
                        """
                        <h2>Password reset sent</h2><hr>
                        <p>
                            We've emailed you instructions for setting your password, if an account exists with the email you entered. 
                            You should receive them shortly.<br>If you don't receive an email, please make sure you've entered the address 
                            you registered with, and check your spam folder.
                        </p>
                        """
                    )
                else:
                    message.error(request, "Problem sending reset password email, <b>SERVER PROBLEM</b>")

            
            return redirect('/')

    form = PasswordResetForm()
    return render(
        request=request,
        template_name='core/passord-reset.html',
        context={'form':form}
    )

# def passwordResetConfirm():