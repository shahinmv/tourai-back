from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Tour, TourCompany, Conversation, ChatMessage, SavedTour


@admin.register(TourCompany)
class TourCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'description', 'email', 'phone', 'website')
        }),
        ('Business Details', {
            'fields': ('address',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'tour_company', 'is_staff')
    list_filter = ('user_type', 'tour_company', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('User Details', {'fields': ('user_type', 'tour_company')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('User Details', {'fields': ('user_type', 'tour_company')}),
    )


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'destination', 'hotel_name', 'formatted_price', 'meal_plan', 'flight_type', 'start_date', 'end_date', 'visa_required', 'is_active', 'created_at')
    list_filter = ('meal_plan', 'flight_type', 'visa_required', 'is_active', 'start_date', 'created_at', 'agent__user_type')
    search_fields = ('title', 'destination', 'hotel_name', 'description', 'agent__username', 'agent__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('agent', 'title', 'description')
        }),
        ('Tour Details', {
            'fields': ('destination', 'hotel_name', 'price', 'start_date', 'end_date', 'visa_required', 'meal_plan', 'flight_type')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agent')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'message_count', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'user__user_type')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('messages')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content_preview', 'recommended_tour_count', 'created_at')
    list_filter = ('sender', 'created_at', 'conversation__user__user_type')
    search_fields = ('content', 'conversation__user__username', 'conversation__title')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
    content_preview.short_description = 'Content Preview'
    
    def recommended_tour_count(self, obj):
        return obj.recommended_tours.count()
    recommended_tour_count.short_description = 'Recommended Tours'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation__user').prefetch_related('recommended_tours')


@admin.register(SavedTour)
class SavedTourAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tour', 'saved_at')
    list_filter = ('saved_at', 'user__user_type', 'tour__destination')
    search_fields = ('user__username', 'user__email', 'tour__title', 'tour__destination')
    readonly_fields = ('saved_at',)
    date_hierarchy = 'saved_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'tour', 'tour__agent')
