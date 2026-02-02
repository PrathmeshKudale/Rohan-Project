from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import secrets
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import smtplib
import random
import string
from functools import wraps
import requests

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'mov'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['SESSION_TYPE'] = 'filesystem'

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mock database (in production, use PostgreSQL/MySQL)
users_db = {}
otp_store = {}
crop_data = {}
farmer_posts = []
products_list = []

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """OTP-based login"""
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        if mobile and len(mobile) == 10 and mobile.isdigit():
            # Generate OTP
            otp = ''.join(random.choices(string.digits, k=6))
            otp_store[mobile] = otp
            # In production: Send SMS via Twilio/msg91
            print(f"OTP for {mobile}: {otp}")  # For demo
            session['pending_mobile'] = mobile
            return redirect(url_for('verify_otp'))
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP"""
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        mobile = session.get('pending_mobile')
        
        if mobile in otp_store and otp_store[mobile] == entered_otp:
            # Create user if not exists
            if mobile not in users_db:
                users_db[mobile] = {
                    'mobile': mobile,
                    'joined': datetime.now().isoformat(),
                    'language': 'hindi',
                    'region': 'default'
                }
            session['user_id'] = mobile
            session['language'] = users_db[mobile]['language']
            del otp_store[mobile]
            session.pop('pending_mobile', None)
            return redirect(url_for('dashboard'))
        
        return render_template('verify_otp.html', error="Invalid OTP")
    
    return render_template('verify_otp.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html', user=users_db.get(session['user_id']))

@app.route('/crop-library')
@login_required
def crop_library():
    """Crop knowledge base"""
    crops = [
        {
            'id': 1,
            'name': 'Wheat',
            'hindi_name': 'गेहूं',
            'soil': 'Well-drained loamy soil',
            'water': 'Moderate (500-600mm)',
            'season': 'Rabi (Oct-Nov sowing)',
            'harvest': 'March-April'
        },
        {
            'id': 2,
            'name': 'Rice',
            'hindi_name': 'धान',
            'soil': 'Clay loam with good water retention',
            'water': 'High (1500-2000mm)',
            'season': 'Kharif (June-July)',
            'harvest': 'October-November'
        },
        {
            'id': 3,
            'name': 'Cotton',
            'hindi_name': 'कपास',
            'soil': 'Black cotton soil',
            'water': 'Moderate (500-700mm)',
            'season': 'Kharif (April-June)',
            'harvest': 'October-December'
        }
    ]
    return render_template('crop_library.html', crops=crops)

@app.route('/crop-problem', methods=['GET', 'POST'])
@login_required
def crop_problem():
    """Crop problem detection"""
    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Mock AI analysis (in production, use ML model)
            analysis = {
                'problem': 'Possible fungal infection',
                'confidence': '85%',
                'guidance': [
                    'Remove affected leaves',
                    'Ensure proper drainage',
                    'Use neem-based organic spray',
                    'Maintain plant spacing for air circulation'
                ],
                'organic_remedies': [
                    'Neem oil spray (5ml per liter water)',
                    'Garlic-chili spray',
                    'Cow urine solution'
                ]
            }
            
            return jsonify(analysis)
    
    return render_template('crop_problem.html')

@app.route('/voice-assistant')
@login_required
def voice_assistant():
    """Voice AI assistant"""
    return render_template('voice_assistant.html')

@app.route('/ask-ai', methods=['POST'])
@login_required
def ask_ai():
    """Process voice/text queries"""
    data = request.json
    query = data.get('query', '').lower()
    
    # Mock responses based on keywords
    responses = {
        'fertilizer': 'Use well-decomposed compost or vermicompost. Jeevamrut can be applied weekly.',
        'pest': 'For organic pest control, use neem oil spray. Mix 5ml neem oil with 1 liter water.',
        'water': 'Water needs vary by crop. Most vegetables need watering every 2-3 days in summer.',
        'soil': 'Test soil pH. Most crops prefer 6.0-7.0 pH. Add organic matter to improve soil.',
        'weather': 'Check weather section for detailed forecast and alerts.',
        'scheme': 'Government schemes are listed in Schemes section with eligibility details.',
        'market': 'Check organic products section for local inputs.'
    }
    
    for keyword, response in responses.items():
        if keyword in query:
            return jsonify({
                'response': response,
                'voice': response,
                'source': 'FarmAssist AI'
            })
    
    return jsonify({
        'response': 'I can help with farming questions about crops, pests, weather, or government schemes.',
        'voice': 'I can help with farming questions about crops, pests, weather, or government schemes.',
        'source': 'FarmAssist AI'
    })

@app.route('/farmer-blog')
@login_required
def farmer_blog():
    """Farmer knowledge sharing"""
    return render_template('farmer_blog.html', posts=farmer_posts)

@app.route('/submit-post', methods=['POST'])
@login_required
def submit_post():
    """Submit farmer post/blog"""
    data = request.json
    post = {
        'id': len(farmer_posts) + 1,
        'user': session['user_id'],
        'title': data.get('title'),
        'content': data.get('content'),
        'type': data.get('type'),  # blog/video
        'crop': data.get('crop'),
        'timestamp': datetime.now().isoformat(),
        'likes': 0
    }
    farmer_posts.append(post)
    return jsonify({'success': True, 'post_id': post['id']})

@app.route('/government-schemes')
@login_required
def government_schemes():
    """Government schemes information"""
    schemes = [
        {
            'name': 'PM-KISAN',
            'hindi_name': 'पीएम-किसान',
            'eligibility': 'All farmer families',
            'benefit': '₹6000 per year',
            'link': 'https://pmkisan.gov.in'
        },
        {
            'name': 'Soil Health Card',
            'hindi_name': 'मृदा स्वास्थ्य कार्ड',
            'eligibility': 'All farmers',
            'benefit': 'Free soil testing',
            'link': 'https://soilhealth.dac.gov.in'
        }
    ]
    return render_template('schemes.html', schemes=schemes)

@app.route('/organic-market')
@login_required
def organic_market():
    """Organic products marketplace"""
    return render_template('market.html', products=products_list)

@app.route('/list-product', methods=['POST'])
@login_required
def list_product():
    """List organic product"""
    data = request.json
    product = {
        'id': len(products_list) + 1,
        'user': session['user_id'],
        'name': data.get('name'),
        'type': data.get('type'),
        'quantity': data.get('quantity'),
        'location': data.get('location'),
        'contact': data.get('contact'),
        'timestamp': datetime.now().isoformat()
    }
    products_list.append(product)
    return jsonify({'success': True, 'product_id': product['id']})

@app.route('/weather')
@login_required
def weather():
    """Weather information"""
    # Mock weather data (in production, use weather API)
    weather_data = {
        'current': {
            'temp': '32°C',
            'condition': 'Partly Cloudy',
            'humidity': '65%',
            'wind': '12 km/h',
            'rain': '20%'
        },
        'forecast': [
            {'day': 'Today', 'high': '32°C', 'low': '24°C', 'rain': '20%'},
            {'day': 'Tomorrow', 'high': '33°C', 'low': '25°C', 'rain': '10%'},
            {'day': 'Day 3', 'high': '34°C', 'low': '26°C', 'rain': '5%'}
        ]
    }
    return render_template('weather.html', weather=weather_data)

@app.route('/change-language', methods=['POST'])
def change_language():
    """Change interface language"""
    data = request.json
    language = data.get('language', 'hindi')
    session['language'] = language
    if 'user_id' in session:
        users_db[session['user_id']]['language'] = language
    return jsonify({'success': True, 'language': language})

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
