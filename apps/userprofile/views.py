import requests


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
        user = request.user

        
        # Try to get the existing profile or create a new one
        profile, created = Profile.objects.get_or_create(user=user)


        u_form =  UserUpdateForm(request.POST, instance=user)
        p_form =  ProfileUpdateForm(request.POST, instance=profile)


        if p_form.is_valid() and u_form.is_valid(): 


            telefon = p_form.cleaned_data['telefon']
            

            username = u_form.cleaned_data['username']
            first_name = u_form.cleaned_data['first_name']
            last_name = u_form.cleaned_data['last_name']
            
            p_form.save()
            u_form.save()

        else:
            u_form = UserUpdateForm() 
            p_form = ProfileUpdateForm() 

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

    if user.is_superuser:
        cars_with_bids = Car.objects.annotate(
            highest_bid=Max('bud__bid_amount'),
            highest_bid_instance=Subquery(
                Bud.objects.filter(car=OuterRef('pk')).order_by('-bid_amount', '-expiry_date')[:1].values('status')
            ),
            highest_bid_expiry=Subquery(
                Bud.objects.filter(car=OuterRef('pk')).order_by('-bid_amount', '-expiry_date').values('expiry_date')[:1]
            ),
        )
    else:
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


            bruksmerker_bilde1 = request.POST.get('bruksmerker_bilde1', '')
            bruksmerker_bilde2 = request.POST.get('bruksmerker_bilde2', '')
            bruksmerker_bilde3 = request.POST.get('bruksmerker_bilde3', '')
            bruksmerker_bilde4 = request.POST.get('bruksmerker_bilde4', '')
            bruksmerker_bilde5 = request.POST.get('bruksmerker_bilde5', '')
            bruksmerker_bilde6 = request.POST.get('bruksmerker_bilde6', '')
            bruksmerker_bilde7 = request.POST.get('bruksmerker_bilde7', '')
            bruksmerker_bilde8 = request.POST.get('bruksmerker_bilde8', '')
            bruksmerker_bilde9 = request.POST.get('bruksmerker_bilde9', '')
            bruksmerker_bilde10 = request.POST.get('bruksmerker_bilde10', '')
            bruksmerker_bilde11 = request.POST.get('bruksmerker_bilde11', '')
            bruksmerker_bilde12 = request.POST.get('bruksmerker_bilde12', '')
            bruksmerker_bilde13 = request.POST.get('bruksmerker_bilde13', '')
            bruksmerker_bilde14 = request.POST.get('bruksmerker_bilde14', '')
            bruksmerker_bilde15 = request.POST.get('bruksmerker_bilde15', '')
            bruksmerker_bilde16 = request.POST.get('bruksmerker_bilde16', '')
            bruksmerker_bilde17 = request.POST.get('bruksmerker_bilde17', '')
            bruksmerker_bilde18 = request.POST.get('bruksmerker_bilde18', '')
            bruksmerker_bilde19 = request.POST.get('bruksmerker_bilde19', '')
            bruksmerker_bilde20 = request.POST.get('bruksmerker_bilde20', '')


            bruksmerker_text = request.POST.get('bruksmerker_text', '')

            # Check if egnerklæring is an instance of Egenerkeling
            if egnerklæring and isinstance(egnerklæring, Egenerkeling):
                egnerklæring.stepTwo = stepTwo
                egnerklæring.reg_nr = reg_nr
                egnerklæring.km = km
                egnerklæring.owners = owners
                egnerklæring.bruktimportert = bruktimportert
                egnerklæring.demobil = demobil

                egnerklæring.bruksmerker_bilde1 = bruksmerker_bilde1
                egnerklæring.bruksmerker_bilde2 = bruksmerker_bilde2
                egnerklæring.bruksmerker_bilde3 = bruksmerker_bilde3
                egnerklæring.bruksmerker_bilde4 = bruksmerker_bilde4
                egnerklæring.bruksmerker_bilde5 = bruksmerker_bilde5
                egnerklæring.bruksmerker_bilde6 = bruksmerker_bilde6
                egnerklæring.bruksmerker_bilde7 = bruksmerker_bilde7
                egnerklæring.bruksmerker_bilde8 = bruksmerker_bilde8
                egnerklæring.bruksmerker_bilde9 = bruksmerker_bilde9
                egnerklæring.bruksmerker_bilde10 = bruksmerker_bilde10
                egnerklæring.bruksmerker_bilde11 = bruksmerker_bilde11
                egnerklæring.bruksmerker_bilde12 = bruksmerker_bilde12
                egnerklæring.bruksmerker_bilde13 = bruksmerker_bilde13
                egnerklæring.bruksmerker_bilde14 = bruksmerker_bilde14
                egnerklæring.bruksmerker_bilde15 = bruksmerker_bilde15
                egnerklæring.bruksmerker_bilde16 = bruksmerker_bilde16
                egnerklæring.bruksmerker_bilde17 = bruksmerker_bilde17
                egnerklæring.bruksmerker_bilde18 = bruksmerker_bilde18
                egnerklæring.bruksmerker_bilde19 = bruksmerker_bilde19
                egnerklæring.bruksmerker_bilde20 = bruksmerker_bilde20


                egnerklæring.bruksmerker_text = bruksmerker_text
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

                    bruksmerker_bilde1=bruksmerker_bilde1,
                    bruksmerker_bilde2=bruksmerker_bilde2,
                    bruksmerker_bilde3=bruksmerker_bilde3,
                    bruksmerker_bilde4=bruksmerker_bilde4,
                    bruksmerker_bilde5=bruksmerker_bilde5,
                    bruksmerker_bilde6 = bruksmerker_bilde6,
                    bruksmerker_bilde7 = bruksmerker_bilde7,
                    bruksmerker_bilde8 = bruksmerker_bilde8,
                    bruksmerker_bilde9 = bruksmerker_bilde9,
                    bruksmerker_bilde10 = bruksmerker_bilde10,
                    bruksmerker_bilde11 = bruksmerker_bilde11,
                    bruksmerker_bilde12 = bruksmerker_bilde12,
                    bruksmerker_bilde13 = bruksmerker_bilde13,
                    bruksmerker_bilde14 = bruksmerker_bilde14,
                    bruksmerker_bilde15 = bruksmerker_bilde15,
                    bruksmerker_bilde16 = bruksmerker_bilde16,
                    bruksmerker_bilde17 = bruksmerker_bilde17,
                    bruksmerker_bilde18 = bruksmerker_bilde18,
                    bruksmerker_bilde19 = bruksmerker_bilde19,
                    bruksmerker_bilde20 = bruksmerker_bilde20,


                    bruksmerker_text=bruksmerker_text,
                )



        elif 'tools' in request.POST:
            car_id = request.POST.get('car_id')
            car = get_object_or_404(Car, id=car_id, user=request.user)

            stepThree = request.POST.get('stepThree', False) == 'on'
            file_tools = request.POST.get('file_tools', '')
            manual_tools = request.POST.get('manual_tools', '')

            egnerklæring = Egenerkeling.objects.filter(car=car, user=request.user).first()

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
            car_id = request.POST.get('car_id')
            car = get_object_or_404(Car, id=car_id, user=request.user)

            stepFour = request.POST.get('stepFour', False) == 'on'
            verksted_history = request.POST.get('verksted_history', '')
            service_history = request.POST.get('service_history', '')
            next_service = request.POST.get('next_service', '')

            egnerklæring = Egenerkeling.objects.filter(car=car, user=request.user).first()

            if egnerklæring:
                egnerklæring.stepFour = stepFour
                egnerklæring.verksted_history = verksted_history
                egnerklæring.service_history = service_history
                egnerklæring.next_service = next_service
                egnerklæring.save()
            else:
                egnerklæring = Egenerkeling.objects.create(
                car=car,
                user=request.user,
                stepFour=stepFour,
                verksted_history=verksted_history,
                service_history=service_history,
                next_service=next_service,
                )



        elif 'garanti' in request.POST:
            car_id = request.POST.get('car_id')
            car = get_object_or_404(Car, id=car_id, user=request.user)

            stepFive = request.POST.get('stepFive', False) == 'on'
            left_garantier = request.POST.get('left_garantier', '')
            new_car_garanti = request.POST.get('new_car_garanti', '')
            batery = request.POST.get('batery', '')
            karrosseri = request.POST.get('karrosseri', '')
            drivverk = request.POST.get('drivverk', '')

            # Check if egnerklæring is an instance of Egenerkeling
            if egnerklæring and isinstance(egnerklæring, Egenerkeling):
                egnerklæring.stepFive = stepFive
                egnerklæring.left_garantier = left_garantier
                egnerklæring.new_car_garanti = new_car_garanti
                egnerklæring.batery = batery
                egnerklæring.karrosseri = karrosseri
                egnerklæring.drivverk = drivverk
                egnerklæring.save()
            else:
                egnerklæring = Egenerkeling.objects.create(
                    car=car,
                    user=request.user,
                    stepFive=stepFive,
                    left_garantier=left_garantier,
                    new_car_garanti=new_car_garanti,
                    batery=batery,
                    karrosseri=karrosseri,
                    drivverk=drivverk,
                )


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
    antall_visninger = visninger.count()

    context = {
        'visninger': visninger,
        'antall_visninger': antall_visninger,
    }
    return render(request, 'core/account/timer.html', context)





