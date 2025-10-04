# YieldWise AI - Agricultural Platform
# Using ONLY Gemini API for all AI features

import os
import sqlite3
import uuid
import markdown
from flask import (
    Flask, render_template, request, jsonify, abort, redirect, url_for, flash,
    make_response, session
)
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime

# User Management & Security
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user, current_user, login_required
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# PDF & Image Handling
from weasyprint import HTML
import google.generativeai as genai
from PIL import Image

# Load environment variables
load_dotenv()

# Initialize Flask and extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- GEMINI API SETUP (ONLY AI PROVIDER) ---
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
gemini_model = None

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    print("✅ Gemini API configured successfully!")
else:
    print("⚠️  Warning: GEMINI_API_KEY not found. All AI features will be disabled.")
    print("   Please add GEMINI_API_KEY to your Replit Secrets.")

# --- DATABASE SETUP ---
def get_db_connection():
    conn = sqlite3.connect('yieldwise.db', check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Create tables
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, name TEXT NOT NULL);')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS farm_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
            location TEXT NOT NULL, country TEXT, currency TEXT, 
            plan_html TEXT NOT NULL, showcase_id TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    conn.execute('CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (plan_id) REFERENCES farm_plans (id));')
    conn.execute('CREATE TABLE IF NOT EXISTS diagnoses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, crop_type TEXT, report_html TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id));')
    conn.execute('CREATE TABLE IF NOT EXISTS diagnoses_chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, diagnosis_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (diagnosis_id) REFERENCES diagnoses (id));')
    
    # Create indexes for performance optimization
    conn.execute('CREATE INDEX IF NOT EXISTS idx_farm_plans_user_id ON farm_plans(user_id);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_farm_plans_created_at ON farm_plans(created_at DESC);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_farm_plans_showcase_id ON farm_plans(showcase_id);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_farm_plans_country ON farm_plans(country);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_plan_id ON chat_history(plan_id);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_diagnoses_user_id ON diagnoses(user_id);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_diagnoses_created_at ON diagnoses(created_at DESC);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_diagnoses_chat_history_diagnosis_id ON diagnoses_chat_history(diagnosis_id);')
    
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
@app.template_filter('dateformat')
def dateformat(value, format='%Y-%m-%d'):
    if value is None: return ""
    if isinstance(value, str):
        try: value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError): return value
    if hasattr(value, 'strftime'): return value.strftime(format)
    return value

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- USER CLASS & LOADER ---
class User(UserMixin):
    def __init__(self, id, email, password, name):
        self.id, self.email, self.password, self.name = id, email, password, name

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data: return User(user_data['id'], user_data['email'], user_data['password'], user_data['name'])
    return None

