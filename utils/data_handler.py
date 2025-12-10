import json
import os 
from datetime import datetime
import uuid


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR,'data')
SESSIONS_DIR = os.path.join(DATA_DIR,'sessions')

os.makedirs(SESSIONS_DIR, exist_ok=True)

def load_regions():
    """
    Load the regions database from JSON File.
    Returns dict with all the regions and cities data.
    """

    regions_path = os.path.join(DATA_DIR, 'regions.json')
    try:
        with open(regions_path,'r',encoding='utf-8') as f:
            return json.load(f)
    except FileExistsError:
        print(f'Error: regions.json not found at {regions_path}')
        return{'regions':{}}
    except json.JSONDecodeError as e:
        print(f'Error parsing regions.json: {e}')
        return {'regions':{}}
    
def create_session(creator_name, expected_users):
    """
    Create a new trip planning session.
    Args:
        creator_name: Name of the person creating the trip
        expected_users: How many people will participate
    
    Returns:
        session_id: Unique 8- character identifier

    """
    session_id = str(uuid.uuid4())[:8]


    session_data = {
        'session_id': session_id,
        'creator': creator_name,
        'expected_users': expected_users,
        'created_at': datetime.now().isoformat(),
        'status': 'collecting',
        'users': [],
        'results': None
    }

    save_session(session_id,session_data)
    return session_id


def save_session(session_id, session_data):
    """
    Save Session data to JSON File
    Each Session gets its own file: sessions/session_abc123.json
    """

    session_path = os.path.join(SESSIONS_DIR, f"session_{session_id}.json")
    with open(session_path, 'w',encoding='utf-8') as f:
        json.dump(session_data,f , indent=2,ensure_ascii=False)


def load_session(session_id):
    """
    Load an existing session by ID.
    Returns none if session doesnot exist.
    """

    session_path = os.path.join(SESSIONS_DIR,f'session_{session_id}.json')
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def add_user_to_session(session_id, user_data):
    """
    Add a user's preferences to a session

    Args: 
        session_id: The session to add to 
        user_data: Dict containing user's name and preferences

    Returns:
        True if successful , False if session not found
    """

    session = load_session(session_id)
    if not session:
        return False
    user_data['user_id'] = str(uuid.uuid4())[:8]
    user_data['submitted_at'] = datetime.now().isoformat()

    existing_user_index = None
    for i , user in enumerate(session['users']):
        if user['name'].lower() == user_data['name'].lower():
            existing_user_index = i
            break
    if existing_user_index is not None:
        session['users'][existing_user_index] = user_data
    else:
        session['users'].append(user_data)
    

    save_session(session_id,session)
    return True

def get_session_progress(session_id):
    """
    Get how many users have submitted vs expected.
    Returns: (submitted_count, expected_count, user_names)
    """
    session = load_session(session_id)
    if not session:
        return (0, 0, [])
    
    submitted = len(session['users'])
    expected = session['expected_users']  # ✅ Fixed!
    names = [user['name'] for user in session['users']]

    return (submitted, expected, names)

def mark_session_complete(session_id, results):
    """
    Mark session as complete and save results

    Args:
        session_id: Session to update
        results: Generated itinerary options
    """

    session = load_session(session_id)
    if not session:
        return False
    
    session['status'] = 'completed'
    session['results'] = results
    session['completed_at'] = datetime.now().isoformat()


    save_session(session_id,session)
    return True

