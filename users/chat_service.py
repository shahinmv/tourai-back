import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from .models import Tour
from django.db.models import Q
from decimal import Decimal
import json
from typing import List, Dict, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Define tools outside the class so they can be used by the agent
@tool
def search_tours_by_destination(destination: str) -> List[Dict]:
    """Search for tours by destination. Use this when users mention specific countries, cities, or regions."""
    print(f"🔍 TOOL CALLED: search_tours_by_destination")
    print(f"   Parameters: destination='{destination}'")
    
    try:
        tours = Tour.objects.filter(is_active=True, destination__icontains=destination)
        result = _serialize_tours_for_llm(tours)
        print(f"   Results: Found {len(result)} tours for destination '{destination}'")
        for tour in result:
            print(f"     - {tour['title']} ({tour['destination']})")
        return result
    except Exception as e:
        print(f"   Error: {str(e)}")
        return []

@tool  
def search_tours_by_price_range(min_price: float = 0, max_price: float = 10000) -> List[Dict]:
    """Search for tours within a specific price range. Use for budget or luxury requests."""
    print(f"💰 TOOL CALLED: search_tours_by_price_range")
    print(f"   Parameters: min_price=${min_price}, max_price=${max_price}")
    
    try:
        tours = Tour.objects.filter(is_active=True, price__gte=min_price, price__lte=max_price).order_by('price')
        result = _serialize_tours_for_llm(tours)
        print(f"   Results: Found {len(result)} tours in price range ${min_price}-${max_price}")
        for tour in result:
            print(f"     - {tour['title']} ({tour['destination']})")
        return result
    except Exception as e:
        print(f"   Error: {str(e)}")
        return []

@tool
def search_tours_by_keyword(keyword: str) -> List[Dict]:
    """Search tours by keywords in title or description. Use for activity types like 'adventure', 'cultural', 'safari', etc."""
    print(f"🔎 TOOL CALLED: search_tours_by_keyword")
    print(f"   Parameters: keyword='{keyword}'")
    
    try:
        tours = Tour.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword)
        )
        result = _serialize_tours_for_llm(tours)
        print(f"   Results: Found {len(result)} tours matching keyword '{keyword}'")
        for tour in result:
            print(f"     - {tour['title']} ({tour['destination']})")
        return result
    except Exception as e:
        print(f"   Error: {str(e)}")
        return []

@tool
def get_all_available_destinations() -> List[str]:
    """Get a list of all available tour destinations. Use this to help users discover options."""
    print(f"🌍 TOOL CALLED: get_all_available_destinations")
    print(f"   Parameters: None")
    
    try:
        destinations = Tour.objects.filter(is_active=True).values_list('destination', flat=True).distinct()
        result = list(destinations)
        print(f"   Results: Found {len(result)} unique destinations")
        print(f"     - Destinations: {', '.join(result)}")
        return result
    except Exception as e:
        print(f"   Error: {str(e)}")
        return []

@tool
def search_tours_by_visa_requirement(visa_required: bool) -> List[Dict]:
    """Search for tours based on visa requirements. Use when users ask about destinations that require visa or visa-free travel."""
    print(f"📋 TOOL CALLED: search_tours_by_visa_requirement")
    print(f"   Parameters: visa_required={visa_required}")
    
    try:
        tours = Tour.objects.filter(is_active=True, visa_required=visa_required).order_by('destination')
        result = _serialize_tours_for_llm(tours)
        visa_status = "require visa" if visa_required else "are visa-free"
        print(f"   Results: Found {len(result)} tours that {visa_status}")
        for tour in result:
            print(f"     - {tour['title']} ({tour['destination']})")
        return result
    except Exception as e:
        print(f"   Error: {str(e)}")
        return []