# --- CORE AI FUNCTIONS (ALL USE GEMINI) ---
def generate_farm_plan(location, space, budget, country, currency):
    """Generate farm business plan using Gemini AI"""
    try:
        if not gemini_model:
            return "<p class='error-message'>AI service is currently unavailable. Please contact support to enable Gemini API.</p>", []
        
        # Prioritize Nigerian crops for Nigerian users
        nigerian_priority = ""
        if country == "Nigeria" or "nigeria" in location.lower():
            nigerian_priority = """
**PRIORITY CROPS FOR NIGERIA (Consider these first):**
- Cassava (highest yield, multiple uses: garri, fufu, flour, starch)
- Maize/Corn (staple food, animal feed, fast-growing)
- Rice (high government support, import gap, strong demand)
- Yam (traditional staple, high value)
- Vegetables (tomatoes, peppers, onions - daily necessity, urban demand)
- Plantain (best long-term ROI, year-round production)
- Ginger (export value, medicinal demand)

**Nigerian Market Context:**
- Consider selling at major markets: Mile 12 (Lagos), Kano State markets, Dawanau International Grains Market, local daily markets
- Factor in Nigerian climate zones and seasonal patterns
- Use local farming practices combined with modern techniques
"""
            
        master_prompt = f"""You are an expert Nigerian agronomist and agricultural business consultant with deep knowledge of West African farming. Create a comprehensive farm business plan.

**Farm Details:**
- Location: {location}, {country}
- Available Space: {space}
- Budget: {currency} {budget}

{nigerian_priority}

**Instructions:**
Generate a detailed business plan in markdown format with these sections:

1. **🌱 Recommended Crop**
   - Choose ONE highly profitable, fast-growing crop ideal for {location}
   - Prioritize crops proven successful for Nigerian/African smallholder farmers
   - Explain why this crop is perfect for their location, budget, and local market demand

2. **💰 Budget Breakdown (in {currency})**
   - Create a detailed markdown table breaking down the EXACT budget
   - Include: seeds/seedlings, fertilizer (organic & chemical options), tools, water/irrigation, labor, transportation, miscellaneous
   - Show total = {budget}
   - Use realistic local market prices

3. **🗓️ 90-Day Action Plan**
   - Week 1-2: Land preparation and initial steps (consider Nigerian weather patterns)
   - Week 3-4: Planting and setup
   - Week 5-8: Growth and maintenance (pest management, fertilizing)
   - Week 9-12: Pre-harvest and harvest preparation

4. **📈 Realistic Earnings Projection (in {currency})**
   - Expected harvest amount (based on local yields)
   - Market price per unit (use current Nigerian market rates if applicable)
   - Total expected revenue
   - Net profit after all expenses
   - Profit margin percentage

5. **🛒 Market Strategy**
   - Best places to sell in {location} (local markets, cooperatives, processors)
   - For Nigeria: mention specific markets like Mile 12, Kano markets, or local daily markets
   - Pricing recommendations based on local competition
   - Marketing tips for African farmers (cooperative selling, direct-to-consumer)

6. **⚠️ Risk & Mitigation**
   - 2-3 major risks specific to {location}/Nigeria
   - Practical mitigation strategies (pest control, weather challenges, market fluctuation)
   - Consider Nigerian agricultural realities (power, water access, transportation)

---SUGGESTIONS---

**Suggested Follow-up Questions:**
1. What are the most common pests for this crop in {location} and how do I prevent them organically?
2. Can you give me a detailed week-by-week watering and fertilizer schedule for {location}'s climate?
3. What are the best local markets in {location} to sell my produce and what prices should I expect?"""

        response = gemini_model.generate_content(master_prompt)
        full_response = response.text
        
        if "---SUGGESTIONS---" in full_response:
            plan_text, suggestions_text = full_response.split("---SUGGESTIONS---", 1)
            suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and any(s.strip().startswith(str(i)) for i in range(1, 6))]
        else:
            plan_text, suggestions = full_response, []
        
        plan_html = markdown.markdown(plan_text, extensions=['tables'])
        return plan_html, suggestions[:3]
    except Exception as e:
        print(f"Error in generate_farm_plan: {e}")
        return "<p class='error-message'>Error: Could not generate the plan. Please try again.</p>", []

def diagnose_plant_issue(image_file, crop_type):
    """Diagnose plant disease using Gemini Vision AI"""
    try:
        if not gemini_model:
            return "Error", "<p class='error-message'>AI service is currently unavailable. Please contact support to enable Gemini API.</p>", []
            
        img = Image.open(image_file)
        prompt_parts = [
            f"""Analyze this {crop_type} plant image and provide a detailed diagnosis. You are an expert plant pathologist with extensive experience in Nigerian and West African crop diseases.

**Part 1: Diagnosis Report (Markdown Format)**
1. **Title:** A short, descriptive title for the issue
2. **Analysis:** Identify the likely pest or disease affecting this plant
   - Consider common pests/diseases prevalent in Nigeria and West Africa
   - Look for signs of nutrient deficiency common in tropical soils
3. **Symptoms:** Describe the symptoms visible in the image
4. **Organic Treatment:** Recommend organic/natural treatment methods
   - Prioritize locally available organic solutions (neem oil, wood ash, local herbs)
   - Traditional Nigerian farming remedies where applicable
5. **Chemical Treatment:** Recommend chemical treatment options if needed
   - Suggest products commonly available in Nigerian agro-dealers
   - Include both brand names and generic chemical names
   - Provide dosage and safety precautions
6. **Prevention:** Tips to prevent this issue in the future
   - Climate-specific advice for Nigerian weather conditions
   - Crop rotation practices suitable for African smallholder farms

**IMPORTANT:** Provide your best diagnosis even if the image quality is not perfect. Focus on practical solutions Nigerian farmers can implement immediately.

---SUGGESTIONS---

**Part 2: Follow-up Questions**
Suggest 3 relevant follow-up questions the user might want to ask.""",
            img,
        ]
        
        response = gemini_model.generate_content(prompt_parts)
        full_response = response.text
        
        if "---SUGGESTIONS---" in full_response:
            report_text, suggestions_text = full_response.split("---SUGGESTIONS---", 1)
            title_line = report_text.strip().split('\n')[0]
            title = title_line.replace('**Title:**', '').replace('#', '').strip() or f"Diagnosis for {crop_type}"
            suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and any(s.strip().startswith(str(i)) for i in range(1, 6))]
        else:
            report_text, title, suggestions = full_response, f"Diagnosis for {crop_type}", []
        
        report_html = markdown.markdown(report_text, extensions=['tables'])
        return title, report_html, suggestions[:3]
    except Exception as e:
        print(f"Error in diagnose_plant_issue: {e}")
        return "Error", "<p class='error-message'>Sorry, an error occurred while analyzing the image.</p>", []

