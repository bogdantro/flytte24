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
    highest_bid = request.user.bud.filter().order_by('bid_amount').last() 

    context={
        'highest_bid':highest_bid,
    }
    return render(request, 'core/account/user-cars.html', context)

@login_required
def kommende_visninger(request):
    
    return render(request, 'core/account/timer.html')


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