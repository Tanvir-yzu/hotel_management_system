from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Room, Guest, Booking, Payment

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class BookingForm(forms.ModelForm):
    # Fields for guest information (to create or select a guest)
    guest_name = forms.CharField(max_length=100, required=True, label="Guest Name")
    guest_email = forms.EmailField(required=True, label="Guest Email")

    class Meta:
        model = Booking
        fields = ['room', 'check_in_date', 'check_out_date', 'status']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(choices=[
                ('Pending', 'Pending'),
                ('Confirmed', 'Confirmed'),
                ('Cancelled', 'Cancelled'),
            ]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make room field filter only available rooms
        self.fields['room'].queryset = Room.objects.filter(is_available=True)

    def save(self, commit=True):
        # Get or create the Guest instance based on email
        guest_email = self.cleaned_data['guest_email']
        guest_name = self.cleaned_data['guest_name']
        guest, created = Guest.objects.get_or_create(
            email=guest_email,
            defaults={'name': guest_name}
        )
        # Update name if guest already exists but name is different
        if not created and guest.name != guest_name:
            guest.name = guest_name
            guest.save()

        # Assign the guest to the booking
        booking = super().save(commit=False)
        booking.guest = guest
        if commit:
            booking.save()
        return booking

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount_paid', 'payment_method']
        widgets = {
            'payment_method': forms.Select(choices=[
                ('Credit Card', 'Credit Card'),
                ('PayPal', 'PayPal'),
                ('Bank Transfer', 'Bank Transfer'),
            ]),
        }