# --- WEBSITE ROUTES ---
@app.route('/')
def home():
    if current_user.is_authenticated: 
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, email, password = request.form.get('name'), request.form.get('email'), request.form.get('password')
        if not all([name, email, password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user:
            flash('Email address already exists.', 'error')
            conn.close()
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_password))
        new_user_id = cursor.lastrowid
        conn.commit()
        
        if 'guest_plan' in session:
            guest_plan = session['guest_plan']
            conn.execute(
                'INSERT INTO farm_plans (user_id, location, country, currency, plan_html) VALUES (?, ?, ?, ?, ?)',
                (new_user_id, guest_plan['location'], guest_plan['country'], guest_plan['currency'], guest_plan['plan_html'])
            )
            conn.commit()
            session.pop('guest_plan', None)
        
        conn.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form.get('email'), request.form.get('password')
        if not email or not password:
            flash('Both email and password are required.', 'error')
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['id'], user_data['email'], user_data['password'], user_data['name'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    plans = conn.execute('SELECT * FROM farm_plans WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,)).fetchall()
    diagnoses = conn.execute('SELECT * FROM diagnoses WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,)).fetchall()
    conn.close()
    return render_template('dashboard.html', plans=plans, diagnoses=diagnoses)

@app.route('/diagnostician', methods=['GET'])
@login_required
def diagnostician():
    conn = get_db_connection()
    plans = conn.execute('SELECT * FROM farm_plans WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,)).fetchall()
    diagnoses = conn.execute('SELECT * FROM diagnoses WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,)).fetchall()
    conn.close()
    return render_template('diagnostician.html', plans=plans, diagnoses=diagnoses)

@app.route('/analytics')
@login_required
def analytics():
    conn = get_db_connection()
    plans = conn.execute('SELECT * FROM farm_plans WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,)).fetchall()
    diagnoses = conn.execute('SELECT * FROM diagnoses WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,)).fetchall()
    conn.close()
    plans_data = [dict(p) for p in plans]
    return render_template('analytics.html', plans=plans, diagnoses=diagnoses, plans_data=plans_data)

@app.route('/resources')
def resources():
    """Resource calculator - available to all users"""
    return render_template('resources.html')

@app.route('/knowledge_base')
def knowledge_base():
    """Knowledge Base - available to all users (guests and logged in)"""
    user_location = None
    user_name = None
    
    if current_user.is_authenticated:
        user_name = current_user.name
        # Get user's most recent location from their plans
        conn = get_db_connection()
        recent_plan = conn.execute(
            'SELECT location, country FROM farm_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
            (current_user.id,)
        ).fetchone()
        conn.close()
        
        if recent_plan:
            user_location = f"{recent_plan['location']}, {recent_plan['country']}"
    
    return render_template('knowledge_base.html', user_location=user_location, user_name=user_name)

@app.route('/community_showcase')
def community_showcase():
    """Community showcase - available to all users"""
    conn = get_db_connection()
    public_showcases = conn.execute('''
        SELECT p.*, u.name as user_name 
        FROM farm_plans p 
        JOIN users u ON p.user_id = u.id 
        WHERE p.showcase_id IS NOT NULL 
        ORDER BY p.created_at DESC 
        LIMIT 50
    ''').fetchall()
    conn.close()
    return render_template('community_showcase.html', public_showcases=public_showcases)

@app.route('/showcase/<showcase_id>')
def showcase(showcase_id):
    """View public showcase"""
    conn = get_db_connection()
    plan = conn.execute(
        'SELECT p.*, u.name as user_name FROM farm_plans p JOIN users u ON p.user_id = u.id WHERE showcase_id = ?',
        (showcase_id,)
    ).fetchone()
    conn.close()
    if plan is None: 
        abort(404)
    return render_template('showcase.html', plan=plan)

@app.route('/download_pdf/<int:plan_id>')
@login_required
def download_pdf(plan_id):
    """Download plan as PDF"""
    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    conn.close()
    
    if plan is None: 
        return abort(404)
    
    html_for_pdf = f"""
    <html><head><style>
        body {{ font-family: sans-serif; font-size: 12px; }} 
        h1, h2, h3 {{ color: #2c6b4f; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }} 
        th, td {{ border: 1px solid #ddd; text-align: left; padding: 8px; }}
        th {{ background-color: #f2f2f2; }} 
        .footer {{ text-align: center; font-size: 10px; color: #777; margin-top: 2em; }}
    </style></head><body>
        <h1>Farm Plan for {plan['location']}</h1>
        <p><strong>Prepared for:</strong> {current_user.name}</p>
        <hr>
        {plan['plan_html']}
        <div class="footer"><p>Generated by YieldWise AI</p></div>
    </body></html>
    """
    
    pdf_bytes = HTML(string=html_for_pdf).write_pdf()
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=YieldWise_Plan_{plan["id"]}.pdf'
    return response

# --- API ROUTES ---
@app.route('/api/generate', methods=['POST'])
@limiter.limit("3 per day", key_func=lambda: current_user.id if current_user.is_authenticated else get_remote_address)
def api_generate():
    """Generate farm plan using Gemini AI"""
    data = request.get_json()
    
    if not all(k in data for k in ['location', 'space', 'budget', 'country', 'currency']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        budget = float(data['budget'])
        if budget <= 0:
            return jsonify({'error': 'Budget must be a positive number'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid budget format'}), 400
    
    if len(data['location'].strip()) < 2:
        return jsonify({'error': 'Location must be at least 2 characters'}), 400
    
    if len(data['space'].strip()) < 5:
        return jsonify({'error': 'Please provide more details about your available space'}), 400
    
    plan_html, suggestions = generate_farm_plan(
        data['location'], data['space'], data['budget'], data['country'], data['currency']
    )
    
    if "error-message" in plan_html: 
        return jsonify({'error': plan_html}), 500
    
    # Handle guest users
    if not current_user.is_authenticated:
        if session.get('free_plan_used'):
            return jsonify({
                'error': '<p class="error-message">Free plan already used. Please register to continue using YieldWise AI!</p>'
            }), 429
        
        session['free_plan_used'] = True
        session['guest_plan'] = {
            'plan_html': plan_html,
            'location': data['location'],
            'country': data['country'],
            'currency': data['currency']
        }
        return jsonify({'plan': plan_html, 'plan_id': None, 'suggestions': suggestions})
    
    # Save for logged-in users
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO farm_plans (user_id, location, country, currency, plan_html) VALUES (?, ?, ?, ?, ?)',
        (current_user.id, data['location'], data['country'], data['currency'], plan_html)
    )
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'plan': plan_html, 'plan_id': plan_id, 'suggestions': suggestions})

@app.route('/api/diagnose', methods=['POST'])
@login_required
@limiter.limit("3 per day")
def api_diagnose():
    """Diagnose plant disease using Gemini Vision AI"""
    if 'plant_image' not in request.files or 'crop_type' not in request.form:
        return jsonify({'error': 'Missing file or crop type'}), 400
    
    file, crop_type = request.files['plant_image'], request.form['crop_type']
    
    if file.filename == '' or not crop_type:
        return jsonify({'error': 'No selected file or crop type'}), 400
    
    if len(crop_type.strip()) < 2:
        return jsonify({'error': 'Crop type must be at least 2 characters'}), 400
    
    # Check file size (5MB limit)
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 5 * 1024 * 1024:
        return jsonify({'error': 'Image size must be less than 5MB'}), 400
    
    if file and allowed_file(file.filename):
        title, report_html, suggestions = diagnose_plant_issue(file, crop_type)
        
        if "Error" in title: 
            return jsonify({'error': report_html}), 500
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO diagnoses (user_id, title, crop_type, report_html) VALUES (?, ?, ?, ?)',
            (current_user.id, title, crop_type, report_html)
        )
        diagnosis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'title': title,
            'diagnosis': report_html,
            'suggestions': suggestions,
            'diagnosis_id': diagnosis_id
        })
    else:
        return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, or JPEG'}), 400

@app.route('/api/follow_up', methods=['POST'])
@login_required
def api_follow_up():
    """Follow-up chat for farm plans using Gemini AI"""
    data = request.get_json()
    plan_id, question = data.get('plan_id'), data.get('question')
    
    if not all([plan_id, question]): 
        return jsonify({'error': 'Missing data'}), 400
    
    if len(question.strip()) < 3:
        return jsonify({'error': 'Question must be at least 3 characters'}), 400
    
    conn = get_db_connection()
    plan = conn.execute(
        'SELECT * FROM farm_plans WHERE id = ? AND user_id = ?',
        (plan_id, current_user.id)
    ).fetchone()
    
    if not plan:
        conn.close()
        return jsonify({'error': 'Plan not found or access denied'}), 404
    
    history = conn.execute(
        'SELECT role, content FROM chat_history WHERE plan_id = ? ORDER BY created_at ASC',
        (plan_id,)
    ).fetchall()
    
    conn.execute('INSERT INTO chat_history (plan_id, role, content) VALUES (?, ?, ?)', (plan_id, 'user', question))
    conn.commit()
    
    try:
        if not gemini_model:
            conn.close()
            return jsonify({'error': 'AI service is currently unavailable.'}), 503
        
        # Build conversation context
        conversation = f"Initial Farm Plan:\n{plan['plan_html']}\n\n"
        for message in history:
            conversation += f"{message['role'].capitalize()}: {message['content']}\n"
        conversation += f"\nUser's new question: {question}\n\nProvide a helpful, practical answer:"
        
        response = gemini_model.generate_content(conversation)
        answer = response.text
        
        conn.execute('INSERT INTO chat_history (plan_id, role, content) VALUES (?, ?, ?)', (plan_id, 'assistant', answer))
        conn.commit()
        conn.close()
        
        return jsonify({'answer': markdown.markdown(answer)})
    except Exception as e:
        conn.close()
        print(f"Error in follow_up: {e}")
        return jsonify({'error': 'Sorry, an error occurred.'}), 500

@app.route('/api/diagnose_follow_up', methods=['POST'])
@login_required
def api_diagnose_follow_up():
    """Follow-up chat for diagnoses using Gemini AI"""
    data = request.get_json()
    diagnosis_id, question = data.get('diagnosis_id'), data.get('question')
    
    if not all([diagnosis_id, question]): 
        return jsonify({'error': 'Missing data'}), 400
    
    if len(question.strip()) < 3:
        return jsonify({'error': 'Question must be at least 3 characters'}), 400
    
    conn = get_db_connection()
    diagnosis = conn.execute(
        'SELECT * FROM diagnoses WHERE id = ? AND user_id = ?',
        (diagnosis_id, current_user.id)
    ).fetchone()
    
    if not diagnosis:
        conn.close()
        return jsonify({'error': 'Diagnosis not found or access denied'}), 404
    
    history = conn.execute(
        'SELECT role, content FROM diagnoses_chat_history WHERE diagnosis_id = ? ORDER BY created_at ASC',
        (diagnosis_id,)
    ).fetchall()
    
    conn.execute('INSERT INTO diagnoses_chat_history (diagnosis_id, role, content) VALUES (?, ?, ?)', (diagnosis_id, 'user', question))
    conn.commit()
    
    try:
        if not gemini_model:
            conn.close()
            return jsonify({'error': 'AI service is currently unavailable.'}), 503
        
        # Build conversation context
        conversation = f"Initial Diagnosis:\n{diagnosis['report_html']}\n\n"
        for message in history:
            conversation += f"{message['role'].capitalize()}: {message['content']}\n"
        conversation += f"\nUser's new question: {question}\n\nProvide a helpful answer:"
        
        response = gemini_model.generate_content(conversation)
        answer = response.text
        
        conn.execute('INSERT INTO diagnoses_chat_history (diagnosis_id, role, content) VALUES (?, ?, ?)', (diagnosis_id, 'assistant', answer))
        conn.commit()
        conn.close()
        
        return jsonify({'answer': markdown.markdown(answer)})
    except Exception as e:
        conn.close()
        print(f"Error in diagnose_follow_up: {e}")
        return jsonify({'error': 'Sorry, an error occurred.'}), 500

@app.route('/api/knowledge_query', methods=['POST'])
def api_knowledge_query():
    """Answer farming questions using Gemini AI - Available to ALL users"""
    data = request.get_json()
    query = data.get('query') or data.get('question')
    
    if not query or len(query.strip()) < 3:
        return jsonify({'error': 'Question must be at least 3 characters'}), 400
    
    try:
        if not gemini_model:
            return jsonify({'error': 'AI service is currently unavailable.'}), 503
        
        # Get user context if available
        user_context = ""
        if current_user.is_authenticated:
            conn = get_db_connection()
            recent_plan = conn.execute(
                'SELECT location, country FROM farm_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
                (current_user.id,)
            ).fetchone()
            conn.close()
            
            if recent_plan:
                user_context = f"\n\nUser is located in: {recent_plan['location']}, {recent_plan['country']}"
        
        prompt = f"""You are an expert agricultural advisor with decades of farming experience in Nigeria and West Africa. Answer this farming question with practical, actionable advice tailored for African smallholder farmers.

Question: {query}{user_context}

Provide a clear, helpful answer in 2-4 paragraphs. Focus on:
- Practical advice Nigerian/African farmers can implement immediately
- Location-specific recommendations (Nigerian climate zones, soil types, seasons)
- Cost-effective solutions using locally available materials and resources
- Both traditional African farming wisdom and modern agricultural techniques
- Reference Nigerian crops (cassava, maize, rice, yam, vegetables, plantain) when relevant
- Consider Nigerian agricultural realities (weather patterns, market access, smallholder constraints)

Keep it conversational and easy to understand. Use simple language suitable for farmers with varying education levels."""
        
        response = gemini_model.generate_content(prompt)
        answer_html = markdown.markdown(response.text)
        
        return jsonify({'answer': answer_html, 'response': answer_html})
    except Exception as e:
        print(f"Error in knowledge_query: {e}")
        return jsonify({'error': 'Sorry, an error occurred. Please try again.'}), 500

# --- UTILITY API ROUTES ---
@app.route('/api/create_showcase', methods=['POST'])
@login_required
def api_create_showcase():
    """Create public showcase for a plan"""
    data = request.get_json()
    plan_id = data.get('plan_id')
    
    if not plan_id: 
        return jsonify({'error': 'Plan ID is required'}), 400
    
    conn = get_db_connection()
    plan = conn.execute(
        'SELECT * FROM farm_plans WHERE id = ? AND user_id = ?',
        (plan_id, current_user.id)
    ).fetchone()
    
    if not plan:
        conn.close()
        return jsonify({'error': 'Plan not found or access denied'}), 404
    
    existing = conn.execute(
        'SELECT showcase_id FROM farm_plans WHERE id = ? AND user_id = ?',
        (plan_id, current_user.id)
    ).fetchone()
    
    if existing and existing['showcase_id']:
        conn.close()
        return jsonify({'showcase_id': existing['showcase_id']})
    
    showcase_id = str(uuid.uuid4())
    conn.execute(
        'UPDATE farm_plans SET showcase_id = ? WHERE id = ? AND user_id = ?',
        (showcase_id, plan_id, current_user.id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'showcase_id': showcase_id})

@app.route('/api/get_plan/<int:plan_id>', methods=['GET'])
@login_required
def get_plan(plan_id):
    """Get plan details with chat history"""
    conn = get_db_connection()
    plan = conn.execute(
        'SELECT * FROM farm_plans WHERE id = ? AND user_id = ?',
        (plan_id, current_user.id)
    ).fetchone()
    chat_history = conn.execute(
        'SELECT role, content FROM chat_history WHERE plan_id = ? ORDER BY created_at ASC',
        (plan_id,)
    ).fetchall()
    conn.close()
    
    if plan is None: 
        return jsonify({'error': 'Plan not found'}), 404
    
    return jsonify({
        'plan': dict(plan),
        'chat_history': [dict(row) for row in chat_history]
    })

@app.route('/api/delete_plan/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    """Delete a farm plan"""
    conn = get_db_connection()
    plan = conn.execute(
        'SELECT * FROM farm_plans WHERE id = ? AND user_id = ?',
        (plan_id, current_user.id)
    ).fetchone()
    
    if not plan:
        conn.close()
        return jsonify({'error': 'Plan not found or access denied'}), 404
    
    conn.execute('DELETE FROM chat_history WHERE plan_id = ?', (plan_id,))
    conn.execute('DELETE FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/get_diagnosis/<int:diagnosis_id>', methods=['GET'])
@login_required
def get_diagnosis(diagnosis_id):
    """Get diagnosis details with chat history"""
    conn = get_db_connection()
    diagnosis = conn.execute(
        'SELECT * FROM diagnoses WHERE id = ? AND user_id = ?',
        (diagnosis_id, current_user.id)
    ).fetchone()
    chat_history = conn.execute(
        'SELECT role, content FROM diagnoses_chat_history WHERE diagnosis_id = ? ORDER BY created_at ASC',
        (diagnosis_id,)
    ).fetchall()
    conn.close()
    
    if diagnosis is None: 
        return jsonify({'error': 'Diagnosis not found'}), 404
    
    return jsonify({
        'diagnosis': dict(diagnosis),
        'chat_history': [dict(row) for row in chat_history]
    })
    
@app.route('/api/delete_diagnosis/<int:diagnosis_id>', methods=['DELETE'])
@login_required
def delete_diagnosis(diagnosis_id):
    """Delete a diagnosis"""
    conn = get_db_connection()
    diagnosis = conn.execute(
        'SELECT * FROM diagnoses WHERE id = ? AND user_id = ?',
        (diagnosis_id, current_user.id)
    ).fetchone()
    
    if not diagnosis:
        conn.close()
        return jsonify({'error': 'Diagnosis not found or access denied'}), 404
    
    conn.execute('DELETE FROM diagnoses_chat_history WHERE diagnosis_id = ?', (diagnosis_id,))
    conn.execute('DELETE FROM diagnoses WHERE id = ? AND user_id = ?', (diagnosis_id, current_user.id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/search_plans', methods=['GET'])
@login_required
def api_search_plans():
    """Search user's plans"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'plans': []})
    
    conn = get_db_connection()
    plans = conn.execute(
        'SELECT * FROM farm_plans WHERE user_id = ? AND location LIKE ? ORDER BY created_at DESC LIMIT 10',
        (current_user.id, f'%{query}%')
    ).fetchall()
    conn.close()
    
    return jsonify({'plans': [dict(plan) for plan in plans]})

@app.route('/api/export_data', methods=['GET'])
@login_required
def api_export_data():
    """Export user's data as JSON"""
    conn = get_db_connection()
    plans = conn.execute('SELECT * FROM farm_plans WHERE user_id = ?', (current_user.id,)).fetchall()
    diagnoses = conn.execute('SELECT * FROM diagnoses WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    
    export_data = {
        'user': {
            'name': current_user.name,
            'email': current_user.email
        },
        'plans': [dict(plan) for plan in plans],
        'diagnoses': [dict(diagnosis) for diagnosis in diagnoses],
        'exported_at': datetime.now().isoformat()
    }
    
    response = make_response(jsonify(export_data))
    response.headers['Content-Disposition'] = f'attachment; filename=yieldwise_data_{current_user.id}.json'
    return response

@app.route('/api/health', methods=['HEAD', 'GET'])
def health_check():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'gemini_api': 'available' if gemini_model else 'unavailable',
            'database': 'available'
        },
        'version': '3.0.0',
        'features': ['farm_planning', 'plant_diagnosis', 'knowledge_base', 'chat_support', 'pdf_export']
    })

# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
