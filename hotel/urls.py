from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('book/<int:room_id>/', views.book_room, name='book_room'),
    path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('payment/<int:booking_id>/', views.make_payment, name='make_payment'),
    path('payment/success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('search/', views.search_rooms, name='search_rooms'),
    path('dashboard/', views.dashboard, name='dashboard'),
]