from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/register/', views.user_registration, name='user_registration'),
    path('auth/signin/', views.sign_in, name='sign_in'),
    path('auth/profile/', views.user_profile, name='user_profile'),
    path('agent/dashboard/', views.agent_dashboard_access, name='agent_dashboard'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Tour endpoints
    path('tours/', views.TourListCreateView.as_view(), name='tour_list_create'),
    path('tours/<int:pk>/', views.TourDetailView.as_view(), name='tour_detail'),
    path('tours/destinations/', views.get_unique_destinations, name='get_unique_destinations'),
    
    # Chat endpoints
    path('chat/', views.chat_with_ai, name='chat_with_ai'),
    path('chat/messages/<int:message_id>/recommended-tours/', views.message_recommended_tours, name='message_recommended_tours'),
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # Saved tours endpoints
    path('saved-tours/', views.saved_tours_list, name='saved_tours_list'),
    path('saved-tours/<int:tour_id>/', views.unsave_tour, name='unsave_tour'),
    
    # Tour companies endpoint
    path('companies/', views.get_tour_companies, name='get_tour_companies'),
    path('companies/<str:company_id>/tours/', views.get_company_tours, name='get_company_tours'),
]