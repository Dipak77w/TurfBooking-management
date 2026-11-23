from django.urls import path
from . import views

urlpatterns = [
    # Customer / Public Views
    path('', views.turf_list_view, name='turf_list'),
    path('<slug:slug>/', views.turf_detail_view, name='turf_detail'),
    path('<slug:slug>/slots/', views.api_get_slots_view, name='api_get_slots'),
    
    # Turf Owner Management
    path('owner/add/', views.add_turf_view, name='add_turf'),
    path('owner/<slug:slug>/edit/', views.edit_turf_view, name='edit_turf'),
    path('owner/<slug:slug>/delete/', views.delete_turf_view, name='delete_turf'),
    path('owner/<slug:slug>/photos/', views.manage_turf_images_view, name='manage_turf_images'),
    path('owner/photo/<int:image_id>/delete/', views.delete_turf_image_view, name='delete_turf_image'),
    path('owner/<slug:slug>/blocked-slots/', views.manage_blocked_slots_view, name='manage_blocked_slots'),
    path('owner/blocked-slot/<int:slot_id>/delete/', views.delete_blocked_slot_view, name='delete_blocked_slot'),
    path('owner/review/<int:review_id>/moderate/', views.moderate_review_view, name='moderate_review'),
]
