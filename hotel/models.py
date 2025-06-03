from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    ROOM_TYPES = (
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Suite', 'Suite'),
        ('Deluxe', 'Deluxe'),
    )
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.room_number} ({self.room_type})"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # Added user field
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100) # May still be useful if a user books for someone else
    guest_email = models.EmailField() # May still be useful for contact, or if user is not logged in
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')  # Pending, Confirmed, Cancelled

    def __str__(self):
        return f"Booking {self.id} - {self.guest_name}"

    def get_total_price(self):
        if self.check_in_date and self.check_out_date and self.room:
            duration = (self.check_out_date - self.check_in_date).days
            if duration <= 0: # Ensure at least one night is charged if dates are same or invalid
                duration = 1
            return duration * self.room.price_per_night
        return 0

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)  # Credit Card, PayPal, etc.

    def __str__(self):
        return f"Payment {self.id} - ${self.amount_paid}"