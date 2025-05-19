from django import forms
from .models import Room, Booking, Payment
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest_name', 'guest_email', 'check_in_date', 'check_out_date']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'})
        }

class PaymentForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cash', 'Cash'),
        ('Mobile Banking', 'Mobile Banking'),  # Add new payment method here
        ('Cryptocurrency', 'Cryptocurrency'),  # Add another payment method
    ]
    
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, required=True)
    
    class Meta:
        model = Payment
        fields = ['amount_paid', 'payment_method']