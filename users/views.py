from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignInSerializer, UserSerializer, TourSerializer, TourCreateSerializer, ConversationSerializer, ConversationListSerializer, ChatMessageSerializer, SavedTourSerializer
from .models import Tour, Conversation, ChatMessage, SavedTour
from .chat_service import TourRecommendationService


@api_view(['POST'])
@permission_classes([AllowAny])
def user_registration(request):
    """
    Register a new user with comprehensive profile information
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    import re
    
    User = get_user_model()
    
    try:
        # Extract data from request
        data = request.data
        
        # Required fields
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Optional fields
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        country = data.get('country', '').strip()
        postal_code = data.get('postal_code', '').strip()
        date_of_birth = data.get('date_of_birth', '')
        bio = data.get('bio', '').strip()
        newsletter_subscription = data.get('newsletter_subscription', True)
        
        # Validation
        if not all([username, email, password, first_name, last_name]):
            return Response({
                'error': 'Username, email, password, first name, and last name are required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return Response({
                'error': 'Username already exists',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email already exists',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return Response({
                'error': 'Invalid email format',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({
                'error': f'Password validation failed: {", ".join(e.messages)}',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='normal',
            phone=phone,
            address=address,
            city=city,
            country=country,
            postal_code=postal_code,
            bio=bio,
            newsletter_subscription=newsletter_subscription
        )
        
        # Handle date_of_birth if provided
        if date_of_birth:
            try:
                from datetime import datetime
                user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                user.save()
            except ValueError:
                # Invalid date format - just skip it
                pass
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        
        return Response({
            'message': 'User registered successfully',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data,
            'success': True
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'Registration failed. Please try again.',
            'success': False,
            'debug_error': str(e) if hasattr(request, 'user') and request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def sign_in(request):
    serializer = SignInSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_dashboard_access(request):
    user = request.user
    
    if user.user_type != 'agent':
        return Response(
            {'error': 'Access denied. Only tour agents can access the dashboard.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    return Response({
        'message': 'Welcome to the agent dashboard!',
        'user': UserSerializer(user).data,
        'dashboard_access': True
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    
    if request.method == 'GET':
        return Response({
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        try:
            # Get data from request
            data = request.data
            
            # Update user fields
            if 'first_name' in data:
                user.first_name = data['first_name'].strip()
            if 'last_name' in data:
                user.last_name = data['last_name'].strip()
            if 'email' in data:
                email = data['email'].strip()
                # Check if email is already taken by another user
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    return Response({
                        'error': 'Email already exists',
                        'success': False
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.email = email
            
            # Update contact fields
            if 'phone' in data:
                user.phone = data['phone'].strip()
            if 'address' in data:
                user.address = data['address'].strip()
            if 'city' in data:
                user.city = data['city'].strip()
            if 'country' in data:
                user.country = data['country'].strip()
            if 'postal_code' in data:
                user.postal_code = data['postal_code'].strip()
            
            # Update additional fields
            if 'date_of_birth' in data and data['date_of_birth']:
                try:
                    from datetime import datetime
                    user.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                except ValueError:
                    return Response({
                        'error': 'Invalid date format. Use YYYY-MM-DD',
                        'success': False
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif 'date_of_birth' in data and not data['date_of_birth']:
                user.date_of_birth = None
            
            if 'bio' in data:
                user.bio = data['bio'].strip()
            if 'newsletter_subscription' in data:
                user.newsletter_subscription = bool(data['newsletter_subscription'])
            
            # Save user
            user.save()
            
            return Response({
                'message': 'Profile updated successfully',
                'user': UserSerializer(user).data,
                'success': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Failed to update profile. Please try again.',
                'success': False,
                'debug_error': str(e) if hasattr(request, 'user') and request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TourPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        print(f"DEBUG: Pagination - Total count: {self.page.paginator.count}, Current page: {self.page.number}, Page size: {self.page.paginator.per_page}")
        print(f"DEBUG: Pagination - Items on this page: {len(data)}")
        return super().get_paginated_response(data)


class AgentTourPermission:
    """Custom permission class to ensure only agents can create/manage tours"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'agent'


