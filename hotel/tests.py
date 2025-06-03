from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, call
import datetime # Use this for date objects specifically
from decimal import Decimal

from .models import Room, Booking

class HotelViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.regular_user_password = 'password123'
        self.regular_user = User.objects.create_user(username='testuser', email='testuser@example.com', password=self.regular_user_password)

        self.staff_user_password = 'staffpassword123'
        self.staff_user = User.objects.create_user(username='staffuser', email='staffuser@example.com', password=self.staff_user_password, is_staff=True)

        self.room1 = Room.objects.create(room_number='101', room_type='Single', price_per_night=Decimal('100.00'), is_available=True)
        self.room2 = Room.objects.create(room_number='102', room_type='Double', price_per_night=Decimal('150.00'), is_available=False)
        self.room3 = Room.objects.create(room_number='103', room_type='Suite', price_per_night=Decimal('250.00'), is_available=True)

        self.today = timezone.now().date()
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.day_after_tomorrow = self.today + datetime.timedelta(days=2)

    def _login_regular_user(self):
        self.client.login(username=self.regular_user.username, password=self.regular_user_password)

    def _login_staff_user(self):
        self.client.login(username=self.staff_user.username, password=self.staff_user_password)

    # --- book_room View Tests ---
    @patch('hotel.views.send_mail') # Mocks django.core.mail.send_mail used in hotel.views
    def test_successful_booking_creation(self, mock_send_mail):
        self._login_regular_user()
        booking_data = {
            'guest_name': 'Test Guest',
            'guest_email': self.regular_user.email,
            'check_in_date': self.today.strftime('%Y-%m-%d'),
            'check_out_date': self.tomorrow.strftime('%Y-%m-%d'),
        }
        response = self.client.post(reverse('book_room', args=[self.room1.id]), data=booking_data)

        self.assertEqual(response.status_code, 302) # Redirects to booking_success
        self.assertTrue(Booking.objects.filter(room=self.room1, user=self.regular_user).exists())
        booking = Booking.objects.get(room=self.room1, user=self.regular_user)
        self.assertEqual(booking.guest_name, 'Test Guest')
        self.assertEqual(booking.status, 'Pending') # Default status
        mock_send_mail.assert_called_once() # Check if send_confirmation_email was called

    def test_booking_fail_room_not_available_general(self):
        self._login_regular_user()
        booking_data = {
            'guest_name': 'Test Guest',
            'guest_email': self.regular_user.email,
            'check_in_date': self.today.strftime('%Y-%m-%d'),
            'check_out_date': self.tomorrow.strftime('%Y-%m-%d'),
        }
        response = self.client.post(reverse('book_room', args=[self.room2.id]), data=booking_data)
        self.assertEqual(response.status_code, 200) # Renders form again
        self.assertContains(response, "This room is currently not available.")
        self.assertFalse(Booking.objects.filter(room=self.room2).exists())

    def test_booking_fail_room_not_available_specific_dates(self):
        self._login_regular_user()
        # Pre-existing confirmed booking for room3
        Booking.objects.create(
            room=self.room3, user=self.staff_user, guest_name='Other Guest', guest_email='other@example.com',
            check_in_date=self.today, check_out_date=self.tomorrow, status='Confirmed'
        )
        booking_data = {
            'guest_name': 'Test Guest',
            'guest_email': self.regular_user.email,
            'check_in_date': self.today.strftime('%Y-%m-%d'), # Overlapping dates
            'check_out_date': self.tomorrow.strftime('%Y-%m-%d'),
        }
        response = self.client.post(reverse('book_room', args=[self.room3.id]), data=booking_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room is not available for the selected dates.")
        # Ensure no new booking by regular_user for these dates
        self.assertFalse(Booking.objects.filter(room=self.room3, user=self.regular_user).exists())

    @patch('hotel.views.send_mail')
    def test_booking_associates_logged_in_user(self, mock_send_mail):
        self._login_regular_user()
        booking_data = {
            'guest_name': 'Test Guest Logged In', # Form still requires guest_name/email
            'guest_email': self.regular_user.email,
            'check_in_date': self.today.strftime('%Y-%m-%d'),
            'check_out_date': self.tomorrow.strftime('%Y-%m-%d'),
        }
        self.client.post(reverse('book_room', args=[self.room1.id]), data=booking_data)
        self.assertTrue(Booking.objects.filter(room=self.room1, user=self.regular_user).exists())

    @patch('hotel.views.logger.error') # Patch the logger used in views
    @patch('hotel.views.send_mail', side_effect=Exception("SMTP Error")) # Mock send_mail to raise an error
    def test_booking_email_failure_logged_and_booking_succeeds(self, mock_send_mail_func, mock_logger_error):
        self._login_regular_user()
        booking_data = {
            'guest_name': 'Email Fail Guest',
            'guest_email': self.regular_user.email,
            'check_in_date': self.today.strftime('%Y-%m-%d'),
            'check_out_date': self.tomorrow.strftime('%Y-%m-%d'),
        }
        response = self.client.post(reverse('book_room', args=[self.room1.id]), data=booking_data)
        self.assertEqual(response.status_code, 302) # Should still redirect to success
        self.assertTrue(Booking.objects.filter(room=self.room1, user=self.regular_user, guest_name='Email Fail Guest').exists())
        mock_send_mail_func.assert_called_once()
        mock_logger_error.assert_called_once()
        args, kwargs = mock_logger_error.call_args
        self.assertIn(f"Failed to send confirmation email for Booking ID", args[0])
        self.assertIn("SMTP Error", args[0])

    # --- user_booking_history View Tests ---
    def test_user_booking_history_authenticated_access(self):
        self._login_regular_user()
        response = self.client.get(reverse('user_booking_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hotel/user_booking_history.html')

    def test_user_booking_history_unauthenticated_redirect(self):
        response = self.client.get(reverse('user_booking_history'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url) # Check it redirects to login

    def test_user_booking_history_displays_own_bookings(self):
        self._login_regular_user()
        booking1 = Booking.objects.create(
            user=self.regular_user, room=self.room1, guest_name=self.regular_user.username, guest_email=self.regular_user.email,
            check_in_date=self.today, check_out_date=self.tomorrow, status='Confirmed'
        )
        # Booking by another user (staff user for simplicity)
        booking2 = Booking.objects.create(
            user=self.staff_user, room=self.room3, guest_name=self.staff_user.username, guest_email=self.staff_user.email,
            check_in_date=self.today, check_out_date=self.tomorrow, status='Pending'
        )
        response = self.client.get(reverse('user_booking_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, booking1.room.room_number)
        self.assertNotContains(response, booking2.room.room_number)
        self.assertEqual(len(response.context['bookings']), 1)
        self.assertEqual(response.context['bookings'][0], booking1)

    def test_user_booking_history_total_price(self):
        self._login_regular_user()
        # Booking for 2 nights: today to day_after_tomorrow
        booking = Booking.objects.create(
            user=self.regular_user, room=self.room1, guest_name=self.regular_user.username, guest_email=self.regular_user.email,
            check_in_date=self.today, check_out_date=self.day_after_tomorrow, status='Confirmed'
        )
        expected_price = self.room1.price_per_night * 2 # 100.00 * 2 = 200.00
        self.assertEqual(booking.get_total_price(), expected_price)

        response = self.client.get(reverse('user_booking_history'))
        self.assertEqual(response.status_code, 200)
        # Example: Check if the calculated price is present in the rendered HTML
        # This can be fragile. A better way is to check context if possible, or use more specific selectors.
        self.assertContains(response, f"${expected_price}")


    # --- dashboard View Tests ---
    def test_dashboard_non_staff_redirect_or_forbidden(self):
        self._login_regular_user() # Regular user is not staff
        response = self.client.get(reverse('dashboard'))
        # Expect redirect to login because user_passes_test redirects by default if login_url not specified
        # Or, if login_url is None, it returns 403 Forbidden. Django's default is login_url=settings.LOGIN_URL
        self.assertTrue(response.status_code == 302 or response.status_code == 403)
        if response.status_code == 302:
             self.assertIn(reverse('login'), response.url.split('?')[0])


    def test_dashboard_staff_access(self):
        self._login_staff_user()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hotel/dashboard.html')

    def test_dashboard_context_booking_counts(self):
        self._login_staff_user()
        Booking.objects.create(user=self.regular_user, room=self.room1, guest_name='P1', guest_email='p1@e.com', check_in_date=self.today, check_out_date=self.tomorrow, status='Pending')
        Booking.objects.create(user=self.regular_user, room=self.room3, guest_name='C1', guest_email='c1@e.com', check_in_date=self.today, check_out_date=self.tomorrow, status='Confirmed')
        Booking.objects.create(user=self.staff_user, room=self.room1, guest_name='P2', guest_email='p2@e.com', check_in_date=self.tomorrow, check_out_date=self.day_after_tomorrow, status='Pending')
        # Assuming 'Cancelled' is a valid status that can be set
        # Booking.objects.create(user=self.staff_user, room=self.room3, guest_name='X1', guest_email='x1@e.com', check_in_date=self.tomorrow, check_out_date=self.day_after_tomorrow, status='Cancelled')

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pending_bookings_count'], 2)
        self.assertEqual(response.context['confirmed_bookings_count'], 1)
        self.assertEqual(response.context['cancelled_bookings_count'], 0) # No 'Cancelled' bookings created yet

    def test_dashboard_context_recent_bookings_and_all_rooms(self):
        self._login_staff_user()
        # Create a few bookings to test recent_bookings (up to 10)
        # Create bookings with specific booking_date to ensure predictable order for testing
        base_booking_time = timezone.now()
        for i in range(3):
             Booking.objects.create(user=self.regular_user, room=self.room1, guest_name=f'Guest {i}', guest_email=f'g{i}@e.com',
                                   check_in_date=self.today + datetime.timedelta(days=i*2),
                                   check_out_date=self.today + datetime.timedelta(days=i*2 + 1),
                                   status='Pending',
                                   booking_date=base_booking_time - datetime.timedelta(hours=i)) # Newest first in this creation loop


        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        self.assertIn('recent_bookings', response.context)
        self.assertTrue(len(response.context['recent_bookings']) <= 10)

        # Check if the bookings are ordered by booking_date descending (most recent first)
        # recent_bookings[0] should be the one with i=0 (latest booking_date).
        recent_bookings_from_context = list(response.context['recent_bookings'])
        if len(recent_bookings_from_context) > 1:
            # Ensure they are sorted by booking_date descending
            for i in range(len(recent_bookings_from_context) - 1):
                self.assertTrue(recent_bookings_from_context[i].booking_date >= recent_bookings_from_context[i+1].booking_date)


        self.assertIn('all_rooms', response.context)
        # The view orders rooms by room_number. setUp creates room1, room2, room3 in that order.
        expected_rooms_order = [self.room1, self.room2, self.room3]
        self.assertListEqual(list(response.context['all_rooms']), expected_rooms_order)

# Example of how to run tests in Django:
# python manage.py test hotel.tests
# (or specific test class/method)
# python manage.py test hotel.tests.HotelViewsTestCase
# python manage.py test hotel.tests.HotelViewsTestCase.test_successful_booking_creation

# Note on logging test:
# To properly test that logging to a file occurs, you might need to
# configure a specific log handler for tests or check the file content,
# which can be complex. The current mock test for logger.error checks
# if the logging method was called with correct parameters, which is a good start.
# Testing that `send_mail` itself is called is done by mocking `send_mail`.
# Testing that `django.core.mail.send_mail` is called from `hotel.views.send_confirmation_email`
# requires patching at 'hotel.views.send_mail'.
# If send_confirmation_email directly calls django.core.mail.send_mail, then
# @patch('django.core.mail.send_mail') would be needed if not patching at hotel.views.send_mail.
# Current patch is at 'hotel.views.send_mail', which is correct as it's the import location in views.py.

# Final check on BookingForm:
# The tests assume BookingForm takes 'guest_name', 'guest_email', 'check_in_date', 'check_out_date'.
# If the form is more complex or has different fields, tests would need adjustment.
# The view does `form = BookingForm(request.POST)`.
# Then `booking = form.save(commit=False)`.
# Then `booking.room = room` and `booking.user = request.user`.
# This seems fine.
# The `guest_email` in the form is used by `send_confirmation_email(booking)`.
# `booking.guest_name` is also used.
# The model has `user`, `guest_name`, `guest_email`. It's okay to have both user and guest_name/email
# if a user can book for someone else, or if bookings can be made without login (though book_room is @login_required).
# The current setup looks consistent.
```
