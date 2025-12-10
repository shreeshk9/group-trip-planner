"""
Scoring algorithms for matching users with cities and calculating compatibility.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def calculate_activity_similarity(user_activities, city_activities):
    """
    Calculate how well a city matches a user's activity preferences.
    
    Uses cosine similarity between two vectors:
    - User vector: [adventure, culture, food, nightlife, beach, nature, shopping]
    - City vector: [adventure, culture, food, nightlife, beach, nature, shopping]
    
    Returns: Similarity score 0-100 (0 = no match, 100 = perfect match)
    
    Why cosine similarity?
    - Handles different scales (user rates 1-5, city has 0-5)
    - Focuses on direction/pattern, not magnitude
    - Standard ML metric for preference matching
    """
    # Convert dicts to ordered lists (same order for both)
    activity_keys = ['adventure', 'culture', 'food', 'nightlife', 'beach', 'nature', 'shopping']
    
    user_vector = np.array([user_activities.get(key, 0) for key in activity_keys])
    city_vector = np.array([city_activities.get(key, 0) for key in activity_keys])
    
    # Reshape for sklearn (expects 2D arrays)
    user_vector = user_vector.reshape(1, -1)
    city_vector = city_vector.reshape(1, -1)
    
    # Calculate cosine similarity (returns 0-1)
    similarity = cosine_similarity(user_vector, city_vector)[0][0]
    
    # Convert to 0-100 scale for easier interpretation
    return similarity * 100

def calculate_group_city_score(users_data, city_data):
    """
    Calculate how well a city matches the ENTIRE group.
    
    Logic:
    1. Calculate similarity for each user with this city
    2. Average all similarities
    3. Apply budget penalty if city too expensive
    
    Returns: Score 0-100
    
    Why average not sum?
    - Fair for groups of any size
    - One person's strong preference doesn't dominate
    """
    similarities = []
    
    for user in users_data:
        user_activities = user['preferences']['activities']
        city_activities = city_data['activities']
        
        sim = calculate_activity_similarity(user_activities, city_activities)
        similarities.append(sim)
    
    # Average similarity across all users
    avg_similarity = np.mean(similarities)
    
    # Budget penalty: If city is too expensive for group, reduce score
    budget_penalty = calculate_budget_fit(users_data, city_data)
    
    # Final score = similarity × budget_fit (0-100 scale)
    final_score = avg_similarity * budget_penalty
    
    return final_score

def calculate_budget_fit(users_data, city_data):
    """
    Check if city fits within group's budget.
    
    Logic:
    1. Find group's budget overlap (min of max_budgets, max of min_budgets)
    2. Check if city's cost falls in this range
    3. Return penalty multiplier: 1.0 (perfect fit) to 0.5 (expensive but possible)
    
    Why not binary (yes/no)?
    - Some flexibility: slightly expensive city might still be worth it
    - Gradual penalty better than hard cutoff
    """
    # Calculate group budget range (the overlap where everyone agrees)
    min_budgets = [user['preferences']['budget']['min'] for user in users_data]
    max_budgets = [user['preferences']['budget']['max'] for user in users_data]
    
    group_min = max(min_budgets)  # Highest minimum (everyone can afford this)
    group_max = min(max_budgets)  # Lowest maximum (what tightest budget allows)
    
    # Get city's daily cost for the accommodation type most people prefer
    accommodation_prefs = [user['preferences']['accommodation'] for user in users_data]
    most_common_accommodation = max(set(accommodation_prefs), key=accommodation_prefs.count)
    
    city_daily_cost = city_data['avg_daily_cost'].get(most_common_accommodation, 
                                                       city_data['avg_daily_cost']['mid-range'])
    
    # Assume typical trip = 3 days for this city
    typical_days = city_data.get('typical_days', 2)
    city_total_cost = city_daily_cost * typical_days
    
    # Calculate fit
    if group_min <= city_total_cost <= group_max:
        return 1.0  # Perfect fit
    elif city_total_cost < group_min:
        return 0.95  # Cheaper than expected (still good!)
    elif city_total_cost <= group_max * 1.2:
        return 0.8  # Slightly expensive but doable
    elif city_total_cost <= group_max * 1.5:
        return 0.6  # Expensive, but might be worth it
    else:
        return 0.4  # Too expensive, heavy penalty

def calculate_group_compatibility(users_data):
    """
    Calculate how compatible the group is overall.
    
    Measures:
    1. How similar are their activity preferences?
    2. How much budget overlap?
    3. Date flexibility?
    
    Returns: Compatibility score 0-100
    
    Why this matters?
    - Shows user: "Your group agrees 85%" (builds confidence)
    - Helps algorithm: High compatibility = easier to find perfect trip
    """
    # Activity compatibility: Compare all pairs of users
    activity_similarities = []
    
    for i in range(len(users_data)):
        for j in range(i + 1, len(users_data)):
            user1_activities = users_data[i]['preferences']['activities']
            user2_activities = users_data[j]['preferences']['activities']
            
            sim = calculate_activity_similarity(user1_activities, user2_activities)
            activity_similarities.append(sim)
    
    avg_activity_compatibility = np.mean(activity_similarities) if activity_similarities else 50
    
    # Budget compatibility: How much overlap?
    min_budgets = [user['preferences']['budget']['min'] for user in users_data]
    max_budgets = [user['preferences']['budget']['max'] for user in users_data]
    
    group_min = max(min_budgets)
    group_max = min(max_budgets)
    
    if group_max >= group_min:
        # There's overlap - good!
        budget_compatibility = 100
    else:
        # No overlap - someone needs to compromise
        gap_percent = ((group_min - group_max) / group_min) * 100
        budget_compatibility = max(0, 100 - gap_percent)
    
    # Date flexibility: More flexible = easier planning
    flexible_count = sum(1 for user in users_data 
                        if user['preferences']['dates']['flexible'])
    date_flexibility = (flexible_count / len(users_data)) * 100
    
    # Weighted average (activities matter most, then budget, then dates)
    overall_compatibility = (
        avg_activity_compatibility * 0.5 +
        budget_compatibility * 0.3 +
        date_flexibility * 0.2
    )
    
    return round(overall_compatibility, 1)

def calculate_individual_satisfaction(user_data, selected_cities, cities_database):
    """
    Calculate how satisfied ONE user will be with the selected cities.
    
    Used to show: "This itinerary matches YOUR preferences 88%"
    
    Returns: Satisfaction score 0-100
    """
    satisfactions = []
    
    for city_name in selected_cities:
        city_data = cities_database.get(city_name, {})
        if not city_data:
            continue
        
        user_activities = user_data['preferences']['activities']
        city_activities = city_data.get('activities', {})
        
        sim = calculate_activity_similarity(user_activities, city_activities)
        satisfactions.append(sim)
    
    return round(np.mean(satisfactions), 1) if satisfactions else 50

def rank_cities_for_group(users_data, cities_dict):
    """
    Score and rank ALL cities for this group.
    
    Returns: List of (city_name, score) sorted by score (best first)
    
    This is the core ranking function the consensus algorithm uses.
    """
    city_scores = []
    
    for city_name, city_data in cities_dict.items():
        score = calculate_group_city_score(users_data, city_data)
        city_scores.append((city_name, score))
    
    # Sort by score descending (best cities first)
    city_scores.sort(key=lambda x: x[1], reverse=True)
    
    return city_scores