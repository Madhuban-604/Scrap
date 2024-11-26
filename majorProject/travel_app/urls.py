from django.urls import path
from . import views
from .views import landing, explore, packages, bookings, bookingDetails, contact, terms_conditions, edit_profile, bookings_redirect  # Ensure this view is imported
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('', views.landing, name='landing'),
    path('explore/', explore, name='explore'),  
    path('packages/', packages, name='packages'),  
    path('bookings/', bookings_redirect, name='bookings_redirect'),  # Redirects to login
    path('bookings/', login_required(bookings), name='bookings'),  # Protects the bookings page
    path('bookings/page/', bookings, name='bookings'), 
    path('contact/', contact, name='contact'),  
    path('terms/', terms_conditions, name='terms'),
    path('account/confirm-email/<uidb64>/<token>/', views.confirm_email, name='confirm_email'),
    path('faq/', views.faq, name='faq'),
    path('about/', views.about, name='about'),
    path('edit_profile/', edit_profile, name='edit_profile'), 
    path('create-payment/', views.create_payment, name='create_payment'),
    path('payment-handler/', views.payment_handler, name='payment_handler'),
    path('bookingDetails/', views.bookingDetails, name='bookingDetails'),  
]
