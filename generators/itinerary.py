"""
Gemini-powered itinerary generation.
Generates detailed day-by-day plans for each city.
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
# You'll set this as environment variable or directly here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize model
model = genai.GenerativeModel("models/gemini-2.5-flash")

def generate_city_itinerary(city_name, num_days, group_preferences, budget_level, city_description):
    """
    Generate detailed day-by-day itinerary for ONE city using Gemini.
    
    Args:
        city_name: Name of the city
        num_days: How many days to spend here
        group_preferences: Dict with activity scores
        budget_level: 'budget', 'mid-range', or 'luxury'
        city_description: Brief description of the city
    
    Returns:
        String with formatted itinerary
    
    Why we need this?
    - Our algorithm picks cities, but users need DETAILS
    - What to do each day? Where to eat? What time?
    - Gemini generates this rich content
    """
    
    # Find top 3 activities the group loves
    top_activities = sorted(group_preferences.items(), 
                           key=lambda x: x[1], 
                           reverse=True)[:3]
    top_activity_names = [act[0] for act in top_activities]
    
    # Create detailed prompt for Gemini
    prompt = f"""
You are an expert travel planner. Create a detailed {num_days}-day itinerary for {city_name}.

CITY INFO:
{city_description}

GROUP PREFERENCES:
- Top interests: {', '.join(top_activity_names)}
- Budget level: {budget_level}
- Travel pace: moderate (not too rushed, but productive)

REQUIREMENTS:
1. Create a day-by-day plan for {num_days} days
2. Focus heavily on {top_activity_names[0]} and {top_activity_names[1]} activities
3. Include specific attractions, restaurants, and timings
4. Add estimated costs in Indian Rupees (₹)
5. Include practical tips (best time to visit, dress code, etc.)
6. Suggest both popular AND hidden gems
7. Keep budget appropriate for {budget_level} travelers

FORMAT EACH DAY LIKE THIS:

## Day X: [Theme]

### Morning (9:00 AM - 12:00 PM)
**[Attraction Name]**
- What: Brief description
- Why: Why it's great for this group
- Time: How long to spend
- Cost: ₹X per person
- Tip: Practical advice

### Lunch (12:30 PM - 1:30 PM)
**[Restaurant Name]**
- Cuisine type
- Must-try dishes
- Cost: ₹X per person

### Afternoon (2:00 PM - 5:00 PM)
[Continue same format]

### Evening (6:00 PM - 9:00 PM)
[Continue same format]

### Dinner (9:00 PM onwards)
[Restaurant suggestion]

---

START THE ITINERARY:
"""
    
    try:
        # Call Gemini API
        response = model.generate_content(prompt)
        
        # Extract text
        itinerary_text = response.text
        
        return itinerary_text
        
    except Exception as e:
        # Fallback if API fails
        return f"""
## {city_name} - {num_days} Day Itinerary

### Day 1
**Morning:** Explore main attractions focusing on {top_activity_names[0]}
**Afternoon:** Visit local markets and cultural sites
**Evening:** Experience local cuisine and nightlife

### Day 2
**Morning:** Continue exploring with focus on {top_activity_names[1]}
**Afternoon:** Leisure activities and shopping
**Evening:** Sunset views and dinner at recommended spots

(Note: Detailed itinerary generation failed. Error: {str(e)})
"""

def generate_full_trip_itinerary(option_data, region_cities, group_preferences_combined):
    """
    Generate complete itinerary for all cities in one option.
    
    Args:
        option_data: One option from consensus algorithm output
        region_cities: Database of cities in this region
        group_preferences_combined: Averaged activity preferences for the group
    
    Returns:
        Dict with itineraries for each city
    
    Why separate function?
    - Handles multiple cities
    - Coordinates between cities
    - Adds travel days
    """
    
    cities = option_data['cities']
    day_allocation = option_data['day_allocation']
    travel_plan = option_data.get('travel_plan', [])
    budget_level = 'mid-range'  # Default, could be calculated from user data
    
    full_itinerary = {}
    current_day = 1
    
    for i, city in enumerate(cities):
        city_data = region_cities.get(city, {})
        num_days = int(day_allocation.get(city, 2))  # Convert to int to fix error
        city_description = city_data.get('description', f'{city} - A wonderful destination')
        
        # Generate itinerary for this city
        city_itinerary = generate_city_itinerary(
            city_name=city,
            num_days=num_days,
            group_preferences=group_preferences_combined,
            budget_level=budget_level,
            city_description=city_description
        )
        
        # Use integers for day ranges
        full_itinerary[city] = {
            'city_name': city,
            'days': num_days,
            'day_numbers': list(range(int(current_day), int(current_day + num_days))),
            'itinerary': city_itinerary
        }
        
        current_day += num_days
        
        # Add travel day if there's another city after this
        if i < len(cities) - 1:
            travel_info = travel_plan[i] if i < len(travel_plan) else {}
            travel_day_text = f"""
## Travel Day: {city} → {cities[i+1]}

**Transport:** {travel_info.get('transport', 'Car/Train')}
**Distance:** {travel_info.get('distance_km', 'N/A')} km
**Duration:** {travel_info.get('travel_time_hours', 'N/A')} hours
**Estimated Cost:** ₹{travel_info.get('cost_estimate', 'N/A')} per person

**Morning:** Check out from {city} accommodation
**Travel:** {travel_info.get('transport', 'Travel')} to {cities[i+1]}
**Evening:** Check into {cities[i+1]} accommodation, rest and explore nearby area
"""
            
            full_itinerary[f'travel_{i+1}'] = {
                'city_name': f'Travel: {city} → {cities[i+1]}',
                'days': 0.5,
                'day_numbers': [int(current_day)],
                'itinerary': travel_day_text
            }
            
            current_day += 0.5
    
    return full_itinerary

def combine_group_preferences(users_data):
    """
    Average activity preferences across all users.
    
    Why?
    - Gemini needs ONE set of preferences to work with
    - Take the group's average interest in each activity
    
    Returns: Dict like {'adventure': 3.5, 'culture': 4.2, ...}
    """
    activity_sums = {
        'adventure': 0, 'culture': 0, 'food': 0,
        'nightlife': 0, 'beach': 0, 'nature': 0, 'shopping': 0
    }
    
    num_users = len(users_data)
    
    for user in users_data:
        activities = user['preferences']['activities']
        for activity, score in activities.items():
            activity_sums[activity] += score
    
    # Calculate averages
    avg_preferences = {
        activity: round(total / num_users, 1)
        for activity, total in activity_sums.items()
    }
    
    return avg_preferences