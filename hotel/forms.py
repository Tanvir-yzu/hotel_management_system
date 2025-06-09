from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Booking, Payment

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class LoginForm(AuthenticationForm):
    # Using Django's built-in AuthenticationForm
    pass

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in_date', 'check_out_date', 'guest_email']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount_paid', 'payment_method_type']
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'step': '0.01'}),
            'payment_method_type': forms.Select(),
        }
