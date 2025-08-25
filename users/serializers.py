from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Tour, TourCompany, Conversation, ChatMessage, SavedTour


class TourCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = TourCompany
        fields = ('id', 'name', 'description', 'email', 'phone', 'website')


class UserSerializer(serializers.ModelSerializer):
    tour_company = TourCompanySerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'tour_company', 'phone', 'address', 'city', 'country', 
            'postal_code', 'date_of_birth', 'profile_picture', 'bio', 
            'preferred_currency', 'newsletter_subscription', 'date_joined',
            'profile_updated_at'
        )
        extra_kwargs = {
            'email': {'required': False}
        }
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
                
                if user:
                    if user.is_active:
                        data['user'] = user
                        return data
                    else:
                        raise serializers.ValidationError('User account is disabled.')
                else:
                    raise serializers.ValidationError('Invalid credentials.')
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must provide email and password.')


class TourSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)
    formatted_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Tour
        fields = [
            'id', 'agent', 'title', 'description', 'destination', 'hotel_name',
            'price', 'formatted_price', 
            'start_date', 'end_date', 'visa_required', 'meal_plan', 'flight_type', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'agent', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set the agent to the current user
        validated_data['agent'] = self.context['request'].user
        return super().create(validated_data)


class TourCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tour
        fields = [
            'title', 'description', 'destination', 'hotel_name', 
            'price', 'start_date', 'end_date', 'visa_required', 'meal_plan', 'flight_type'
        ]

    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data


class ChatMessageSerializer(serializers.ModelSerializer):
    recommended_tours = TourSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'content', 'sender', 'recommended_tours', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active', 'messages', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count', 'last_message']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content[:100] + ('...' if len(last_msg.content) > 100 else ''),
                'sender': last_msg.sender,
                'created_at': last_msg.created_at
            }
        return None


class SavedTourSerializer(serializers.ModelSerializer):
    tour = TourSerializer(read_only=True)
    tour_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = SavedTour
        fields = ['id', 'tour', 'tour_id', 'saved_at']
        read_only_fields = ['id', 'saved_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)