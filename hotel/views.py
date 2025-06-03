from django.shortcuts import render, redirect, get_object_or_404
from .models import Room, Booking, Payment
from .forms import BookingForm, PaymentForm, RegistrationForm, LoginForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from django.db import transaction
import logging

# Basic logging configuration
logging.basicConfig(filename='email_errors.log',
                    level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(module)s:%(funcName)s:%(lineno)d:%(message)s')
logger = logging.getLogger(__name__)

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
            # General availability check for the room itself
            if not room.is_available:
                form.add_error(None, "This room is currently not available.")
                return render(request, 'hotel/book_room.html', {'form': form, 'room': room})

            booking_details = form.cleaned_data

            # Note: The problem description implies booking_id might be relevant for check_availability
            # if we were updating a booking. However, this view seems to be for new bookings.
            # Passing None or not passing booking_id for new bookings is appropriate.
            # For this refactor, we assume new bookings, so booking.id isn't available yet.
            if not check_availability(room, booking_details['check_in_date'], booking_details['check_out_date']):
                form.add_error(None, "Room is not available for the selected dates.")
                return render(request, 'hotel/book_room.html', {'form': form, 'room': room})

            try:
                with transaction.atomic():
                    booking = form.save(commit=False)
                    booking.room = room
                    if request.user.is_authenticated:
                        booking.user = request.user
                    # Ensure guest_email is still populated, e.g. from form, or from user.email
                    # The BookingForm should ideally handle populating guest_name and guest_email.
                    # If user is logged in, we can pre-fill guest_email from user.email if desired.
                    # For now, we assume BookingForm collects guest_email.
                    booking.save() # First save to get an ID, status should be 'Pending' or similar by default

                    # Send confirmation email
                    # This email should ideally be for a 'Pending' booking or a successful transactional save
                    send_confirmation_email(booking)

                    return redirect('booking_success', booking_id=booking.id)
            except Exception as e:
                # Log the error if the transaction failed for some reason (other than availability)
                print(f"Booking transaction failed: {e}")
                form.add_error(None, "There was an issue processing your booking. Please try again.")
                # Fall through to render the form again
    else:
        form = BookingForm()
    return render(request, 'hotel/book_room.html', {'form': form, 'room': room})

def check_availability(room, check_in_date, check_out_date, booking_id=None):
    # Corrected overlap logic:
    # A booking overlaps if its check-in is before the other's check-out
    # AND its check-out is after the other's check-in.
    overlapping_bookings = Booking.objects.filter(
        room=room,
        status='Confirmed',
        check_in_date__lt=check_out_date,  # strictly less than
        check_out_date__gt=check_in_date   # strictly greater than
    )
    if booking_id:
        overlapping_bookings = overlapping_bookings.exclude(id=booking_id)
    return not overlapping_bookings.exists()

def send_confirmation_email(booking):
    try:
        subject = 'Booking Confirmation'
        message = f'Thank you for your booking! Your booking ID is {booking.id}.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [booking.guest_email]
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        logger.error(f"Failed to send confirmation email for Booking ID {booking.id}: {e}", exc_info=True)
        # Removed raise: allow booking to proceed even if email fails.

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
                # Error is logged within send_payment_confirmation_email, no need to print here
                # If that function no longer raises, this try-except might be less critical here,
                # but keeping it doesn't harm, in case other errors occur before/after email.
                # The main change is that send_payment_confirmation_email itself won't raise for email issues.
                pass # Email errors are logged by the function, allow flow to continue
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
        logger.error(f"Failed to send payment confirmation email for Payment ID {payment.id} (Booking ID {payment.booking.id}): {e}", exc_info=True)
        # Removed raise: allow payment confirmation to proceed even if email fails.

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


@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard(request):
    all_bookings_list = Booking.objects.all() # Renamed to avoid conflict if needed, used for total guests
    payments = Payment.objects.all()
    
    # Calculate total revenue
    total_revenue = sum(payment.amount_paid for payment in payments if payment.amount_paid is not None) # Added safety for None
    
    # Booking counts by status
    pending_bookings_count = Booking.objects.filter(status='Pending').count()
    confirmed_bookings_count = Booking.objects.filter(status='Confirmed').count()
    cancelled_bookings_count = Booking.objects.filter(status='Cancelled').count() # Assuming 'Cancelled' is a valid status

    # Recent bookings
    recent_bookings = Booking.objects.order_by('-booking_date')[:10]

    # All rooms for availability display
    all_rooms = Room.objects.all().order_by('room_number')

    context = {
        'bookings': all_bookings_list, # Keep for existing template parts like "Total Guests"
        'payments': payments,
        'total_revenue': total_revenue,
        'pending_bookings_count': pending_bookings_count,
        'confirmed_bookings_count': confirmed_bookings_count,
        'cancelled_bookings_count': cancelled_bookings_count,
        'recent_bookings': recent_bookings,
        'all_rooms': all_rooms,
    }
    return render(request, 'hotel/dashboard.html', context)

@login_required
def user_booking_history(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-check_in_date')
    return render(request, 'hotel/user_booking_history.html', {'bookings': bookings})