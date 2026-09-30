from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm, OpenAIKeyForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo(a), {user.get_short_name()}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'E-mail ou senha inválidos.')

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Conta criada com sucesso! Bem-vindo(a), {user.get_short_name()}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Corrija os erros abaixo.')

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Você saiu da sua conta.')
    return redirect('login')


@login_required
def profile_view(request):
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    password_form = ChangePasswordForm(request.POST or None)
    openai_form = OpenAIKeyForm(request.POST or None)
    active_tab = request.GET.get('tab', 'profile')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'password':
            active_tab = 'password'

        if action == 'openai_key':
            active_tab = 'openai'
            if openai_form.is_valid():
                request.user.openai_api_key = openai_form.cleaned_data['openai_api_key']
                request.user.save(update_fields=['openai_api_key_encrypted'])
                messages.success(request, 'Chave da OpenAI salva! Os recursos de IA já estão liberados.')
                return redirect(reverse('profile') + '?tab=openai')
            messages.error(request, 'Corrija os erros abaixo.')

        elif action == 'openai_key_remove':
            request.user.openai_api_key = ''
            request.user.save(update_fields=['openai_api_key_encrypted'])
            messages.info(request, 'Chave da OpenAI removida.')
            return redirect(reverse('profile') + '?tab=openai')

        elif action == 'profile' and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('profile')

        elif action == 'password' and password_form.is_valid():
            user = request.user
            current = password_form.cleaned_data['current_password']
            if user.check_password(current):
                user.set_password(password_form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('profile')
            else:
                messages.error(request, 'Senha atual incorreta.')
        else:
            messages.error(request, 'Corrija os erros abaixo.')

    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'openai_form': openai_form,
        'active_tab': active_tab,
    })
