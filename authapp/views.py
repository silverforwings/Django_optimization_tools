from django import forms
from django.contrib import auth
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from authapp.forms import ShopUserAuthenticationForm, ShopUserRegisterForm, ShopUserUpdateForm, \
    ShopUserPasswordEditForm, ShopUserProfileUpdateForm
from authapp.models import ShopUser, ShopUserProfile


def login(request):
    # предыдущая страница, с которой совершён переход
    # реализовано в шаблоне для выяснения открылся ли логин со страницы регистрации
    # print(request.META)
    # print('register' in request.META.get('HTTP_REFERER'))

    # для возврата на страницу покупки, после логина при покупке товара
    # redirect_url = request.GET['next'] if 'next' in request.GET.keys() else ''
    # или так:
    # redirect_url = request.GET.get('next', None)

    # print(request.method)  # смотрим метод запроса
    if request.method == 'POST':
        # print('data:', request.POST)  # смотрим что приходит в POST
        form = ShopUserAuthenticationForm(data=request.POST)
        print(form)
        print(form.is_valid())
        if form.is_valid():  # errors dict
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)
            if user and user.is_active:
                auth.login(request, user)
                # return HttpResponseRedirect('/')  # хардкод, лучше так не делать
                # if 'redirect_url' in request.POST.keys():
                if request.POST.get('redirect_url', None):
                    return HttpResponseRedirect(request.POST['redirect_url'])
                return HttpResponseRedirect(reverse('main:index'))
    else:
        # form = ShopUserAuthenticationForm()
        # print(request.GET)
        form = ShopUserAuthenticationForm(data=request.GET or None)
    context = {
        'page_title': 'аутентификация',
        'form': form,
        # 'redirect_url': redirect_url,
    }
    return render(request, 'authapp/login.html', context)


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('main:index'))


def user_register(request):
    if request.method == 'POST':
        register_form = ShopUserRegisterForm(request.POST, request.FILES)
        if register_form.is_valid():
            user = register_form.save()
            user.send_verify_mail()

            # сразу авторизуем нового пользователя и отправляем на главную страницу
            # username = request.POST['username']
            # password = request.POST['password1']
            # new_user = auth.authenticate(username=username, password=password)
            # if new_user and new_user.is_active:
            #     auth.login(request, new_user)
            #     return HttpResponseRedirect(reverse('main:index'))
            # return HttpResponseRedirect(reverse('auth:login'))
            return render(request, 'authapp/user_register_send.html')
    else:
        register_form = ShopUserRegisterForm()
    context = {
        'page_title': 'регистрация',
        'register_form': register_form
    }

    return render(request, 'authapp/user_register.html', context)


# Так как теперь изменения сохраняются в двух моделях,
# для обеспечения целостности данных применяем к контроллеру декоратор @transaction.atomic
@transaction.atomic
def user_profile(request):
    if request.method == 'POST':
        # instance подтягивает данные, вместо создания нового объекта
        # request.user - текущий залогиненый пользователь
        profile_form = ShopUserUpdateForm(request.POST, request.FILES, instance=request.user)
        user_profile = ShopUserProfileUpdateForm(request.POST, request.FILES,
            instance=request.user.shopuserprofile
        )
        if profile_form.is_valid() and user_profile.is_valid():
            profile_form.save()
            #  user_profile сохранится автоматически, так как используется @receiver в методе ниже
            # user_profile.save()  # вариант сохранения без @receiver(post_save, sender=ShopUser)
            return HttpResponseRedirect(reverse('main:index'))
    else:
        profile_form = ShopUserUpdateForm(instance=request.user)
        user_profile = ShopUserProfileUpdateForm(
            instance=request.user.shopuserprofile
        )
    context = {
        'page_title': 'профиль',
        'form': profile_form,
        'user_profile_form': user_profile,
    }

    return render(request, 'authapp/user_profile.html', context)


def change_password(request):
    if request.method == 'POST':
        password_form = ShopUserPasswordEditForm(user=request.user, data=request.POST)
        # print(check_password(request.POST['old_password'], request.user.password),
        #       password_form.is_valid())
        if password_form.is_valid():
            username = request.user.username
            password_form.save()

            # сразу пользователя и отправляем на страницу профиля
            password = request.POST['new_password1']
            user = auth.authenticate(username=username, password=password)
            if user and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('auth:user_profile'))
    else:
        password_form = ShopUserPasswordEditForm(user=request.user, data=request.POST)
    context = {
        'page_title': 'Редактирование пароля',
        'password_form': password_form
    }

    return render(request, 'authapp/change_password.html', context)


def user_verify(request, email, activation_key):
    try:
        user = ShopUser.objects.get(email=email)
        if user.activation_key == activation_key and not user.is_activation_key_expired() and not user.is_active:
            user.is_active = True
            user.save()
            auth.login(request, user,
                       backend='django.contrib.auth.backends.ModelBackend')
        else:
            print(f'error activation user: {user}')
            return render(request, 'authapp/verification-err.html')
        return render(request, 'authapp/verification.html')
    except Exception as e:
        print(f'error activation user : {e.args}')
        return HttpResponseRedirect(reverse('main:index'))


@receiver(post_save, sender=ShopUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # print('ShopUser created')
        ShopUserProfile.objects.create(user=instance)
    else:
        # print('ShopUser modified')
        instance.shopuserprofile.save()