@login_required
def mine_kjøp(request):
    user = request.user
    buy = Buy.objects.filter(user=user).order_by('-id')



    if request.method == 'POST' and 'stepfour' in request.POST:
        carowner = request.POST.get('carowner', '')
        fullname = request.POST.get('fullname', '')
        email = request.POST.get('email', '')
        telefonnummer = request.POST.get('telefonnummer', '')
        personalnumber = request.POST.get('personalnumber', '')

        data = {
            'carowner': carowner,
            'fullname': fullname,
            'email': email,
            'telefonnummer': telefonnummer,
            'personalnumber': personalnumber,
        }   

        # Replace 'YOUR_ZAPIER_WEBHOOK_URL' with your actual Zapier webhook URL
        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/13544280/3fjmye2/'

        # Make a POST request to Zapier webhook
        response = requests.post(zapier_webhook_url, json=data)

        for purchase in buy:
            if request.user == purchase.user:
                purchase.step_three()


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



@login_required
def password_change(request):
    user = request.user
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('/logg-inn/')
        
            
    form = SetPasswordForm(user)
    return render(request, 'core/password_reset_confirm.html', {'form': form})


def pass_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = User.objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Forespørsel om tilbakestilling av passord"
                message = render_to_string("core/template_reset_password.html", {
                    'domain': get_current_site(request).domain,
                    'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)),
                    'token': account_activation_token.make_token(associated_user),
                    "protocol": 'https' if request.is_secure() else 'http'
                })

                data = {
                        'user_email': user_email,
                        'subject': subject,
                        'message': message,
                    }   


                # Replace 'YOUR_ZAPIER_WEBHOOK_URL' with your actual Zapier webhook URL
                zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/13544280/3z7w5kd/'

                # Make a POST request to Zapier webhook
                response = requests.post(zapier_webhook_url, json=data)
            
            return redirect('/')

    form = PasswordResetForm()
    return render(
        request=request,
        template_name='core/passord-reset.html',
        context={'form':form}
    )

