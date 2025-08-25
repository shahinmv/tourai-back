#!/usr/bin/env python
"""
Quick test to verify tools are working after the formatted_price fix
"""
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourai_back.settings')
django.setup()

from users.chat_service import search_tours_by_destination, search_tours_by_keyword, search_tours_by_price_range

def test_tools():
    """Test that tools work without errors"""
    
    print("🔧 TESTING TOOL EXECUTION")
    print("=" * 30)
    
    try:
        # Test destination search
        print("1. Testing search_tours_by_destination...")
        result1 = search_tours_by_destination.invoke({"destination": "Thailand"})
        print(f"   ✅ Success: Found {len(result1)} tours")
        
        # Test keyword search  
        print("2. Testing search_tours_by_keyword...")
        result2 = search_tours_by_keyword.invoke({"keyword": "adventure"})
        print(f"   ✅ Success: Found {len(result2)} tours")
        
        # Test price range search
        print("3. Testing search_tours_by_price_range...")
        result3 = search_tours_by_price_range.invoke({"min_price": 1000, "max_price": 5000})
        print(f"   ✅ Success: Found {len(result3)} tours")
        
        # Verify structure
        if result1:
            keys = list(result1[0].keys())
            print(f"\n📊 Tour data structure: {keys}")
            expected_keys = {'id', 'title', 'description', 'destination', 'hotel_name', 'price', 'formatted_price', 'start_date', 'end_date', 'visa_required', 'meal_plan', 'flight_type', 'agent_name', 'company_name'}
            if set(keys) == expected_keys:
                print("   ✅ Correct full tour structure")
            else:
                print(f"   ❌ Unexpected structure. Missing: {expected_keys - set(keys)}")
                
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_tools()
    if success:
        print("\n🎉 All tools working correctly!")
    else:
        print("\n❌ Tool execution failed")