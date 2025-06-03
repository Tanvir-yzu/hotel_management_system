from django.db import models
from django.contrib.auth.models import User

class RoomType(models.Model):
    type_name = models.CharField(
        max_length=10,
        unique=True,
        choices=(
            ('Single', 'Single'),
            ('Double', 'Double'),
            ('Suite', 'Suite'),
            ('Deluxe', 'Deluxe'),
        )
    )
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.type_name

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.room_number} ({self.room_type.type_name})"

class Guest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True, blank=True)  # Temporary nullable
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    # Keep guest_name and guest_email temporarily for data migration
    guest_name = models.CharField(max_length=100, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return f"Booking {self.id} - {self.guest.name if self.guest else self.guest_name}"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)

    def __str__(self):
        return f"Payment {self.id} - ${self.amount_paid}"