class TourListCreateView(generics.ListCreateAPIView):
    pagination_class = TourPagination
    
    def get_permissions(self):
        """
        Allow anyone to view tours (GET), but require authentication to create (POST)
        """
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TourCreateSerializer
        return TourSerializer
    
    def get_queryset(self):
        user = self.request.user
        print(f"DEBUG: get_queryset called for user: {user} (authenticated: {user.is_authenticated}, type: {getattr(user, 'user_type', 'anonymous')})")
        
        # Base queryset - Everyone can see all active tours on the Discover page
        queryset = Tour.objects.filter(is_active=True)
        print(f"DEBUG: Base active tours count (everyone sees all): {queryset.count()}")
        
        # Apply search and filters
        search = self.request.query_params.get('search', '').strip()
        destination = self.request.query_params.get('destination', '').strip()
        date_from = self.request.query_params.get('date_from', '').strip()
        date_to = self.request.query_params.get('date_to', '').strip()
        min_price = self.request.query_params.get('min_price', '').strip()
        max_price = self.request.query_params.get('max_price', '').strip()
        visa_required = self.request.query_params.get('visa_required', '').strip()
        meal_plan = self.request.query_params.get('meal_plan', '').strip()
        flight_type = self.request.query_params.get('flight_type', '').strip()
        
        print(f"DEBUG: Query parameters - search: '{search}', destination: '{destination}', min_price: '{min_price}', max_price: '{max_price}', visa_required: '{visa_required}', meal_plan: '{meal_plan}', flight_type: '{flight_type}'")
        
        # Keyword search across title, description, and destination
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(destination__icontains=search) |
                Q(hotel_name__icontains=search)
            )
            print(f"DEBUG: After search filter: {queryset.count()} tours")
        
        # Filter by destination
        if destination:
            queryset = queryset.filter(destination__iexact=destination)
            print(f"DEBUG: After destination filter: {queryset.count()} tours")
        
        # Filter by date range
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__gte=date_from_obj)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(end_date__lte=date_to_obj)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        # Filter by price range
        if min_price:
            try:
                min_price_decimal = float(min_price)
                queryset = queryset.filter(price__gte=min_price_decimal)
                print(f"DEBUG: After min_price filter: {queryset.count()} tours")
            except ValueError:
                pass  # Invalid price format, ignore filter
        
        if max_price:
            try:
                max_price_decimal = float(max_price)
                queryset = queryset.filter(price__lte=max_price_decimal)
                print(f"DEBUG: After max_price filter: {queryset.count()} tours")
            except ValueError:
                pass  # Invalid price format, ignore filter
        
        # Filter by visa required
        if visa_required and visa_required.lower() == 'true':
            queryset = queryset.filter(visa_required=True)
            print(f"DEBUG: After visa_required filter: {queryset.count()} tours")
        
        # Filter by meal plan
        if meal_plan:
            queryset = queryset.filter(meal_plan=meal_plan)
            print(f"DEBUG: After meal_plan filter: {queryset.count()} tours")
        
        # Filter by flight type
        if flight_type:
            queryset = queryset.filter(flight_type=flight_type)
            print(f"DEBUG: After flight_type filter: {queryset.count()} tours")
        
        final_queryset = queryset.order_by('-created_at')
        print(f"DEBUG: Final queryset count (after all filters): {final_queryset.count()} tours")
        return final_queryset
    
    def perform_create(self, serializer):
        # Only agents can create tours
        if self.request.user.user_type != 'agent':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only tour agents can create tours.")
        
        serializer.save(agent=self.request.user)


class TourDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TourSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'agent':
            # Agents can access their own tours (including inactive for editing)
            return Tour.objects.filter(agent=user)
        else:
            # Regular users can view all active tours
            return Tour.objects.filter(is_active=True)
    
    def perform_update(self, serializer):
        # Only the tour's agent can update it
        if self.get_object().agent != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own tours.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only the tour's agent can delete it
        if instance.agent != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own tours.")
        
        # Soft delete by setting is_active to False
        instance.is_active = False
        instance.save()


