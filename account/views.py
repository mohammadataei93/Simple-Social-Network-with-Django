from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from .forms import UserRegistrationForm, UserLoginForm, EditUserForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from home.models import Post
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from .models import Relation, Profile

class UserRegisterView(View):
    form_class = UserRegistrationForm
    template_name = 'account/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home:home')
        return super().dispatch(request,*args,**kwargs)

    def get(self,request):
        form = self.form_class()
        return render(request,self.template_name,{'form':form})

    def post(self,request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            User.objects.create_user(cd['username'],cd['email'],cd['password1'])
            messages.success(request,'You registered successfully','success')
            return redirect('home:home')
        else: return render(request,self.template_name,{'form':form})


class UserLoginView(View):
    form_class = UserLoginForm
    template_name = 'account/login.html'

    def setup(self, request, *args, **kwargs):
        self.next = request.GET.get('next')
        super().setup(request,*args,**kwargs)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home:home')
        return super().dispatch(request,*args,**kwargs)

    def get(self,request):
        form = self.form_class()
        return render(request,self.template_name,{'form':form})

    def post(self,request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request,username=cd['username'],password=cd['password'])
            if user:
                login(request,user)
                messages.success(request,'you logged in successfully','success')
                if self.next:
                    return redirect(self.next)
                return redirect('home:home')
            else:
                messages.error(request,'username or password is wrong!','warning')
                return redirect('home:home')
        else: return render(request,self.template_name,{'form':form})


class UserLogoutView(LoginRequiredMixin,View):
    # login_url = '/account/login/'
    def get(self,request):
        logout(request)
        messages.success(request,'you logged out successfuly','success')
        return redirect('home:home')



class UserProfileView(LoginRequiredMixin, View):
    def get(self, request,user_id):
        is_following = False
        user = get_object_or_404(User,id=user_id)
        posts = user.posts.all()
        relation = Relation.objects.filter(from_user=request.user,to_user=user)
        if relation.exists():
            is_following = True
        return render(request, 'account/profile.html', {'user':user , 'posts':posts, 'is_following':is_following})


class UserPasswordResetView(PasswordResetView):
    template_name = 'account/password_reset_form.html'
    success_url = reverse_lazy('account:password-reset-done')
    email_template_name = 'account/password_reset_email.html'

class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'account/password_reset_done.html'

class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('account:password-reset-complete')

class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'account/password_reset_complete.html'

class UserFollowView(View):
    def get(self,request,user_id):
        user = User.objects.get(pk=user_id)
        relation = Relation.objects.filter(from_user=request.user,to_user=user)
        if relation.exists():
            messages.error(request,'you already following this user','danger')
        else:
            Relation(from_user=request.user,to_user=user).save()
            messages.success(request, 'you followed this user', 'success')
        return redirect('account:user-profile',user.id)

class UserUnfollowView(View):
    def get(self,request,user_id):
        user = User.objects.get(pk=user_id)
        relation = Relation.objects.filter(from_user=request.user,to_user=user)
        if relation.exists():
            relation.delete()
            messages.success(request, 'you unfollowed this user','success')
        else:
            messages.error(request, 'you are not following this user','danger')
        return redirect('account:user-profile', user.id)

class EditUserView(LoginRequiredMixin, View):
    form_class = EditUserForm
    def get(self, request):
        form = self.form_class(instance=request.user.profile, initial={'email':request.user.email})
        return render(request, 'account/edit_profile.html', {'form':form})

    def post(self, request):
        form = self.form_class(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            request.user.email = form.cleaned_data['email']
            request.user.save()
            messages.success(request, 'profile edited successfully', 'success')
            return redirect('account:user-profile', request.user.id)