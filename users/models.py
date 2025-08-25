from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import datetime


def default_start_date():
    return timezone.now().date()


def default_end_date():
    return timezone.now().date() + datetime.timedelta(days=7)


class TourCompany(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Tour Companies"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('normal', 'Normal User'),
        ('agent', 'Tour Agent'),
    )
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='normal'
    )
    tour_company = models.ForeignKey(
        TourCompany,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agents',
        help_text="Tour company this agent belongs to (only for agents)"
    )
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Full address")
    city = models.CharField(max_length=100, blank=True, help_text="City")
    country = models.CharField(max_length=100, blank=True, help_text="Country")
    postal_code = models.CharField(max_length=20, blank=True, help_text="Postal/ZIP code")
    
    # Additional Profile Information
    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of birth")
    profile_picture = models.URLField(blank=True, help_text="Profile picture URL")
    bio = models.TextField(blank=True, max_length=500, help_text="Short bio/description")
    
    # Preferences
    preferred_currency = models.CharField(max_length=3, default='USD', help_text="Preferred currency code")
    newsletter_subscription = models.BooleanField(default=True, help_text="Subscribe to newsletter")
    
    # Timestamps
    profile_updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user_type == 'agent' and self.tour_company:
            return f"{self.username} ({self.tour_company.name})"
        return f"{self.username} ({self.get_user_type_display()})"


class Tour(models.Model):
    
    MEAL_PLAN_CHOICES = [
        ('room_only', 'Room Only'),
        ('bed_breakfast', 'Bed & Breakfast'),
        ('half_board', 'Half Board'),
        ('full_board', 'Full Board'),
        ('all_inclusive', 'All Inclusive'),
    ]
    
    FLIGHT_TYPE_CHOICES = [
        ('direct', 'Direct Flight'),
        ('layover', 'Flight with Layover'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tours')
    title = models.CharField(max_length=200)
    description = models.TextField()
    destination = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    hotel_name = models.CharField(max_length=200, blank=True, help_text="Name of the hotel included in the tour")
    start_date = models.DateField(default=default_start_date)
    end_date = models.DateField(default=default_end_date)
    visa_required = models.BooleanField(default=False, help_text="Check if visa is required for this destination")
    meal_plan = models.CharField(
        max_length=20, 
        choices=MEAL_PLAN_CHOICES, 
        default='room_only',
        help_text="Meal plan included in the tour package"
    )
    flight_type = models.CharField(
        max_length=20,
        choices=FLIGHT_TYPE_CHOICES,
        default='direct',
        help_text="Type of flight included in the tour"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.agent.get_full_name() or self.agent.username}"
    
    @property
    def formatted_price(self):
        return f"${self.price:,.2f}"


class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, blank=True, help_text="Conversation title (auto-generated from first message)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title or f'Conversation {self.id}'}"
    
    def save(self, *args, **kwargs):
        # Auto-generate title from first user message if not set
        if not self.title and self.pk:
            first_message = self.messages.filter(sender='user').first()
            if first_message:
                # Use first 50 characters of the message as title
                self.title = first_message.content[:50] + ('...' if len(first_message.content) > 50 else '')
        super().save(*args, **kwargs)


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI Assistant'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(help_text="The message content")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    recommended_tours = models.ManyToManyField(
        Tour, 
        blank=True, 
        related_name='chat_recommendations',
        help_text="Tours recommended in this message"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender}: {self.content[:100]}{'...' if len(self.content) > 100 else ''}"


class SavedTour(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_tours')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='saved_by_users')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'tour')
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.tour.title}"