@api_view(['GET'])
@permission_classes([AllowAny])
def get_tour_companies(request):
    """
    Get all tour companies with their agent and tour information
    """
    from django.contrib.auth import get_user_model
    from .models import TourCompany
    User = get_user_model()
    
    try:
        companies = TourCompany.objects.all()
        companies_data = []
        
        for company in companies:
            # Get all agents for this company
            agents = User.objects.filter(user_type='agent', tour_company=company)
            
            # Calculate total tours for this company
            total_tours = 0
            agent_names = []
            for agent in agents:
                total_tours += agent.tours.filter(is_active=True).count()
                agent_names.append(agent.get_full_name() or agent.username)
            
            company_info = {
                'id': company.id,
                'name': company.name,
                'address': company.address,
                'phone': company.phone,
                'email': company.email,
                'website': company.website,
                'agent_count': agents.count(),
                'agent_names': agent_names,
                'total_tours': total_tours,
                'created_date': company.created_at.strftime('%Y-%m-%d') if hasattr(company, 'created_at') else None
            }
            companies_data.append(company_info)
        
        # Also include independent agents (those without companies)
        independent_agents = User.objects.filter(user_type='agent', tour_company__isnull=True)
        if independent_agents.exists():
            independent_agent_names = []
            independent_total_tours = 0
            
            for agent in independent_agents:
                independent_agent_names.append(agent.get_full_name() or agent.username)
                independent_total_tours += agent.tours.filter(is_active=True).count()
            
            companies_data.append({
                'id': 'independent',
                'name': 'Independent Agents',
                'address': None,
                'phone': None,
                'email': None,
                'website': None,
                'agent_count': independent_agents.count(),
                'agent_names': independent_agent_names,
                'total_tours': independent_total_tours,
                'created_date': None
            })
        
        return Response({
            'companies': companies_data,
            'total_count': len(companies_data),
            'success': True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch tour companies',
            'success': False,
            'debug_error': str(e) if hasattr(request, 'user') and request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_company_tours(request, company_id):
    """
    Get all tours for a specific company
    """
    from django.contrib.auth import get_user_model
    from .models import TourCompany
    User = get_user_model()
    
    try:
        if company_id == 'independent':
            # Handle independent agents
            independent_agents = User.objects.filter(user_type='agent', tour_company__isnull=True)
            tours = Tour.objects.filter(agent__in=independent_agents, is_active=True).select_related('agent')
            company_info = {
                'id': 'independent',
                'name': 'Independent Agents',
                'address': None,
                'phone': None,
                'email': None,
                'website': None,
                'agent_count': independent_agents.count(),
                'agent_names': [agent.get_full_name() or agent.username for agent in independent_agents]
            }
        else:
            # Handle regular companies
            try:
                company = TourCompany.objects.get(id=company_id)
            except TourCompany.DoesNotExist:
                return Response({
                    'error': 'Company not found',
                    'success': False
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get all agents for this company
            agents = User.objects.filter(user_type='agent', tour_company=company)
            tours = Tour.objects.filter(agent__in=agents, is_active=True).select_related('agent')
            
            company_info = {
                'id': company.id,
                'name': company.name,
                'address': company.address,
                'phone': company.phone,
                'email': company.email,
                'website': company.website,
                'agent_count': agents.count(),
                'agent_names': [agent.get_full_name() or agent.username for agent in agents]
            }
        
        # Serialize tours
        tours_data = []
        for tour in tours:
            tours_data.append({
                'id': tour.id,
                'title': tour.title,
                'description': tour.description,
                'destination': tour.destination,
                'hotel_name': tour.hotel_name,
                'price': float(tour.price),
                'formatted_price': tour.formatted_price,
                'start_date': tour.start_date.strftime('%Y-%m-%d'),
                'end_date': tour.end_date.strftime('%Y-%m-%d'),
                'visa_required': tour.visa_required,
                'meal_plan': tour.get_meal_plan_display(),
                'flight_type': tour.get_flight_type_display(),
                'agent_name': tour.agent.get_full_name() or tour.agent.username,
            })
        
        return Response({
            'company': company_info,
            'tours': tours_data,
            'tour_count': len(tours_data),
            'success': True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch company tours',
            'success': False,
            'debug_error': str(e) if hasattr(request, 'user') and request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_unique_destinations(request):
    """
    Get all unique tour destinations for filter dropdown
    """
    try:
        destinations = Tour.objects.filter(is_active=True).values_list('destination', flat=True).distinct().order_by('destination')
        destinations_list = [dest for dest in destinations if dest and dest.strip()]
        
        return Response({
            'destinations': destinations_list,
            'count': len(destinations_list),
            'success': True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch destinations',
            'success': False,
            'debug_error': str(e) if hasattr(request, 'user') and request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    """
    Get user's conversation history
    """
    conversations = Conversation.objects.filter(user=request.user, is_active=True)
    serializer = ConversationListSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """
    Get or delete a specific conversation
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        conversation.delete()
        return Response({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_recommended_tours(request, message_id):
    """
    Get recommended tours for a specific chat message
    """
    try:
        # Get the chat message and verify it belongs to the user's conversation
        message = ChatMessage.objects.select_related('conversation').prefetch_related('recommended_tours').get(
            id=message_id,
            conversation__user=request.user
        )
        
        # Get the recommended tours for this message
        recommended_tours = message.recommended_tours.all()
        
        # Serialize the tours
        tours_data = []
        for tour in recommended_tours:
            tours_data.append({
                'id': tour.id,
                'title': tour.title,
                'description': tour.description,
                'destination': tour.destination,
                'hotel_name': tour.hotel_name,
                'price': float(tour.price),
                'formatted_price': tour.formatted_price,
                'start_date': tour.start_date.isoformat(),
                'end_date': tour.end_date.isoformat(),
                'visa_required': tour.visa_required,
                'meal_plan': tour.meal_plan,
                'flight_type': tour.flight_type,
                'agent_name': tour.agent.get_full_name() or tour.agent.username,
                'company_name': tour.agent.tour_company.name if tour.agent.tour_company else 'Independent Agent'
            })
        
        return Response(tours_data)
        
    except ChatMessage.DoesNotExist:
        return Response({
            'error': 'Chat message not found or you do not have permission to access it'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'An error occurred while fetching recommended tours',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_with_ai(request):
    """
    Chat endpoint for users to get tour recommendations based on their preferences.
    Supports memory for logged-in users.
    """
    user_message = request.data.get('message', '').strip()
    conversation_id = request.data.get('conversation_id', None)
    
    if not user_message:
        return Response({
            'error': 'Message is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Initialize the recommendation service
        recommendation_service = TourRecommendationService()
        
        # Handle conversation context for authenticated users
        conversation = None
        chat_history = []
        
        if request.user.is_authenticated:
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user)
                    # Get recent messages for context (last 10 messages) with recommended tours
                    recent_messages = conversation.messages.prefetch_related('recommended_tours').all()[:10]
                    chat_history = []
                    
                    for msg in recent_messages:
                        if msg.sender == 'user':
                            chat_history.append(f"User: {msg.content}")
                        else:
                            # Include only AI response without tour context
                            chat_history.append(f"Assistant: {msg.content}")
                            
                except Conversation.DoesNotExist:
                    pass
            
            # Create new conversation if none exists
            if not conversation:
                conversation = Conversation.objects.create(user=request.user)
            
            # Save user message
            user_chat_message = ChatMessage.objects.create(
                conversation=conversation,
                content=user_message,
                sender='user'
            )
        
        # Get recommendation from LLM with chat history context
        if chat_history:
            print(f"Chat history context ({len(chat_history)} messages):")
            for i, msg in enumerate(chat_history):
                print(f"  {i+1}. {msg[:100]}...")
        
        result = recommendation_service.recommend_tours(user_message, chat_history=chat_history, conversation=conversation)
        
        # Save AI response and recommended tours for authenticated users
        ai_message = None
        if request.user.is_authenticated and conversation:
            ai_message = ChatMessage.objects.create(
                conversation=conversation,
                content=result['response'],
                sender='ai'
            )
            
            # Associate recommended tours with the AI message
            if result['recommended_tours']:
                tour_ids = [tour['id'] for tour in result['recommended_tours']]
                tours = Tour.objects.filter(id__in=tour_ids)
                ai_message.recommended_tours.set(tours)
            
            # Update conversation title if it's the first exchange
            if not conversation.title and conversation.messages.count() >= 2:
                conversation.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
                conversation.save()
        
        response_data = {
            'response': result['response'],
            'recommended_tours': result['recommended_tours'],
            'success': True
        }
        
        # Add conversation info for authenticated users
        if request.user.is_authenticated and conversation:
            response_data['conversation_id'] = conversation.id
            response_data['conversation_title'] = conversation.title
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Something went wrong while processing your request. Please try again.',
            'success': False,
            'debug_error': str(e) if hasattr(request, 'user') and request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def saved_tours_list(request):
    """
    List user's saved tours or save a new tour
    """
    if request.method == 'GET':
        saved_tours = SavedTour.objects.filter(user=request.user).select_related('tour', 'tour__agent')
        serializer = SavedTourSerializer(saved_tours, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = SavedTourSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Handle duplicate save attempts
                if 'unique_together' in str(e).lower():
                    return Response({
                        'error': 'Tour is already saved'
                    }, status=status.HTTP_400_BAD_REQUEST)
                raise e
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unsave_tour(request, tour_id):
    """
    Remove a tour from user's saved tours
    """
    try:
        saved_tour = SavedTour.objects.get(user=request.user, tour_id=tour_id)
        saved_tour.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
    except SavedTour.DoesNotExist:
        return Response({
            'error': 'Tour not found in saved tours'
        }, status=status.HTTP_404_NOT_FOUND)
