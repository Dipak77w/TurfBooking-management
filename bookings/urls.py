from django.urls import path
from . import views

urlpatterns = [
    # Customer Booking Flow
    path('turf/<slug:slug>/book/', views.initiate_booking_view, name='initiate_booking'),
    path('checkout/<str:booking_id>/', views.checkout_payment_view, name='checkout_payment'),
    path('cancel/<str:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('receipt/<str:booking_id>/', views.booking_receipt_view, name='booking_receipt'),
    path('review/<str:booking_id>/', views.submit_review_view, name='submit_review'),
    path('dashboard/', views.customer_dashboard_view, name='customer_dashboard'),
    
    # Turf Owner (Admin) Flow
    path('owner/dashboard/', views.owner_dashboard_view, name='owner_dashboard'),
    path('owner/payment/<int:payment_id>/verify/', views.verify_payment_action, name='verify_payment_action'),
    path('owner/booking/<str:booking_id>/action/', views.admin_booking_action, name='admin_booking_action'),
]
