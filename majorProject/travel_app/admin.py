from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile

# Inline admin to display Profile fields along with User fields
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False  # Prevent accidental deletion of the profile
    verbose_name_plural = 'Profile Details'

# Extend the UserAdmin to include Profile information
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)  # Add the Profile inline to the User admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_country_code', 'get_phone_number')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    def get_country_code(self, obj):
        return obj.profile.country_code  # Display country code from Profile
    get_country_code.short_description = 'Country Code'

    def get_phone_number(self, obj):
        return obj.profile.phone_number  # Display phone number from Profile
    get_phone_number.short_description = 'Phone Number'

# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register the Profile model (optional, for standalone management)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'country_code', 'phone_number')
