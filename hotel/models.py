from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class RoomType(models.Model):
    TYPE_CHOICES = (
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Suite', 'Suite'),
        ('Deluxe', 'Deluxe'),
    )
    type_name = models.CharField(max_length=10, unique=True, choices=TYPE_CHOICES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=1)
    amenities = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.type_name


class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    floor_number = models.PositiveIntegerField()
    room_size = models.DecimalField(max_digits=5, decimal_places=2)
    has_balcony = models.BooleanField(default=False)
    has_view = models.BooleanField(default=False)
    view_description = models.CharField(max_length=100, blank=True, null=True)

    def clean(self):
        if self.has_view and not self.view_description:
            raise ValidationError("View description is required if the room has a view.")

    def __str__(self):
        return f"{self.room_number} ({self.room_type.type_name})"


class Guest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    id_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_vip = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Checked In', 'Checked In'),
        ('Checked Out', 'Checked Out'),
        ('Cancelled', 'Cancelled'),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    guest_name = models.CharField(max_length=100, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    special_requests = models.TextField(blank=True, null=True)
    number_of_guests = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    payment_method_used = models.CharField(max_length=50, blank=True, null=True)

    def clean(self):
        if self.check_in_date >= self.check_out_date:
            raise ValidationError("Check-out date must be after check-in date.")
        if self.room and self.number_of_guests > self.room.room_type.capacity:
            raise ValidationError("Number of guests exceeds room capacity.")

    def save(self, *args, **kwargs):
        if self.check_in_date and self.check_out_date and not self.total_price:
            duration = (self.check_out_date - self.check_in_date).days
            if duration <= 0:
                raise ValidationError("Invalid stay duration.")
            self.total_price = self.room.room_type.price_per_night * duration
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} - {self.guest.name if self.guest else self.guest_name}"


class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('Full', 'Full Payment'),
        ('Partial', 'Partial Payment'),
        ('Refund', 'Refund'),
    )

    PAYMENT_METHOD_TYPE_CHOICES = (
        ('Cash', 'Cash'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Online', 'Online Payment'),
        ('Mobile', 'Mobile Payment'),
        ('Voucher', 'Voucher/Coupon'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, default='Full')
    payment_method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_TYPE_CHOICES,  default='Cash')
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.id} - {self.payment_type} via {self.payment_method_type} - ${self.amount_paid}"


class RoomService(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='room_services')
    service_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    service_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=(
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ), default='Pending')

    def __str__(self):
        return f"{self.service_name} for Booking {self.booking.id}"


class Housekeeping(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    cleaning_date = models.DateField()
    cleaning_time = models.TimeField()
    status = models.CharField(max_length=20, choices=(
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ), default='Scheduled')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Housekeeping for Room {self.room.room_number} on {self.cleaning_date}"


class MaintenanceRequest(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=(
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ), default='Pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Maintenance Request for Room {self.room.room_number}"


class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    review_date = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"Review for Booking {self.booking.id} - {self.rating} stars"
