from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .forms import RegisterForm, LoginForm, ProfileForm
from .models import Profile

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'ثبت‌نام با موفقیت انجام شد. خوش آمدید!')
        return redirect('dashboard:home')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is not None:
            login(request, user)
            messages.success(request, 'با موفقیت وارد شدید.')
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'dashboard:home')
        messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'با موفقیت خارج شدید.')
    return redirect('accounts:login')


def profile_view(request, username=None):
    """FIX from PROJECT_PATTERNS.md checklist: optional username param so
    profiles of *other* users are viewable, not just request.user's own."""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        user = request.user

    profile, _ = Profile.objects.get_or_create(user=user)
    is_owner = request.user.is_authenticated and request.user == user

    if is_owner and request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل به‌روزرسانی شد.')
            return redirect('accounts:profile', username=user.username)
    else:
        form = ProfileForm(instance=profile) if is_owner else None

    context = {
        'profile_user': user,
        'profile': profile,
        'form': form,
        'is_owner': is_owner,
    }
    return render(request, 'accounts/profile.html', context)


def password_reset_request_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email=email).first()
        # FIX from PROJECT_PATTERNS.md checklist: guard against missing email
        if user and user.email:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_url = request.build_absolute_uri(f'/accounts/reset/{uid}/{token}/')
            send_mail(
                subject='بازیابی رمز عبور - Code Snippet Manager',
                message=f'برای بازیابی رمز عبور روی لینک زیر کلیک کنید:\n{reset_url}',
                from_email=None,
                recipient_list=[user.email],
                fail_silently=True,
            )
        messages.success(request, 'اگر ایمیل در سیستم موجود باشد، لینک بازیابی ارسال شد.')
        return redirect('accounts:login')
    return render(request, 'accounts/password_reset_request.html')


def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not token_generator.check_token(user, token):
        messages.error(request, 'لینک بازیابی نامعتبر یا منقضی شده است.')
        return redirect('accounts:login')

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 and password1 == password2:
            user.set_password(password1)
            user.save()
            messages.success(request, 'رمز عبور با موفقیت تغییر کرد. اکنون وارد شوید.')
            return redirect('accounts:login')
        messages.error(request, 'رمزهای عبور مطابقت ندارند.')

    return render(request, 'accounts/password_reset_confirm.html')