@tool
def search_tours_by_date_range(start_date: str, end_date: str = None) -> List[Dict]:
    """Search for tours within a specific date range. Use when users mention specific dates, months, or travel periods.
    Format dates as YYYY-MM-DD. If end_date is not provided, searches for tours starting from start_date onwards."""
    print(f"📅 TOOL CALLED: search_tours_by_date_range")
    print(f"   Parameters: start_date='{start_date}', end_date='{end_date}'")
    
    try:
        from datetime import datetime
        
        # Parse start_date
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        # Build the query
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            tours = Tour.objects.filter(
                is_active=True,
                start_date__gte=start_date_obj,
                start_date__lte=end_date_obj
            ).order_by('start_date')
            date_range_desc = f"between {start_date} and {end_date}"
        else:
            tours = Tour.objects.filter(
                is_active=True,
                start_date__gte=start_date_obj
            ).order_by('start_date')
            date_range_desc = f"starting from {start_date}"
        
        result = _serialize_tours_for_llm(tours)
        print(f"   Results: Found {len(result)} tours {date_range_desc}")
        for tour in result:
            print(f"     - {tour['title']} ({tour['destination']})")
        return result
    except Exception as e:
        print(f"   Error: {str(e)}")
        return []

@tool
def search_tours_by_meal_plan(meal_plan: str) -> List[Dict]:
    """Search for tours by meal plan. Use when users mention meal preferences.
    Valid meal plans: 'room_only', 'bed_breakfast', 'half_board', 'full_board', 'all_inclusive'"""
    print(f"🍽️ TOOL CALLED: search_tours_by_meal_plan")
    print(f"   Parameters: meal_plan='{meal_plan}'")
    
    try:
        # Map common user terms to database values
        meal_plan_mapping = {
            'room only': 'room_only',
            'bed and breakfast': 'bed_breakfast',
            'breakfast': 'bed_breakfast',
            'half board': 'half_board',
            'full board': 'full_board',
            'all inclusive': 'all_inclusive',
            'all-inclusive': 'all_inclusive'
        }
        
        # Normalize the meal plan input
        meal_plan_normalized = meal_plan_mapping.get(meal_plan.lower(), meal_plan.lower())
        
        tours = Tour.objects.filter(is_active=True, meal_plan=meal_plan_normalized).order_by('destination')
        result = _serialize_tours_for_llm(tours)
        
        print(f"   Results: Found {len(result)} tours with {meal_plan} meal plan")
        for tour in result:
            print(f"     - {tour['title']} ({tour['destination']})")
        return result
    except Exception as e:
        print(f"   Error: {str(e)}")
        return []

def _serialize_tours_for_llm(tours) -> List[Dict]:
    """Serialize tour objects with minimal data for LLM - prevents detailed responses"""
    tours_data = []
    for tour in tours[:5]:  # Limit to 5 tours to save tokens
        tours_data.append({
            'id': tour.id,
            'title': tour.title,
            'destination': tour.destination,
            # 'hotel': tour.hotel_name,
            # 'start_date': tour.start_date,
            # 'end_date': tour.end_date,
            # 'meal_plan': tour.meal_plan,
            # 'flight_type': tour.flight_type,
            # 'price': tour.price,
            # Only basic info - no detailed data that LLM might include in response
        })
    return tours_data

def _serialize_tours_for_frontend(tours) -> List[Dict]:
    """Serialize tour objects with full details for frontend display"""
    tours_data = []
    for tour in tours[:5]:  # Limit to 5 tours to save tokens
        tours_data.append({
            'id': tour.id,
            'title': tour.title,
            'description': tour.description[:200] + '...' if len(tour.description) > 200 else tour.description,
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
            'company_name': tour.agent.tour_company.name if tour.agent.tour_company else None
        })
    return tours_data

