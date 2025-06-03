from django.contrib import admin
from .models import RoomType, Room, Guest, Booking, Payment

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'price_per_night')
    search_fields = ('type_name',)
    list_filter = ('type_name',)
    ordering = ('type_name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'is_available')
    list_filter = ('room_type', 'is_available')
    search_fields = ('room_number', 'room_type__type_name')
    ordering = ('room_number',)

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')
    ordering = ('name',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'room', 'check_in_date', 'check_out_date', 'status', 'booking_date')
    list_filter = ('status', 'check_in_date', 'check_out_date', 'room__room_type')
    search_fields = ('guest__name', 'guest__email', 'room__room_number')
    date_hierarchy = 'booking_date'
    ordering = ('-booking_date',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount_paid', 'payment_method', 'payment_date')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('booking__guest__name', 'booking__room__room_number')
    date_hierarchy = 'payment_date'
    ordering = ('-payment_date',)