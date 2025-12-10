"""
Main consensus algorithm: Finds the best trip for the group.
"""

import numpy as np
from algorithms.scoring import (
    rank_cities_for_group,
    calculate_group_compatibility,
    calculate_individual_satisfaction
)


def select_region(users_data, regions_data):
    """
    Decide which region to visit based on group preferences.
    
    Logic:
    1. Count votes for each region
    2. Weight votes by budget/date compatibility
    3. Pick region with highest weighted score
    
    Returns: (region_name, region_cities_dict)
    """
    region_votes = {}

    for user in users_data:
        preferred_region = user['preferences']['region']

        if preferred_region not in region_votes:
            region_votes[preferred_region] = {'count': 0, 'total_weight': 0}

        # Base weight = 1 vote
        weight = 1.0

        # Bonus if dates are flexible (+0.2)
        if user['preferences']['dates']['flexible']:
            weight += 0.2

        # Bonus if budget is high (+0.3 if max > 40k)
        if user['preferences']['budget']['max'] > 40000:
            weight += 0.3

        region_votes[preferred_region]['count'] += 1
        region_votes[preferred_region]['total_weight'] += weight

    # Pick region with highest weighted score
    selected_region = max(region_votes.items(), key=lambda x: x[1]['total_weight'])[0]

    # Get cities for this region
    region_cities = regions_data['regions'][selected_region]['cities']

    return selected_region, region_cities


def allocate_days_to_cities(selected_cities, total_days, cities_database):
    """
    Decide how many days to spend in each city.
    """
    num_transitions = len(selected_cities) - 1
    travel_days = num_transitions * 0.5
    available_days = total_days - travel_days

    if available_days < 1:
        return {city: 1 for city in selected_cities}

    typical_days = []
    for city in selected_cities:
        city_data = cities_database.get(city, {})
        typical_days.append(city_data.get('typical_days', 2))

    total_typical = sum(typical_days)
    allocation = {}
    allocated_total = 0

    for i, city in enumerate(selected_cities[:-1]):
        city_days = (typical_days[i] / total_typical) * available_days
        city_days = max(1, round(city_days))
        allocation[city] = city_days
        allocated_total += city_days

    allocation[selected_cities[-1]] = max(1, int(available_days - allocated_total))
    return allocation


