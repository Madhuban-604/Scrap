from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .form import SignupForm  
from .models import Profile
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib import messages  
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

from django.core.mail import EmailMessage

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Save profile information
            Profile.objects.create(
                user=user,
                country_code=form.cleaned_data['country_code'],
                phone_number=form.cleaned_data['phone_number']
            )

            # Generate email confirmation URL
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

            # Get the current site domain (useful for generating the URL for confirmation)
            current_site = get_current_site(request)
            confirmation_url = f"http://{current_site.domain}/account/confirm-email/{uid}/{token}/"

            # Prepare email
            subject = "Confirm your email address"
            html_message = render_to_string(
                'confirmation_email.html', 
                {
                    'user': user,
                    'confirmation_url': confirmation_url,
                    'current_year': datetime.now().year  # Adding current year dynamically for footer
                }
            )
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email='your-email@example.com',  # Replace with your sender email
                to=[user.email],
            )
            email.content_subtype = "html"  # Specify that this email contains HTML content
            email.send()

            messages.success(request, 'You have signed up successfully. Please check your email for confirmation.')
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def confirm_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
        
        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            user.is_active = True  # Activate the user
            user.save()
            messages.success(request, 'Your email has been confirmed successfully! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid confirmation link.')
            return redirect('login')

    except (TypeError, ValueError, OverflowError, user.DoesNotExist):
        messages.error(request, 'Invalid confirmation link.')
        return redirect('login')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('landing')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')


def profile(request):
    context = {}
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            context['profile'] = profile
        except Profile.DoesNotExist:
            profile = None  # User doesn't have a profile yet
            messages.warning(request, "Profile not found. Please complete your profile.")
        context.update({
            'user': request.user,
            'profile': profile,
        })
    else:
        # User is not logged in, still show the page without details
        messages.info(request, "Please log in to see profile details.")

    return render(request, 'profile.html', context)


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

def landing(request):
    return render(request, 'landing.html')

def explore(request):
    return render(request, 'explore.html')

def packages(request):
    return render(request, 'packages.html')

def bookings(request):
    if request.method == "POST":
        # Extract form data (assume AJAX submission for real-time updates)
        package = request.POST.get('package')
        name = request.POST.get('name')
        email = request.POST.get('email')
        date = request.POST.get('date')
        preferences = request.POST.get('preferences')

        # Validate and process data
        if package and name and email and date:
            # Mocked booking options response
            options = [
                f"Option 1: {package} - {date}",
                f"Option 2: Discounted Package - {package}",
            ]
            return JsonResponse({'success': True, 'options': options})
        return JsonResponse({'success': False, 'message': "Please fill in all fields!"})
    
        package_name = request.POST.get('package')
        date = request.POST.get('date')
        preferences = request.POST.get('preferences')

        if package_name and date:
            # Store booking data in the session
            request.session['booking_data'] = {
                'package_name': package_name,
                'date': date,
                'preferences': preferences,
            }
            return redirect('bookingDetails')

    # Render the page for GET requests
    return render(request, 'bookings.html')

def bookings_redirect(request):
    messages.warning(request, "Please log in to access the bookings page.")
    return redirect('login')  # Assuming your login URL name is 'login'

def contact(request):
    return render(request, 'contact.html')

def terms_conditions(request):
    return render(request, 'terms.html')

def faq(request):
    return render(request, 'faq.html')

def about(request):
    return render(request, 'about.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('profile')  # Redirect to the profile page after saving

    return redirect('profile')  # Redirect if the method is not POST
# Razorpay client initialization
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
@csrf_exempt
def create_payment(request):
    """
    Creates a Razorpay order for a specific package.
    """
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        amount = int(data.get("amount", 0))  # Amount in paise
        package = data.get("package", "Unknown Package")

        if amount <= 0:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        try:
            # Create Razorpay order
            order = razorpay_client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": "1"
            })
            return JsonResponse({"order_id": order["id"]})
        except razorpay.errors.RazorpayError as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def payment_handler(request):
    """
    Handles Razorpay webhook or payment success response.
    """
    if request.method == "POST":
        try:
            # Verify the payment signature
            data = request.POST
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": data["razorpay_order_id"],
                "razorpay_payment_id": data["razorpay_payment_id"],
                "razorpay_signature": data["razorpay_signature"],
            })

            # Process the payment (e.g., save to the database)
            # You can implement logic here to mark an order as "paid"
            return JsonResponse({"status": "Payment verified successfully"})
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"error": "Signature verification failed"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)


@login_required
def bookingDetails(request):
    # Retrieve the booking data from session
    booking_data = request.session.get('booking_data', None)
    
    if not booking_data:
        # If no booking data exists in session, redirect with a message
        messages.info(request, "It looks like you haven't booked any packages yet. Please explore our Travel Packages to get started!")
        return render(request, 'bookingDetails.html', {'booking_data': booking_data})

    # Pass the booking data to the template if it exists
    return render(request, 'bookingDetails.html', {'booking_data': booking_data})
