from django.shortcuts import render, redirect, get_object_or_404
from .models import Room, Booking, Payment
from .forms import BookingForm, PaymentForm, RegistrationForm, LoginForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

def home(request):
    rooms = Room.objects.filter(is_available=True)
    return render(request, 'hotel/home.html', {'rooms': rooms})

def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'hotel/room_detail.html', {'room': room})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'hotel/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'hotel/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.room = room
            if room.is_available:
                booking.save()
                # Check availability for the selected dates
                if not check_availability(room, booking.check_in_date, booking.check_out_date):
                    booking.delete()
                    form.add_error(None, "Room is not available for the selected dates.")
                    return render(request, 'hotel/book_room.html', {'form': form, 'room': room})
                # Send confirmation email
                try:
                    send_confirmation_email(booking)
                except Exception as e:
                    # Log the error but don't stop the booking process
                    print(f"Email sending failed: {e}")
                return redirect('booking_success', booking_id=booking.id)
            else:
                form.add_error(None, "Room is not available.")
    else:
        form = BookingForm()
    return render(request, 'hotel/book_room.html', {'form': form, 'room': room})

def check_availability(room, check_in_date, check_out_date):
    overlapping_bookings = Booking.objects.filter(
        room=room,
        status='Confirmed',
        check_in_date__lte=check_out_date,
        check_out_date__gte=check_in_date
    )
    return not overlapping_bookings.exists()

def send_confirmation_email(booking):
    try:
        subject = 'Booking Confirmation'
        message = f'Thank you for your booking! Your booking ID is {booking.id}.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [booking.guest_email]
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        # Log the error but don't stop the booking process
        print(f"Email sending failed: {e}")
        # You could also log this to a file or database
        raise  # Re-raise to be caught by the calling function

@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'hotel/booking_success.html', {'booking': booking})

@login_required
def make_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.save()
            booking.status = 'Confirmed'
            booking.save()
            # Send payment confirmation email
            try:
                send_payment_confirmation_email(payment)
            except Exception as e:
                # Log the error but don't stop the payment process
                print(f"Payment email sending failed: {e}")
            return redirect('payment_success', payment_id=payment.id)
    else:
        # Pre-fill the amount with the room price
        initial_amount = booking.room.price_per_night
        # Calculate number of nights
        nights = (booking.check_out_date - booking.check_in_date).days
        if nights > 0:
            initial_amount *= nights
        form = PaymentForm(initial={'amount_paid': initial_amount})
    return render(request, 'hotel/make_payment.html', {'form': form, 'booking': booking})

def send_payment_confirmation_email(payment):
    try:
        subject = 'Payment Confirmation'
        message = f'Thank you for your payment! Your payment ID is {payment.id}.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [payment.booking.guest_email]
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        # Log the error but don't stop the payment process
        print(f"Email sending failed: {e}")
        raise  # Re-raise to be caught by the calling function

@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'hotel/payment_success.html', {'payment': payment})

def search_rooms(request):
    room_type = request.GET.get('room_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    availability = request.GET.get('availability')
    sort_by = request.GET.get('sort_by')
    
    # Start with all rooms
    rooms = Room.objects.all()
    
    # Apply filters
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if min_price:
        rooms = rooms.filter(price_per_night__gte=min_price)
    if max_price:
        rooms = rooms.filter(price_per_night__lte=max_price)
    if availability == 'available':
        rooms = rooms.filter(is_available=True)
    
    # Apply sorting
    sort_by_display = "Room Number"
    if sort_by:
        if sort_by == 'price_asc':
            rooms = rooms.order_by('price_per_night')
            sort_by_display = "Price (Low to High)"
        elif sort_by == 'price_desc':
            rooms = rooms.order_by('-price_per_night')
            sort_by_display = "Price (High to Low)"
        elif sort_by == 'room_type':
            rooms = rooms.order_by('room_type')
            sort_by_display = "Room Type"
        else:  # default to room_number
            rooms = rooms.order_by('room_number')
    else:
        rooms = rooms.order_by('room_number')

    context = {
        'rooms': rooms,
        'room_type': room_type,
        'min_price': min_price,
        'max_price': max_price,
        'availability': 'Available Only' if availability == 'available' else availability,
        'sort_by': sort_by,
        'sort_by_display': sort_by_display
    }
    
    return render(request, 'hotel/search_results.html', context)

def search_rooms(request):
    room_type = request.GET.get('room_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    availability = request.GET.get('availability')
    sort_by = request.GET.get('sort_by')
    
    rooms = Room.objects.all()
    
    if room_type:
        rooms = rooms.filter(room_type__name=room_type)
    if min_price:
        rooms = rooms.filter(price_per_night__gte=min_price)
    if max_price:
        rooms = rooms.filter(price_per_night__lte=max_price)
    if availability == 'available':
        rooms = rooms.filter(is_available=True)
    
    sort_by_display = "Room Number"
    if sort_by:
        if sort_by == 'price_asc':
            rooms = rooms.order_by('price_per_night')
            sort_by_display = "Price (Low to High)"
        elif sort_by == 'price_desc':
            rooms = rooms.order_by('-price_per_night')
            sort_by_display = "Price (High to Low)"
        elif sort_by == 'room_type':
            rooms = rooms.order_by('room_type')
            sort_by_display = "Room Type"
        else:
            rooms = rooms.order_by('room_number')
    else:
        rooms = rooms.order_by('room_number')

    context = {
        'rooms': rooms,
        'room_type': room_type,
        'min_price': min_price,
        'max_price': max_price,
        'availability': 'Available Only' if availability == 'available' else availability,
        'sort_by': sort_by,
        'sort_by_display': sort_by_display
    }
    
    return render(request, 'hotel/search_results.html', context)

@login_required
def dashboard(request):
    bookings = Booking.objects.all()
    payments = Payment.objects.all()
    
    # Calculate total revenue
    total_revenue = sum(payment.amount_paid for payment in payments)
    
    context = {
        'bookings': bookings,
        'payments': payments,
        'total_revenue': total_revenue,
    }
    return render(request, 'hotel/dashboard.html', context)