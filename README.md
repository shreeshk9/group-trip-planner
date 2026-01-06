# 🌍 Group Trip Consensus Planner

An intelligent ML-powered travel planning system that helps groups of friends reach consensus on trip destinations by analyzing individual preferences and generating optimized itineraries.

## 🎯 Problem Statement

Planning trips with friends is challenging when everyone has different preferences, budgets, and interests. This project solves that by:
- Collecting preferences from all group members
- Using ML algorithms to find destinations that maximize group satisfaction
- Generating detailed, personalized itineraries

## ✨ Features

### Core ML Algorithms
- **Consensus Algorithm**: Uses weighted voting and cosine similarity to match group preferences with destinations
- **Preference Matching**: Analyzes activity preferences (culture, food, adventure, etc.) using vector similarity
- **Route Optimization**: Implements Haversine distance calculation and brute-force TSP for optimal city ordering
- **Compatibility Scoring**: Calculates group alignment (0-100%) based on preference overlap

### Smart Planning
- **Multi-city Itinerary Generation**: Selects 2-4 cities based on trip duration
- **Day Allocation**: Proportionally distributes days based on city importance and group interests
- **Travel Optimization**: Minimizes travel time and recommends transport modes (car/train/flight)
- **Budget Estimation**: Calculates realistic costs including accommodation, food, and transport

### Three Itinerary Options
1. **Optimal Match**: Highest compatibility with group preferences
2. **Budget-Friendly**: Cost-optimized while maintaining good satisfaction scores
3. **Adventurous Mix**: Blend of popular destinations and off-beat experiences

### AI Integration
- **Gemini AI**: Generates detailed day-by-day itineraries with:
  - Specific attractions with timings and costs
  - Restaurant recommendations
  - Practical tips and local insights

## 🛠️ Tech Stack

**Backend & ML:**
- Python 3.12
- NumPy, Pandas (data processing)
- scikit-learn (cosine similarity, clustering)
- Custom algorithms (weighted voting, route optimization)

**Frontend:**
- Streamlit (interactive web interface)

**APIs:**
- Google Gemini AI (itinerary generation)

**Data Management:**
- JSON-based storage
- Session management system

## 📊 ML Concepts Demonstrated

- **Cosine Similarity**: Activity preference vector matching
- **Weighted Voting**: Budget and flexibility-weighted region selection
- **Multi-objective Optimization**: Balancing preferences, cost, and travel time
- **Clustering Analysis**: Grouping similar user preferences
- **Statistical Aggregation**: Median-based trip duration, mean compatibility scores
- **Distance Calculation**: Haversine formula for geo-coordinates
- **TSP Optimization**: Brute-force approach for small N (2-4 cities)

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.8+
pip
```

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/group-trip-planner.git
cd group-trip-planner
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

5. **Run the application:**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 How It Works

### 1. Create Trip Session
- One person creates a trip and gets a shareable link/QR code
- Friends join using the link

### 2. Collect Preferences
Each user submits:
- Preferred region (Rajasthan, Italy, Thailand, etc.)
- Budget range (min-max)
- Trip duration
- Activity interests (rated 1-5): Adventure, Culture, Food, Nightlife, Beach, Nature, Shopping
- Travel pace and accommodation preference

### 3. Algorithm Processing

**Region Selection:**
```
Weight = base_vote × flexibility_bonus × budget_bonus
Selected_region = argmax(weighted_votes)
```

**City Scoring:**
```
Score = cosine_similarity(user_activities, city_activities) × budget_fit
Group_score = mean(individual_scores)
```

**Route Optimization:**
```
For all permutations of cities:
    Calculate total_distance using Haversine
    Select route with minimum distance
```

### 4. Results Display
- 3 optimized itinerary options
- Group compatibility score
- Individual satisfaction scores
- Detailed day-by-day plans
- Travel logistics (transport, timings, costs)

## 📁 Project Structure

```
group-trip-planner/
│
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
│
├── data/
│   ├── regions.json           # City database (3 regions, 15 cities)
│   └── sessions/              # User session files (gitignored)
│
├── algorithms/
│   ├── consensus.py           # Main consensus algorithm
│   ├── scoring.py             # Similarity and scoring functions
│   └── optimizer.py           # Route optimization logic
│
├── generators/
│   └── itinerary.py           # Gemini AI integration
│
└── utils/
    └── data_handler.py        # Session and data management
```

## 🎓 Key Algorithms Explained

### Cosine Similarity for Preference Matching
```python
similarity = (user_vector · city_vector) / (||user_vector|| × ||city_vector||)
```
Returns 0-1, where 1 = perfect match

### Haversine Distance Formula
```python
distance = 2 × R × arcsin(√(a))
where a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
```
Calculates actual travel distance on Earth's surface

### Weighted Voting
```python
weight = 1.0 + flexible_dates_bonus + high_budget_bonus
region_score = Σ(votes × weights)
```

## 💡 Design Decisions

### Why Cosine Similarity?
- Handles different preference scales naturally
- Focuses on preference patterns, not absolute values
- Standard ML technique for recommendation systems

### Why Brute Force TSP?
- Optimal solution guaranteed for N ≤ 7 cities
- Fast enough (4! = 24 permutations for 4 cities)
- Our use case: 2-4 cities per trip

### Why Median for Trip Duration?
- Less affected by outliers than mean
- Example: [7, 7, 7, 15 days] → median = 7 (reasonable)

### Why Three Options?
- Gives groups choice and control
- Different optimization priorities (compatibility vs cost vs variety)
- Increases user satisfaction

## 🎨 Screenshots

*Add screenshots here of:*
- Homepage
- Preference form
- Results page with 3 options
- Detailed itinerary view

## 🔮 Future Enhancements

- [ ] Real-time collaborative voting
- [ ] Flight/hotel booking integration
- [ ] Past trip learning (improve recommendations over time)
- [ ] Mobile app version
- [ ] Social media integration
- [ ] Export itinerary to PDF/Calendar
- [ ] Multi-language support

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome!

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

- GitHub: shreeshk9
- LinkedIn: Shreesh Kulkarni
- Email: kulkarnishreesh9@gmail.com

## 🙏 Acknowledgments

- Google Gemini AI for itinerary generation
- Streamlit for the web framework
- scikit-learn for ML utilities

---

⭐ **Star this repo if you find it helpful!**
