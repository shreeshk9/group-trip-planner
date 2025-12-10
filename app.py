import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image
import urllib.parse

# Import our utilities
from utils.data_handler import (
    create_session, load_session, add_user_to_session,
    get_session_progress, load_regions
)

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Group Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load regions data (we'll need this throughout)
REGIONS_DATA = load_regions()
AVAILABLE_REGIONS = list(REGIONS_DATA['regions'].keys())

def generate_qr_code(url):
    """
    Generate QR code image for a URL.
    Returns image in BytesIO format that Streamlit can display.
    
    Why BytesIO? Streamlit expects bytes, not PIL Image directly.
    We convert PIL Image → bytes → Streamlit can display it.
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create PIL Image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return buf

def show_homepage():
    """
    Homepage: User creates a new trip session.
    """
    st.title("🌍 Group Trip Consensus Planner")
    st.markdown("---")
    
    st.write("""
    ### Planning a trip with friends? Let's make it easy! 🎉
    
    **How it works:**
    1. You create a trip session
    2. Share the link with your friends
    3. Everyone submits their preferences
    4. Our algorithm finds the perfect trip for your group!
    """)
    
    st.markdown("---")
    
    # Form to create new session
    with st.form("create_session_form"):
        st.subheader("Create New Trip")
        
        creator_name = st.text_input(
            "Your Name",
            placeholder="e.g., Alice",
            help="We'll use this to identify who created the trip"
        )
        
        num_friends = st.number_input(
            "How many people (including you)?",
            min_value=2,
            max_value=10,
            value=4,
            help="Total number of travelers in your group"
        )
        
        submitted = st.form_submit_button("🚀 Create Trip Session", use_container_width=True)
        
        if submitted:
            if not creator_name.strip():
                st.error("Please enter your name!")
            else:
                # Create session
                session_id = create_session(creator_name.strip(), num_friends)
                
                # Store in session state (so we can show success page)
                st.session_state['created_session_id'] = session_id
                st.session_state['creator_name'] = creator_name.strip()
                
                # Rerun to show success page
                st.rerun()
    
    # Show success page if session just created
    if 'created_session_id' in st.session_state:
        show_session_created()

def show_session_created():
    """
    Show shareable link and QR code after session creation.
    """
    session_id = st.session_state['created_session_id']
    creator_name = st.session_state['creator_name']
    
    st.success(f"🎉 Trip created by {creator_name}!")
    st.markdown("---")
    
    # Generate shareable URL
    base_url = "http://localhost:8501"  # Will be your deployed URL later
    session_url = f"{base_url}/?session={session_id}"
    
    st.subheader("📤 Share with Your Friends")
    
    # Create 3 columns for different sharing methods
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**🔗 Link**")
        st.code(session_url, language=None)
        st.caption("Copy this link and share via WhatsApp/Telegram/Email")
    
    with col2:
        st.write("**📱 QR Code**")
        qr_img = generate_qr_code(session_url)
        st.image(qr_img, width=200)
        st.caption("Show this QR code to friends in person")
    
    with col3:
        st.write("**🔢 Session Code**")
        st.code(session_id, language=None)
        st.caption("Friends can enter this code manually")
    
    # WhatsApp share button
    whatsapp_text = f"Join my trip planning! 🌍 {session_url}"
    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(whatsapp_text)}"
    st.link_button("Share on WhatsApp", whatsapp_url, type="primary")
    
    st.markdown("---")
    
    # Show progress
    submitted, expected, names = get_session_progress(session_id)
    
    st.subheader("👥 Who's Joined?")
    progress_percent = submitted / expected if expected > 0 else 0
    st.progress(progress_percent)
    st.write(f"**{submitted} of {expected} people** have submitted preferences")
    
    if names:
        st.write("✅ " + ", ".join(names))
    
    # Button to go to form (creator also needs to fill preferences)
    if st.button("Fill My Preferences", type="primary", use_container_width=True):
        # Clear created session from state and set query params
        del st.session_state['created_session_id']
        del st.session_state['creator_name']
        st.query_params.session = session_id
        st.rerun()
    
    # Refresh button to check progress
    if st.button("🔄 Refresh Progress"):
        st.rerun()

def show_join_session(session_id):
    """
    User joins existing session and fills preferences.
    """
    # Load session data
    session = load_session(session_id)
    
    if not session:
        st.error("❌ Session not found. Please check the link.")
        if st.button("← Go to Homepage"):
            st.query_params.clear()
            st.rerun()
        return
    
    # Check if session is already completed
    if session['status'] == 'completed':
        st.info("This trip planning is already complete!")
        show_results(session)
        return
    
    # Show header
    st.title(f"Join {session['creator']}'s Trip! ✈️")
    st.write(f"Fill in your preferences below. {session['expected_users']} travelers expected.")
    
    st.markdown("---")
    
    # Preference collection form
    with st.form("preference_form"):
        st.subheader("About You")
        
        user_name = st.text_input(
            "Your Name",
            placeholder="e.g., Bob",
            help="So we know who's who!"
        )
        
        st.markdown("---")
        st.subheader("Trip Preferences")
        
        # Region selection
        selected_region = st.selectbox(
            "Which region would you like to visit?",
            options=AVAILABLE_REGIONS,
            help="We'll suggest cities within this region"
        )
        
        # Budget
        col1, col2 = st.columns(2)
        with col1:
            min_budget = st.number_input(
                "Minimum Budget (₹ per person)",
                min_value=5000,
                max_value=200000,
                value=20000,
                step=5000
            )
        with col2:
            max_budget = st.number_input(
                "Maximum Budget (₹ per person)",
                min_value=5000,
                max_value=200000,
                value=50000,
                step=5000
            )
        
        # Duration
        duration = st.slider(
            "How many days?",
            min_value=2,
            max_value=15,
            value=7,
            help="Total trip duration including travel days"
        )
        
        # Travel dates
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Preferred Start Date")
        with col2:
            flexible_dates = st.checkbox("Dates are flexible", value=True)
        
        st.markdown("---")
        st.subheader("What do you enjoy?")
        st.write("Rate your interest in these activities (1 = Not interested, 5 = Love it!)")
        
        # Activity preferences
        col1, col2 = st.columns(2)
        
        with col1:
            adventure = st.slider("🏔️ Adventure (hiking, sports)", 1, 5, 3)
            culture = st.slider("🏛️ Culture & Heritage", 1, 5, 3)
            food = st.slider("🍜 Food & Cuisine", 1, 5, 3)
            nightlife = st.slider("🎉 Nightlife & Entertainment", 1, 5, 3)
        
        with col2:
            beach = st.slider("🏖️ Beach & Relaxation", 1, 5, 3)
            nature = st.slider("🌳 Nature & Wildlife", 1, 5, 3)
            shopping = st.slider("🛍️ Shopping", 1, 5, 3)
        
        st.markdown("---")
        
        # Travel style
        col1, col2 = st.columns(2)
        with col1:
            pace = st.select_slider(
                "Travel Pace",
                options=["relaxed", "moderate", "packed"],
                value="moderate",
                help="How much do you want to pack into each day?"
            )
        
        with col2:
            accommodation = st.select_slider(
                "Accommodation Preference",
                options=["budget", "mid-range", "luxury"],
                value="mid-range"
            )
        
        # Submit button
        submitted = st.form_submit_button(
            "✅ Submit My Preferences",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Validation
            if not user_name.strip():
                st.error("Please enter your name!")
            elif min_budget > max_budget:
                st.error("Minimum budget cannot be greater than maximum budget!")
            else:
                # Create user data object
                user_data = {
                    "name": user_name.strip(),
                    "preferences": {
                        "region": selected_region,
                        "budget": {"min": min_budget, "max": max_budget},
                        "duration": duration,
                        "dates": {
                            "start": start_date.isoformat(),
                            "flexible": flexible_dates
                        },
                        "activities": {
                            "adventure": adventure,
                            "culture": culture,
                            "food": food,
                            "nightlife": nightlife,
                            "beach": beach,
                            "nature": nature,
                            "shopping": shopping
                        },
                        "pace": pace,
                        "accommodation": accommodation
                    }
                }
                
                # Save to session
                success = add_user_to_session(session_id, user_data)
                
                if success:
                    st.success(f"✅ Thanks {user_name}! Your preferences are saved.")
                    st.balloons()
                    
                    # Show progress
                    submitted_count, expected, names = get_session_progress(session_id)
                    st.info(f"👥 {submitted_count} of {expected} people have submitted.")
                else:
                    st.error("Error saving preferences. Please try again.")
    
    # Show current progress OUTSIDE the form
    st.markdown("---")
    submitted_count, expected, names = get_session_progress(session_id)
    
    st.subheader("👥 Current Progress")
    progress_percent = submitted_count / expected if expected > 0 else 0
    st.progress(progress_percent)
    st.write(f"**{submitted_count} of {expected} people** have submitted")
    
    if names:
        st.write("✅ Submitted: " + ", ".join(names))
    
    # Generate button OUTSIDE form - only show if everyone submitted
    if submitted_count >= expected:
        st.success("🎉 Everyone has submitted! Ready to generate itinerary.")
        if st.button("🚀 Generate Trip Plan", type="primary", use_container_width=True):
            from algorithms.consensus import generate_itinerary_options
            
            with st.spinner("🧠 Analyzing preferences and finding perfect trip..."):
                try:
                    # Run the consensus algorithm
                    results = generate_itinerary_options(session['users'], REGIONS_DATA)
                    
                    # Save results to session (mark as completed)
                    from utils.data_handler import mark_session_complete
                    mark_session_complete(session_id, results)
                    
                    st.success("✅ Trip plan generated!")
                    st.balloons()
                    
                    session = load_session(session_id)

                    st.rerun() 
                    
                    # TODO: Replace st.json with beautiful results display (next step)
                    
                except Exception as e:
                    st.error(f"Error generating trip plan: {str(e)}")
                    st.exception(e)  # Shows full error for debugging

def show_results(session):
    """
    Display generated itinerary options in a beautiful format.
    """
    results = session.get('results')
    
    if not results:
        st.error("No results found. Please generate trip plan first.")
        return
    
    # Header
    st.title(f"🎯 Your Group's Perfect Trip to {results['selected_region']}")
    
    # Group compatibility badge
    compatibility = results['group_compatibility']
    if compatibility >= 90:
        emoji = "🔥"
        color = "green"
    elif compatibility >= 75:
        emoji = "✨"
        color = "blue"
    else:
        emoji = "👍"
        color = "orange"
    
    st.markdown(f"### {emoji} Group Compatibility: **{compatibility}%**")
    st.caption("How well your group's preferences align")
    
    st.markdown("---")
    
    # Show participants
    with st.expander("👥 Trip Participants"):
        for user in session['users']:
            st.write(f"- **{user['name']}**")
    
    st.markdown("---")
    
    # Tabs for 3 options
    tab1, tab2, tab3 = st.tabs([
        f"✨ {results['options'][0]['name']}",
        f"💰 {results['options'][1]['name']}",
        f"🎒 {results['options'][2]['name']}"
    ])
    
    # Display each option in its tab
    for tab, option in zip([tab1, tab2, tab3], results['options']):
        with tab:
            display_option_details(option, session['users'], results['selected_region'])

def display_option_details(option, users, region):
    """
    Display detailed view of one itinerary option.
    """
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cities", len(option['cities']))
    
    with col2:
        st.metric("Total Days", option['total_days'])
    
    with col3:
        st.metric("Cost/Person", f"₹{option['estimated_cost_per_person']:,}")
    
    with col4:
        st.metric("Group Score", f"{option['group_score']}%")
    
    st.markdown("---")
    
    # Cities route
    st.subheader("📍 Your Route")
    cities_route = " → ".join(option['cities'])
    st.info(f"**{cities_route}**")
    
    # Travel overview
    st.write(f"**Total Distance:** {option['total_distance_km']} km")
    
    # Day allocation
    st.subheader("📅 Days per City")
    for city, days in option['day_allocation'].items():
        st.write(f"- **{city}**: {days} days")
    
    st.markdown("---")
    
    # Individual satisfaction scores
    st.subheader("😊 How Well This Matches Each Person")
    
    cols = st.columns(len(users))
    for col, user, score in zip(cols, users, option['individual_scores']):
        with col:
            # Color based on score
            if score >= 85:
                emoji = "😍"
            elif score >= 75:
                emoji = "😊"
            else:
                emoji = "🙂"
            
            st.metric(user['name'], f"{score}% {emoji}")
    
    st.markdown("---")
    
    # Travel plan
    if option.get('travel_plan'):
        with st.expander("🚗 Travel Details Between Cities"):
            for segment in option['travel_plan']:
                st.write(f"**{segment['from']} → {segment['to']}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"📏 {segment['distance_km']} km")
                with col2:
                    st.write(f"⏱️ {segment['travel_time_hours']} hours")
                with col3:
                    st.write(f"🚗 {segment['transport']}")
                st.caption(f"Estimated cost: ₹{segment['cost_estimate']} per person")
                st.divider()
    
    st.markdown("---")
    
    # Detailed itinerary
    detailed = option.get('detailed_itinerary', {})
    
    if 'error' in detailed or 'note' in detailed:
        # Option doesn't have detailed itinerary
        st.info(f"💡 **Note:** Detailed itinerary is available for Option 1 (Optimal Match). "
                f"This option shows city selections, travel plan, and cost estimates.")
    else:
        # Show detailed itinerary
        st.subheader("📝 Detailed Day-by-Day Itinerary")
        
        for key, city_itinerary in detailed.items():
            city_name = city_itinerary['city_name']
            days = city_itinerary.get('days', 0)
            itinerary_text = city_itinerary['itinerary']
            
            # Create expandable section for each city
            with st.expander(f"📍 {city_name} ({days} days)", expanded=True):
                # Check if it's a travel day
                if 'Travel:' in city_name:
                    st.info(itinerary_text)
                else:
                    # Regular city itinerary - display as markdown
                    st.markdown(itinerary_text)
    
    st.markdown("---")
    
    # Voting section
    st.subheader("👍 Vote for This Option")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Like this itinerary? Vote to help your group decide!")
    with col2:
        if st.button(f"Vote for {option['name']}", 
                    key=f"vote_{option['option_id']}", 
                    type="primary",
                    use_container_width=True):
            st.success("Vote recorded! 🎉")
            st.balloons()
            # TODO: Implement vote counting in session

# ---- App Entry Point ----
def main():
    query_params = st.query_params

    if "session" in query_params:
        session_id = query_params["session"]
        show_join_session(session_id)
    else:
        show_homepage()

if __name__ == "__main__":
    main()
