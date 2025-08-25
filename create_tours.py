#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/Users/shahinmammadov/Desktop/JLTECH/tourai/tourai_back')

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourai_back.settings')
django.setup()

from users.models import User, Tour
from decimal import Decimal
from datetime import date

# Get the first agent user
agent = User.objects.filter(user_type='agent').first()
if not agent:
    print('No agent found')
    exit()

print(f'Creating tours for agent: {agent.username}')

# Define tour data
tours = [
    {
        'title': 'Bali Paradise Escape',
        'description': 'Experience the magical beauty of Bali with pristine beaches, ancient temples, and lush rice terraces. Perfect for relaxation and cultural exploration.',
        'destination': 'Bali, Indonesia',
        'hotel_name': 'Grand Hyatt Bali',
        'price': Decimal('2899.00'),
        'start_date': date(2024, 12, 15),
        'end_date': date(2024, 12, 22),
        'visa_required': False,
        'meal_plan': 'half_board',
        'flight_type': 'direct'
    },
    {
        'title': 'Swiss Alps Adventure',
        'description': 'Breathtaking mountain views, world-class skiing, and charming alpine villages await you in the heart of Switzerland.',
        'destination': 'Zermatt, Switzerland',
        'hotel_name': 'The Omnia',
        'price': Decimal('4299.00'),
        'start_date': date(2025, 1, 10),
        'end_date': date(2025, 1, 17),
        'visa_required': False,
        'meal_plan': 'bed_breakfast',
        'flight_type': 'layover'
    },
    {
        'title': 'Tokyo Cultural Journey',
        'description': 'Immerse yourself in the perfect blend of traditional culture and modern innovation in Japan\'s vibrant capital city.',
        'destination': 'Tokyo, Japan',
        'hotel_name': 'Park Hyatt Tokyo',
        'price': Decimal('3599.00'),
        'start_date': date(2025, 2, 5),
        'end_date': date(2025, 2, 12),
        'visa_required': True,
        'meal_plan': 'room_only',
        'flight_type': 'direct'
    },
    {
        'title': 'Santorini Sunset Romance',
        'description': 'Fall in love with the stunning sunsets, white-washed buildings, and crystal-clear waters of this Greek island paradise.',
        'destination': 'Santorini, Greece',
        'hotel_name': 'Canaves Oia Suites',
        'price': Decimal('2499.00'),
        'start_date': date(2025, 3, 20),
        'end_date': date(2025, 3, 27),
        'visa_required': False,
        'meal_plan': 'bed_breakfast',
        'flight_type': 'layover'
    },
    {
        'title': 'Patagonia Wilderness Trek',
        'description': 'Explore the untamed beauty of Patagonia with dramatic landscapes, glaciers, and world-class hiking trails.',
        'destination': 'Torres del Paine, Chile',
        'hotel_name': 'EcoCamp Patagonia',
        'price': Decimal('3799.00'),
        'start_date': date(2025, 4, 8),
        'end_date': date(2025, 4, 15),
        'visa_required': True,
        'meal_plan': 'full_board',
        'flight_type': 'layover'
    },
    {
        'title': 'Maldives Luxury Retreat',
        'description': 'Ultimate tropical paradise with overwater villas, pristine beaches, and world-class diving in crystal-clear lagoons.',
        'destination': 'Maldives',
        'hotel_name': 'Four Seasons Resort Maldives',
        'price': Decimal('5999.00'),
        'start_date': date(2025, 5, 12),
        'end_date': date(2025, 5, 19),
        'visa_required': False,
        'meal_plan': 'all_inclusive',
        'flight_type': 'direct'
    },
    {
        'title': 'Morocco Desert Adventure',
        'description': 'Journey through imperial cities, bustling souks, and the vast Sahara Desert for an unforgettable cultural experience.',
        'destination': 'Marrakech, Morocco',
        'hotel_name': 'La Mamounia',
        'price': Decimal('2199.00'),
        'start_date': date(2025, 6, 3),
        'end_date': date(2025, 6, 10),
        'visa_required': True,
        'meal_plan': 'half_board',
        'flight_type': 'layover'
    },
    {
        'title': 'Iceland Northern Lights',
        'description': 'Chase the magical Northern Lights while exploring glaciers, waterfalls, and geothermal wonders in the land of fire and ice.',
        'destination': 'Reykjavik, Iceland',
        'hotel_name': 'Hotel Borg by Keahotels',
        'price': Decimal('3299.00'),
        'start_date': date(2025, 1, 25),
        'end_date': date(2025, 2, 1),
        'visa_required': False,
        'meal_plan': 'bed_breakfast',
        'flight_type': 'direct'
    },
    {
        'title': 'Costa Rica Eco Discovery',
        'description': 'Discover incredible biodiversity in rainforests, spot exotic wildlife, and relax on beautiful Pacific coast beaches.',
        'destination': 'Manuel Antonio, Costa Rica',
        'hotel_name': 'Arenas del Mar',
        'price': Decimal('2799.00'),
        'start_date': date(2025, 7, 15),
        'end_date': date(2025, 7, 22),
        'visa_required': False,
        'meal_plan': 'full_board',
        'flight_type': 'layover'
    },
    {
        'title': 'Dubai Luxury Experience',
        'description': 'Experience the height of luxury in this modern metropolis with stunning architecture, world-class shopping, and desert adventures.',
        'destination': 'Dubai, UAE',
        'hotel_name': 'Burj Al Arab Jumeirah',
        'price': Decimal('4599.00'),
        'start_date': date(2025, 8, 10),
        'end_date': date(2025, 8, 17),
        'visa_required': True,
        'meal_plan': 'all_inclusive',
        'flight_type': 'direct'
    },
    {
        'title': 'New Zealand Adventure',
        'description': 'Explore Middle-earth with stunning fjords, adventure sports, and breathtaking landscapes across both North and South Islands.',
        'destination': 'Queenstown, New Zealand',
        'hotel_name': 'Eichardt\'s Private Hotel',
        'price': Decimal('4199.00'),
        'start_date': date(2025, 9, 5),
        'end_date': date(2025, 9, 12),
        'visa_required': True,
        'meal_plan': 'bed_breakfast',
        'flight_type': 'layover'
    },
    {
        'title': 'Thai Island Hopping',
        'description': 'Discover the beauty of Thailand\'s islands with pristine beaches, vibrant marine life, and authentic Thai culture.',
        'destination': 'Phuket, Thailand',
        'hotel_name': 'Amanpuri',
        'price': Decimal('3199.00'),
        'start_date': date(2025, 10, 20),
        'end_date': date(2025, 10, 27),
        'visa_required': False,
        'meal_plan': 'half_board',
        'flight_type': 'direct'
    },
    {
        'title': 'Peru Machu Picchu Trek',
        'description': 'Follow ancient Inca trails to the legendary Machu Picchu and explore the rich cultural heritage of Peru.',
        'destination': 'Cusco, Peru',
        'hotel_name': 'Belmond Hotel Monasterio',
        'price': Decimal('2999.00'),
        'start_date': date(2025, 11, 8),
        'end_date': date(2025, 11, 15),
        'visa_required': False,
        'meal_plan': 'full_board',
        'flight_type': 'layover'
    },
    {
        'title': 'Norwegian Fjords Cruise',
        'description': 'Sail through dramatic fjords, witness stunning waterfalls, and experience the midnight sun in Norway\'s natural wonderland.',
        'destination': 'Bergen, Norway',
        'hotel_name': 'Hotel Admiral Bergen',
        'price': Decimal('3799.00'),
        'start_date': date(2025, 12, 12),
        'end_date': date(2025, 12, 19),
        'visa_required': False,
        'meal_plan': 'all_inclusive',
        'flight_type': 'direct'
    },
    {
        'title': 'Safari Kenya Adventure',
        'description': 'Witness the Great Migration and incredible wildlife in world-famous national parks and reserves.',
        'destination': 'Masai Mara, Kenya',
        'hotel_name': 'Governors\' Camp',
        'price': Decimal('4999.00'),
        'start_date': date(2026, 1, 15),
        'end_date': date(2026, 1, 22),
        'visa_required': True,
        'meal_plan': 'full_board',
        'flight_type': 'layover'
    }
]

# Create tours
created_count = 0
for tour_data in tours:
    try:
        tour = Tour.objects.create(
            agent=agent,
            **tour_data
        )
        created_count += 1
        print(f'Created: {tour.title} - {tour.destination} (${tour.price})')
    except Exception as e:
        print(f'Error creating tour {tour_data["title"]}: {e}')

print(f'Successfully created {created_count} tours')