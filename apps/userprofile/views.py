from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, UserprofileForm
from django.contrib.auth import login
from textwrap import dedent
from django.core.mail import send_mail, BadHeaderError
from .forms import *
from apps.core.models import *


@login_required
def myaccount(request):

    if request.method == 'POST':
        p_form =  ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if p_form.is_valid():
            image = p_form.cleaned_data['image']
            
            p_form.save()

        else:
            p_form = ProfileUpdateForm() 


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



    return render(request, 'core/myaccount.html')



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