class TourRecommendationService:
    def __init__(self):
        # Initialize the LLM
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key="REMOVED_SECRET"
            )
            
            # Define tools
            self.tools = [
                search_tours_by_destination,
                search_tours_by_price_range, 
                search_tours_by_keyword,
                get_all_available_destinations,
                search_tours_by_visa_requirement,
                search_tours_by_date_range,
                search_tours_by_meal_plan
            ]
            
            # Create agent
            system_prompt = """You are TourAI, a friendly travel assistant helping users find perfect tour packages.

IMPORTANT CONVERSATION RULES:
1. For greetings like "Hi", "Hello", "Good morning" - respond conversationally WITHOUT searching for tours
2. ALWAYS search for tours when users mention travel interests, activities, or destinations
3. Be helpful by finding actual tour options, don't just give general advice
4. Keep responses conversational and helpful

MANDATORY TOOL USAGE RULES:
- Use search_tours_by_destination for ANY location mentioned (e.g., "Japan", "Europe", "Thailand")  
- Use search_tours_by_price_range for ANY budget mentioned ("luxury", "budget", "cheap", "expensive", "under $X", "over $X")
- Use search_tours_by_keyword for ANY activity mentioned ("adventure", "cultural", "safari", "beach", "wildlife", "hiking", "romantic")
- Use search_tours_by_visa_requirement when users ask about visa requirements ("visa-free", "no visa required", "visa required")
- Use search_tours_by_date_range when users mention specific dates or travel periods ("in March", "next summer", "2024-05-15")
- Use search_tours_by_meal_plan when users mention meal preferences ("all inclusive", "breakfast included", "full board", "half board")
- Use get_all_available_destinations when users ask about available options
- Always search for tours when users mention specific travel requests

RESPONSE FORMAT:
- Be enthusiastic and conversational when finding new tours
- Answer user questions helpfully and naturally
- Keep all responses brief and natural
- Tour details will be shown separately in visual cards

EXAMPLE RESPONSES:
"Excellent! I found some fantastic adventure tours that would be perfect for you!"
"Great! I discovered some amazing cultural tours in Japan that would be perfect!"

The system will automatically display tour details in cards - you focus on conversation!"""

            try:
                # Try to get the prompt from hub, fallback if not available
                prompt = hub.pull("hwchase17/openai-functions-agent")
                prompt.messages[0].prompt.template = system_prompt
            except:
                # Create a simple prompt if hub is not available
                from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history", optional=True),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad")
                ])

            # Create agent
            agent = create_openai_functions_agent(self.llm, self.tools, prompt)
            self.agent_executor = AgentExecutor(
                agent=agent, 
                tools=self.tools, 
                verbose=False,
                return_intermediate_steps=True
            )
            self.use_mock = False
            
        except Exception as e:
            print(f"OpenAI initialization failed: {e}")
            self.use_mock = True
    
    def get_all_tours_data(self):
        """Get all active tours data for mock responses"""
        tours = Tour.objects.filter(is_active=True)
        return _serialize_tours_for_llm(tours)
    
    def _get_mock_response(self, user_query, tours_data, chat_history=None):
        """Provide a mock response when OpenAI is not available"""
        query_lower = user_query.lower().strip()
        
        # Simple chat history awareness without tour context parsing
        if chat_history:
            # Check if user is asking follow-up questions
            if any(keyword in query_lower for keyword in ['visa', 'hotel', 'price', 'cost', 'meal', 'flight', 'date', 'when']):
                # Generic response for tour detail questions  
                return {
                    'response': "I can help you with tour details! Could you tell me which destination or type of tour you're interested in so I can find the best options for you?",
                    'recommended_tours': []
                }
        
        # Handle greetings without recommending tours
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you']
        if any(greeting == query_lower or query_lower.startswith(greeting + ' ') for greeting in greetings):
            return {
                'response': "Hello! I'm your AI travel assistant. I can help you find amazing tour packages based on your preferences. Tell me what kind of experience you're looking for - adventure, relaxation, cultural exploration, or a specific destination you have in mind!",
                'recommended_tours': []
            }
        
        # Handle general conversation without specific travel intent
        general_phrases = ['thanks', 'thank you', 'ok', 'okay', 'yes', 'no', 'maybe']
        if query_lower in general_phrases:
            return {
                'response': "You're welcome! Feel free to ask me about any destinations or types of tours you're interested in. I can help you find the perfect travel experience!",
                'recommended_tours': []
            }
        
        # Simple keyword matching for travel-related queries
        matching_tour_ids = []
        
        # Match based on destinations mentioned
        if 'japan' in query_lower or 'tokyo' in query_lower:
            matching_tour_ids = [t['id'] for t in tours_data if 'Japan' in t['destination']][:2]
        elif 'thailand' in query_lower or 'asia' in query_lower:
            matching_tour_ids = [t['id'] for t in tours_data if any(country in t['destination'] for country in ['Thailand', 'Japan', 'Indonesia'])][:2]
        elif 'europe' in query_lower or 'switzerland' in query_lower:
            matching_tour_ids = [t['id'] for t in tours_data if any(country in t['destination'] for country in ['Switzerland', 'Greece', 'Norway', 'Iceland'])][:2]
        elif 'adventure' in query_lower or 'hiking' in query_lower:
            matching_tour_ids = [t['id'] for t in tours_data if any(word in t['title'].lower() for word in ['adventure', 'trek', 'hiking', 'wilderness'])][:2]
        elif 'luxury' in query_lower or 'expensive' in query_lower:
            # Get luxury price range tours (>$2500) - need to fetch from DB
            from .models import Tour
            luxury_tour_objects = Tour.objects.filter(is_active=True, price__gte=2500)[:2]
            matching_tour_ids = [t.id for t in luxury_tour_objects]
        elif 'budget' in query_lower or 'cheap' in query_lower:
            # Get budget price range tours (<$1000) - need to fetch from DB  
            from .models import Tour
            budget_tour_objects = Tour.objects.filter(is_active=True, price__lt=1000)[:2]
            matching_tour_ids = [t.id for t in budget_tour_objects]
        elif any(keyword in query_lower for keyword in ['tour', 'travel', 'vacation', 'trip', 'destination', 'where', 'visit']):
            # Only recommend tours if user mentions travel-related keywords
            matching_tour_ids = [t['id'] for t in tours_data[:2]]
        else:
            # For unclear queries, ask for clarification without recommending tours
            return {
                'response': "I'd love to help you find the perfect tour! Could you tell me more about what you're looking for? For example, your preferred destination, budget range, or type of activities you enjoy?",
                'recommended_tours': []
            }
        
        # Convert tour IDs to full tour data for frontend
        recommended_tours = []
        if matching_tour_ids:
            from .models import Tour
            tours = Tour.objects.filter(id__in=matching_tour_ids, is_active=True)
            recommended_tours = _serialize_tours_for_frontend(tours)
        
        # Generate response based on matches
        if recommended_tours:
            if 'japan' in query_lower or 'tokyo' in query_lower:
                response = "Great! I found some amazing tours in Japan that offer incredible cultural experiences!"
            elif 'thailand' in query_lower or 'asia' in query_lower:
                response = "Excellent! I discovered some fantastic tours in Asia that would be perfect for you!"
            elif 'europe' in query_lower or 'switzerland' in query_lower:
                response = "Perfect! I found some wonderful European tours with stunning alpine experiences!"
            elif 'adventure' in query_lower or 'hiking' in query_lower:
                response = "Amazing! I found some thrilling adventure tours that will get your adrenaline pumping!"
            elif 'luxury' in query_lower or 'expensive' in query_lower:
                response = "Fantastic! I found some luxurious tours with premium accommodations and experiences!"
            elif 'budget' in query_lower or 'cheap' in query_lower:
                response = "Great news! I found some excellent budget-friendly tours that offer amazing value!"
            else:
                response = "Perfect! I found some wonderful tour options that match what you're looking for!"
        else:
            response = "I'd love to help you find the perfect tour! Could you tell me more about what you're looking for? For example, your preferred destination, budget range, or type of activities you enjoy?"
        
        return {
            'response': response,
            'recommended_tours': recommended_tours
        }


    def recommend_tours(self, user_query, chat_history=None):
        """Use agent with tools to analyze user query and recommend suitable tours"""
        print(f"\n🤖 NEW CHAT REQUEST")
        print(f"   User Query: '{user_query}'")
        print(f"   Chat History: {len(chat_history) if chat_history else 0} previous messages")
        print(f"   Using Mock Response: {self.use_mock}")
        
        # Use mock response if OpenAI is not available
        if self.use_mock:
            print(f"   → Using mock response system")
            tours_data = self.get_all_tours_data()
            return self._get_mock_response(user_query, tours_data, chat_history)
        
        try:
            print(f"   → Using LangChain agent with tools")
            # Prepare input with chat history if available
            agent_input = {"input": user_query}
            if chat_history:
                # Convert chat history to proper format for the agent
                from langchain.schema import HumanMessage, AIMessage
                chat_messages = []
                for msg in chat_history:
                    if msg.startswith("User:"):
                        chat_messages.append(HumanMessage(content=msg[5:].strip()))
                    elif msg.startswith("Assistant:"):
                        chat_messages.append(AIMessage(content=msg[10:].strip()))
                agent_input["chat_history"] = chat_messages
            
            # Use the agent to process the query
            result = self.agent_executor.invoke(agent_input)
            response_text = result["output"]
            
            # Extract recommended tours from the agent's tool calls
            recommended_tours = self._extract_tours_from_agent_response(result)
            
            print(f"   → Agent completed. Response length: {len(response_text)} chars")
            print(f"   → Extracted {len(recommended_tours)} tours from tool results")
            
            return {
                'response': response_text,
                'recommended_tours': recommended_tours
            }
            
        except Exception as e:
            print(f"   ❌ Agent error: {e}")
            print(f"   → Falling back to mock response")
            # Fallback to mock response if agent fails
            tours_data = self.get_all_tours_data()
            return self._get_mock_response(user_query, tours_data, chat_history)
    
    def _extract_tours_from_agent_response(self, agent_result):
        """Extract tour IDs from agent's intermediate steps and return full tour data for frontend"""
        tour_ids = []
        
        # Look through the agent's intermediate steps for tool outputs
        if 'intermediate_steps' in agent_result:
            for step in agent_result['intermediate_steps']:
                if len(step) > 1:
                    tool_output = step[1]  # Tool output is the second element
                    if isinstance(tool_output, list) and tool_output:
                        # Extract tour IDs from minimal LLM data
                        for tour_data in tool_output:
                            if isinstance(tour_data, dict) and 'id' in tour_data:
                                tour_ids.append(tour_data['id'])
        
        # Remove duplicates and limit to 5 tours
        unique_tour_ids = list(dict.fromkeys(tour_ids))[:5]
        
        # Get full tour objects and serialize for frontend
        if unique_tour_ids:
            from .models import Tour
            tours = Tour.objects.filter(id__in=unique_tour_ids, is_active=True)
            return _serialize_tours_for_frontend(tours)
        
        return []
    
    def _extract_recommended_tours(self, llm_response, tours_data):
        """Extract tour IDs mentioned in the LLM response"""
        recommended_tours = []
        
        # Simple approach: look for tour titles mentioned in the response
        for tour in tours_data:
            if tour['title'].lower() in llm_response.lower():
                recommended_tours.append(tour)
        
        # If no tours found by title, try to find tours mentioned by destination
        if not recommended_tours:
            for tour in tours_data:
                if tour['destination'].lower() in llm_response.lower():
                    recommended_tours.append(tour)
                    if len(recommended_tours) >= 3:  # Limit to 3 recommendations
                        break
        
        return recommended_tours[:3]  # Return max 3 recommendations