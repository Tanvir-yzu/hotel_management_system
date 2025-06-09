from django.contrib import admin
from .models import (
    RoomType, Room, Guest, Booking, Payment,
    RoomService, Housekeeping, MaintenanceRequest, Review
)

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'price_per_night', 'capacity')
    search_fields = ('type_name',)
    list_filter = ('type_name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'is_available', 'floor_number', 'has_view')
    list_filter = ('room_type', 'is_available', 'floor_number')
    search_fields = ('room_number',)

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_vip', 'registration_date')
    search_fields = ('name', 'email')
    list_filter = ('is_vip',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'room', 'check_in_date', 'check_out_date', 'status', 'is_paid')
    list_filter = ('status', 'is_paid', 'check_in_date')
    search_fields = ('guest__name', 'guest_name', 'guest_email')
    date_hierarchy = 'check_in_date'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount_paid', 'payment_type', 'payment_method_type', 'payment_date')
    list_filter = ('payment_type', 'payment_method_type', 'payment_date')
    search_fields = ('transaction_id', 'payment_method')

@admin.register(RoomService)
class RoomServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'booking', 'quantity', 'price_per_unit', 'status', 'service_date')
    list_filter = ('status', 'service_date')
    search_fields = ('service_name',)

@admin.register(Housekeeping)
class HousekeepingAdmin(admin.ModelAdmin):
    list_display = ('room', 'cleaning_date', 'cleaning_time', 'status')
    list_filter = ('status', 'cleaning_date')
    search_fields = ('room__room_number',)

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('room', 'request_date', 'status', 'assigned_to')
    list_filter = ('status', 'request_date')
    search_fields = ('room__room_number', 'description', 'assigned_to__username')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'review_date', 'is_public')
    list_filter = ('rating', 'is_public', 'review_date')
    search_fields = ('booking__guest__name',)