def generate_itinerary_options(users_data, regions_data):
    """
    Main algorithm: Generate 2–3 itinerary options for the group.
    """
    from algorithms.optimizer import optimize_route, create_travel_plan
    from generators.itinerary import generate_full_trip_itinerary, combine_group_preferences
    import time

    # Step 1: Select region
    selected_region, region_cities = select_region(users_data, regions_data)

    # Step 2: Rank cities
    ranked_cities = rank_cities_for_group(users_data, region_cities)

    # Step 3: Calculate compatibility
    group_compatibility = calculate_group_compatibility(users_data)

    # Step 4: Trip duration (median)
    durations = [user['preferences']['duration'] for user in users_data]
    avg_duration = int(np.median(durations))

    # Step 5: City count logic
    if avg_duration <= 4:
        num_cities = 2
    elif avg_duration <= 7:
        num_cities = 3
    else:
        num_cities = 4
    num_cities = min(num_cities, len(ranked_cities))

    # === OPTION 1: Optimal ===
    option1_cities_raw = [city[0] for city in ranked_cities[:num_cities]]
    option1_cities, option1_distance, _ = optimize_route(option1_cities_raw, region_cities)
    option1_travel_plan = create_travel_plan(option1_cities, region_cities)
    option1_allocation = allocate_days_to_cities(option1_cities, avg_duration, region_cities)
    option1_cost = estimate_trip_cost(users_data, option1_cities, option1_allocation, region_cities)

    # === OPTION 2: Budget ===
    budget_cities_raw = select_budget_friendly_cities(ranked_cities, num_cities, region_cities)
    budget_cities, option2_distance, _ = optimize_route(budget_cities_raw, region_cities)
    option2_travel_plan = create_travel_plan(budget_cities, region_cities)
    option2_allocation = allocate_days_to_cities(budget_cities, avg_duration, region_cities)
    option2_cost = estimate_trip_cost(users_data, budget_cities, option2_allocation, region_cities)

    # === OPTION 3: Adventurous ===
    adventurous_cities_raw = select_adventurous_mix(ranked_cities, num_cities, region_cities)
    adventurous_cities, option3_distance, _ = optimize_route(adventurous_cities_raw, region_cities)
    option3_travel_plan = create_travel_plan(adventurous_cities, region_cities)
    option3_allocation = allocate_days_to_cities(adventurous_cities, avg_duration, region_cities)
    option3_cost = estimate_trip_cost(users_data, adventurous_cities, option3_allocation, region_cities)

    # Individual satisfaction
    individual_scores_1 = [
        calculate_individual_satisfaction(user, option1_cities, region_cities)
        for user in users_data
    ]
    individual_scores_2 = [
        calculate_individual_satisfaction(user, budget_cities, region_cities)
        for user in users_data
    ]
    individual_scores_3 = [
        calculate_individual_satisfaction(user, adventurous_cities, region_cities)
        for user in users_data
    ]

    # === RESULTS ===
    results = {
        "selected_region": selected_region,
        "group_compatibility": group_compatibility,
        "options": [
            {
                "option_id": 1,
                "name": "Optimal Match",
                "description": "Best overall match for your group's preferences",
                "cities": option1_cities,
                "day_allocation": option1_allocation,
                "total_days": avg_duration,
                "total_distance_km": option1_distance,
                "travel_plan": option1_travel_plan,
                "estimated_cost_per_person": option1_cost,
                "group_score": round(np.mean([city[1] for city in ranked_cities[:num_cities]]), 1),
                "individual_scores": individual_scores_1,
                "votes": 0
            },
            {
                "option_id": 2,
                "name": "Budget-Friendly",
                "description": "Great experience at a lower cost",
                "cities": budget_cities,
                "day_allocation": option2_allocation,
                "total_days": avg_duration,
                "total_distance_km": option2_distance,
                "travel_plan": option2_travel_plan,
                "estimated_cost_per_person": option2_cost,
                "group_score": round(np.mean([score for city, score in ranked_cities if city in budget_cities]), 1),
                "individual_scores": individual_scores_2,
                "votes": 0
            },
            {
                "option_id": 3,
                "name": "Adventurous Mix",
                "description": "Popular spots plus unique off-beat experiences",
                "cities": adventurous_cities,
                "day_allocation": option3_allocation,
                "total_days": avg_duration,
                "total_distance_km": option3_distance,
                "travel_plan": option3_travel_plan,
                "estimated_cost_per_person": option3_cost,
                "group_score": round(np.mean([score for city, score in ranked_cities if city in adventurous_cities]), 1),
                "individual_scores": individual_scores_3,
                "votes": 0
            }
        ]
    }

    # === GENERATE DETAILED ITINERARY (Gemini) ===
    group_prefs_combined = combine_group_preferences(users_data)

    for i in [0]:  # Only for first option (to avoid quota issue)
        option = results['options'][i]
        try:
            print(f"Generating detailed itinerary for Option {i + 1}: {option['name']}...")

            detailed_itinerary = generate_full_trip_itinerary(
                option_data=option,
                region_cities=region_cities,
                group_preferences_combined=group_prefs_combined
            )

            results['options'][i]['detailed_itinerary'] = detailed_itinerary
            print(f"✓ Option {i + 1} detailed itinerary generated successfully!")

        except Exception as e:
            print(f"✗ Error generating itinerary for Option {i + 1}: {str(e)}")
            results['options'][i]['detailed_itinerary'] = {
                'error': f'Could not generate detailed itinerary: {str(e)}'
            }

    # Add note for other options
    for i in [1, 2]:
        results['options'][i]['detailed_itinerary'] = {
            'note': 'Detailed itinerary generated for Option 1 only.'
        }

    return results


def select_budget_friendly_cities(ranked_cities, num_cities, cities_database):
    """
    Select cheaper but good-score cities.
    """
    city_costs = []
    for city_name, score in ranked_cities:
        city_data = cities_database.get(city_name, {})
        avg_cost = city_data.get('avg_daily_cost', {}).get('mid-range', 5000)
        typical_days = city_data.get('typical_days', 2)
        total_cost = avg_cost * typical_days

        if score > 60:
            city_costs.append((city_name, score, total_cost))

    city_costs.sort(key=lambda x: x[2])
    selected = [city[0] for city in city_costs[:num_cities]]

    if len(selected) < num_cities:
        for city, score in ranked_cities:
            if city not in selected:
                selected.append(city)
                if len(selected) >= num_cities:
                    break
    return selected


def select_adventurous_mix(ranked_cities, num_cities, cities_database):
    """
    Mix top + off-beat cities.
    """
    selected = []

    if ranked_cities:
        selected.append(ranked_cities[0][0])

    mid_ranked = ranked_cities[3:min(8, len(ranked_cities))]
    np.random.shuffle(mid_ranked)

    for city, score in mid_ranked:
        if len(selected) >= num_cities:
            break
        selected.append(city)

    if len(selected) < num_cities:
        for city, score in ranked_cities[1:]:
            if city not in selected:
                selected.append(city)
                if len(selected) >= num_cities:
                    break

    return selected


def estimate_trip_cost(users_data, selected_cities, day_allocation, cities_database):
    """
    Estimate total cost per person.
    """
    accommodation_prefs = [user['preferences']['accommodation'] for user in users_data]
    most_common = max(set(accommodation_prefs), key=accommodation_prefs.count)

    total_cost = 0

    for city, days in day_allocation.items():
        city_data = cities_database.get(city, {})
        daily_cost = city_data.get('avg_daily_cost', {}).get(most_common, 3000)
        total_cost += (daily_cost + 1500 + 500) * days

    num_transitions = len(selected_cities) - 1
    total_cost += num_transitions * 2000

    return int(total_cost)
