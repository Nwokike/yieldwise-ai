# 1. Import necessary libraries
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

# Database adapters for environment-based switching
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from .env file
load_dotenv()

# 2. Initialize Flask and extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- API KEY & AI CLIENT SETUP ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Gemini 2.5 Flash for all AI features
gemini_model = None

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(
        'gemini-2.0-flash-exp',
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
    )
    print("✓ Gemini 2.5 Flash initialized successfully")
else:
    print("Warning: GOOGLE_API_KEY not found. AI features will be disabled.")

# --- DATABASE SETUP ---
DATABASE_ENV = os.getenv('DATABASE_ENV', 'development')
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Get database connection based on environment"""
    if DATABASE_ENV == 'production' and DATABASE_URL:
        # PostgreSQL for production (Neon)
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        # SQLite for development
        conn = sqlite3.connect('yieldwise.db', check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, name TEXT NOT NULL);')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS farm_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
            location TEXT NOT NULL, country TEXT, currency TEXT, 
            plan_html TEXT NOT NULL, showcase_id TEXT, 
            is_promoted INTEGER DEFAULT 0, -- New monetization field
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    conn.execute('CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (plan_id) REFERENCES farm_plans (id));')
    conn.execute('CREATE TABLE IF NOT EXISTS diagnoses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, crop_type TEXT, report_html TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id));')
    conn.execute('CREATE TABLE IF NOT EXISTS diagnoses_chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, diagnosis_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (diagnosis_id) REFERENCES diagnoses (id));')
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

# --- CORE AI FUNCTIONS ---
def generate_farm_plan(location, space, budget, country, currency):
    """Generate farm plan using Gemini 2.5 Flash"""
    try:
        if not gemini_model:
            return f"<p class='error-message'>Farm planning service is currently unavailable. Please configure your Gemini API key.</p>", []
            
        master_prompt = f"""
        **Instruction:** You are an expert agronomist AI. Using your knowledge, generate a comprehensive yet concise business plan in markdown format, followed by three suggested follow-up questions separated by "---SUGGESTIONS---".

        **Business Plan Sections for a user in {location}, {country} with a budget of {currency} {budget} for a {space} space:**
        
        1.  **🌱 Recommended Crop Selection:** 
            - Choose ONE highly profitable, fast-growing crop ideal for {location}
            - Explain why this crop is perfect for their specific location and climate
            - Include expected yield per square meter
        
        2.  **💰 Budget Breakdown (in {currency}):** 
            - Create a detailed markdown table showing exact budget allocation
            - Include: seeds/seedlings, soil/fertilizer, tools, water, pest control, contingency
            - Total must equal {currency} {budget}
        
        3.  **🗓️ 90-Day Action Plan:** 
            - Week 1-4: Preparation and planting
            - Week 5-8: Growth and maintenance
            - Week 9-12: Pre-harvest and harvest
            - Week 13+: Marketing and sales
        
        4.  **📈 Realistic Earnings Projection:** 
            - Estimated harvest quantity
            - Local market price per unit in {currency}
            - Total expected revenue
            - Net profit after costs
        
        5.  **🛒 Market Strategy:** 
            - Best local markets in {location}
            - Online selling options
            - Bulk buyer opportunities
        
        6.  **⚠️ Risk Management:** 
            - Top 3 risks for this crop in {location}
            - Practical mitigation strategies for each
        
        7.  **🎯 Success Tips:**
            - 3 key tips for maximizing yield
            - Local resources and contacts
        
        ---SUGGESTIONS---
        
        **Suggested Follow-up Questions:**
        1. What are the most common pests for [Crop Name] in {location} and how do I prevent them organically?
        2. Can you give me a detailed week-by-week guide for the first month?
        3. Which specific markets in {location} pay the best prices for {currency}?
        """
        
        response = gemini_model.generate_content(master_prompt)
        full_response = response.text
        
        if "---SUGGESTIONS---" in full_response:
            plan_text, suggestions_text = full_response.split("---SUGGESTIONS---", 1)
            suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and s.strip().startswith(('1', '2', '3', '- '))]
        else:
            plan_text, suggestions = full_response, []
        
        plan_html = markdown.markdown(plan_text, extensions=['tables'])
        return plan_html, suggestions
        
    except Exception as e:
        print(f"An error occurred during plan generation: {e}")
        return f"<p class='error-message'>Error: Could not generate the plan. The AI service may be temporarily unavailable.</p>", []

def diagnose_plant_issue(image_file, crop_type):
    """Diagnose plant issues using Gemini 2.5 Flash with vision capabilities"""
    try:
        if not gemini_model:
            return "Error", f"<p class='error-message'>Plant diagnosis service is currently unavailable. Please configure your Gemini API key.</p>", []
            
        img = Image.open(image_file)
        prompt = f"""
        Analyze the attached image of a {crop_type} plant/leaf. Your response must be in two parts, separated by "---SUGGESTIONS---".
        
        **Part 1: Comprehensive Diagnosis Report (Markdown Format)**
        
        1. **Title:** Create a clear, specific diagnostic title (e.g., "Early Blight Detected on Tomato Plant")
        
        2. **Visual Analysis:** 
           - Describe what you observe in the image
           - Identify specific symptoms (discoloration, spots, wilting, etc.)
        
        3. **Diagnosis:** 
           - Identify the most likely disease, pest, or issue
           - Confidence level of diagnosis
           - Alternative possibilities if uncertain
        
        4. **Cause & Impact:**
           - What causes this condition
           - How it affects plant health and yield
           - Progression if left untreated
        
        5. **Organic Treatment Solutions:**
           - 2-3 organic/natural remedies with specific instructions
           - Preventive measures
           - Expected timeline for results
        
        6. **Chemical Treatment Options:**
           - Recommended chemical treatments (product types/active ingredients)
           - Application guidelines
           - Safety precautions
        
        7. **Prevention Strategy:**
           - How to prevent recurrence
           - Best practices for plant health
        
        **IMPORTANT: Provide confident diagnosis based on visible symptoms. Be specific and actionable.**
        
        ---SUGGESTIONS---
        
        **Part 2: Suggested Follow-up Questions**
        Provide 3 insightful questions the farmer might ask based on this diagnosis.
        **IMPORTANT: Questions must be answerable with text only. No image/video requests.**
        """
        
        response = gemini_model.generate_content([prompt, img])
        full_response = response.text
        
        if "---SUGGESTIONS---" in full_response:
            report_text, suggestions_text = full_response.split("---SUGGESTIONS---", 1)
            title_line = report_text.strip().split('\n')[0]
            title = title_line.replace('**Title:**', '').replace('#', '').strip() if '**Title:**' in title_line or title_line.startswith('#') else f"Diagnosis for {crop_type}"
            suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and s.strip().startswith(('1', '2', '3', '- '))]
        else:
            report_text, title, suggestions = full_response, f"Plant Health Analysis: {crop_type}", []
        
        report_html = markdown.markdown(report_text, extensions=['tables'])
        return title, report_html, suggestions
        
    except Exception as e:
        print(f"An error occurred during Gemini image analysis: {e}")
        return "Error", "<p class='error-message'>Sorry, an error occurred while analyzing the image.</p>", []

# --- WEBSITE ROUTES ---
@app.route('/')
def home():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    # Enhanced home page with service status
    services_status = {
        'farm_planning': gemini_model is not None,
        'plant_diagnosis': gemini_model is not None
    }
    return render_template('index.html', services_status=services_status)

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

@app.route('/showcase/<showcase_id>')
def showcase(showcase_id):
    conn = get_db_connection()
    plan = conn.execute('SELECT p.*, u.name as user_name FROM farm_plans p JOIN users u ON p.user_id = u.id WHERE showcase_id = ?', (showcase_id,)).fetchone()
    conn.close()
    if plan is None: abort(404)
    return render_template('showcase.html', plan=plan)

@app.route('/download_pdf/<int:plan_id>')
@login_required
def download_pdf(plan_id):
    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    conn.close()
    if plan is None: return abort(404)
    html_for_pdf = f"""
    <html><head><style>
        body {{ font-family: sans-serif; font-size: 12px; }} h1, h2, h3 {{ color: #2c6b4f; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 1em; margin-bottom: 1em; }} 
        th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
        th {{ background-color: #f2f2f2; }} 
        .footer {{ text-align: center; font-size: 10px; color: #777; position: fixed; bottom: 0; width: 100%; }}
    </style></head><body>
        <h1>Farm Plan for {plan['location']}</h1> <p><strong>Prepared for:</strong> {current_user.name}</p> <hr>
        {plan['plan_html']}
        <div class="footer"><p>Generated by YieldWise AI | A project by Onyeka Nwokike</p></div>
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
    data = request.get_json()
    if not all(k in data for k in ['location', 'space', 'budget', 'country', 'currency']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Enhanced validation
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
    
    plan_html, suggestions = generate_farm_plan(data['location'], data['space'], data['budget'], data['country'], data['currency'])
    if "Error:" in plan_html: return jsonify({'error': plan_html}), 500
    if not current_user.is_authenticated:
        if session.get('free_plan_used'):
            return jsonify({'error': '<p class="error-message">Free plan already used. Please register to continue.</p>'}), 429
        session['free_plan_used'] = True
        session['guest_plan'] = {'plan_html': plan_html, 'location': data['location'], 'country': data['country'], 'currency': data['currency']}
        return jsonify({'plan': plan_html, 'plan_id': None, 'suggestions': suggestions})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO farm_plans (user_id, location, country, currency, plan_html) VALUES (?, ?, ?, ?, ?)', (current_user.id, data['location'], data['country'], data['currency'], plan_html))
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'plan': plan_html, 'plan_id': plan_id, 'suggestions': suggestions})

@app.route('/api/diagnose', methods=['POST'])
@login_required
@limiter.limit("3 per day")
def api_diagnose():
    if 'plant_image' not in request.files or 'crop_type' not in request.form:
        return jsonify({'error': 'Missing file or crop type'}), 400
    file, crop_type = request.files['plant_image'], request.form['crop_type']
    if file.filename == '' or not crop_type:
        return jsonify({'error': 'No selected file or crop type'}), 400
    
    # Enhanced validation
    if len(crop_type.strip()) < 2:
        return jsonify({'error': 'Crop type must be at least 2 characters'}), 400
    
    # Check file size (5MB limit)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return jsonify({'error': 'Image size must be less than 5MB'}), 400
    
    if file and allowed_file(file.filename):
        title, report_html, suggestions = diagnose_plant_issue(file, crop_type)
        if "Error" in title: return jsonify({'error': report_html}), 500
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO diagnoses (user_id, title, crop_type, report_html) VALUES (?, ?, ?, ?)',(current_user.id, title, crop_type, report_html))
        diagnosis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'title': title, 'diagnosis': report_html, 'suggestions': suggestions, 'diagnosis_id': diagnosis_id})
    else:
        return jsonify({'error': 'Invalid file type.'}), 400

@app.route('/api/create_showcase', methods=['POST'])
@login_required
def api_create_showcase():
    data = request.get_json()
    plan_id = data.get('plan_id')
    if not plan_id: return jsonify({'error': 'Plan ID is required'}), 400
    
    # Validate plan ownership
    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    if not plan:
        conn.close()
        return jsonify({'error': 'Plan not found or access denied'}), 404
    
    existing = conn.execute('SELECT showcase_id FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    if existing and existing['showcase_id']:
        conn.close()
        return jsonify({'showcase_id': existing['showcase_id']})
    showcase_id = str(uuid.uuid4())
    conn.execute('UPDATE farm_plans SET showcase_id = ? WHERE id = ? AND user_id = ?', (showcase_id, plan_id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'showcase_id': showcase_id})

@app.route('/api/search_plans', methods=['GET'])
@login_required
def api_search_plans():
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
    
    # Get user's plans
    plans = conn.execute('SELECT * FROM farm_plans WHERE user_id = ?', (current_user.id,)).fetchall()
    
    # Get user's diagnoses
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

@app.route('/api/get_plan/<int:plan_id>', methods=['GET'])
@login_required
def get_plan(plan_id):
    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    chat_history = conn.execute('SELECT role, content FROM chat_history WHERE plan_id = ? ORDER BY created_at ASC', (plan_id,)).fetchall()
    conn.close()
    if plan is None: return jsonify({'error': 'Plan not found'}), 404
    return jsonify({'plan': dict(plan), 'chat_history': [dict(row) for row in chat_history]})

@app.route('/api/delete_plan/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    conn = get_db_connection()
    # Verify ownership before deletion
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    if not plan:
        conn.close()
        return jsonify({'error': 'Plan not found or access denied'}), 404
    
    conn.execute('DELETE FROM chat_history WHERE plan_id = ?', (plan_id,))
    conn.execute('DELETE FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/follow_up', methods=['POST'])
@login_required
def api_follow_up():
    data = request.get_json()
    plan_id, question = data.get('plan_id'), data.get('question')
    if not all([plan_id, question]): return jsonify({'error': 'Missing data'}), 400
    
    # Validate question length
    if len(question.strip()) < 3:
        return jsonify({'error': 'Question must be at least 3 characters'}), 400
    
    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    if not plan:
        conn.close()
        return jsonify({'error': 'Plan not found or access denied'}), 404
    
    history = conn.execute('SELECT role, content FROM chat_history WHERE plan_id = ? ORDER BY created_at ASC', (plan_id,)).fetchall()
    conn.execute('INSERT INTO chat_history (plan_id, role, content) VALUES (?, ?, ?)', (plan_id, 'user', question))
    conn.commit()
    conversation_history = "Initial Farm Plan:\n" + plan['plan_html'] + "\n\n"
    for message in history:
        conversation_history += f"{message['role'].capitalize()}: {message['content']}\n"
    conversation_history += f"User: {question}\n\nAs an expert agronomist, provide a detailed, helpful answer to the user's question about their farm plan."
    try:
        if not gemini_model:
            conn.close()
            return jsonify({'error': 'Farm planning service is currently unavailable. Please configure your Gemini API key.'}), 503
        response = gemini_model.generate_content(conversation_history)
        answer = response.text
        conn.execute('INSERT INTO chat_history (plan_id, role, content) VALUES (?, ?, ?)', (plan_id, 'assistant', answer))
        conn.commit()
        conn.close()
        return jsonify({'answer': markdown.markdown(answer)})
    except Exception as e:
        conn.close()
        print(f"An error occurred in follow-up: {e}")
        return jsonify({'error': 'Sorry, an error occurred.'}), 500

@app.route('/api/get_diagnosis/<int:diagnosis_id>', methods=['GET'])
@login_required
def get_diagnosis(diagnosis_id):
    conn = get_db_connection()
    diagnosis = conn.execute('SELECT * FROM diagnoses WHERE id = ? AND user_id = ?', (diagnosis_id, current_user.id)).fetchone()
    chat_history = conn.execute('SELECT role, content FROM diagnoses_chat_history WHERE diagnosis_id = ? ORDER BY created_at ASC', (diagnosis_id,)).fetchall()
    conn.close()
    if diagnosis is None: return jsonify({'error': 'Diagnosis not found'}), 404
    return jsonify({'diagnosis': dict(diagnosis), 'chat_history': [dict(row) for row in chat_history]})
    
@app.route('/api/delete_diagnosis/<int:diagnosis_id>', methods=['DELETE'])
@login_required
def delete_diagnosis(diagnosis_id):
    conn = get_db_connection()
    # Verify ownership before deletion
    diagnosis = conn.execute('SELECT * FROM diagnoses WHERE id = ? AND user_id = ?', (diagnosis_id, current_user.id)).fetchone()
    if not diagnosis:
        conn.close()
        return jsonify({'error': 'Diagnosis not found or access denied'}), 404
    
    conn.execute('DELETE FROM diagnoses_chat_history WHERE diagnosis_id = ?', (diagnosis_id,))
    conn.execute('DELETE FROM diagnoses WHERE id = ? AND user_id = ?', (diagnosis_id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/diagnose_follow_up', methods=['POST'])
@login_required
def api_diagnose_follow_up():
    data = request.get_json()
    diagnosis_id, question = data.get('diagnosis_id'), data.get('question')
    if not all([diagnosis_id, question]): return jsonify({'error': 'Missing data'}), 400
    
    # Validate question length
    if len(question.strip()) < 3:
        return jsonify({'error': 'Question must be at least 3 characters'}), 400
    
    conn = get_db_connection()
    diagnosis = conn.execute('SELECT * FROM diagnoses WHERE id = ? AND user_id = ?', (diagnosis_id, current_user.id)).fetchone()
    if not diagnosis:
        conn.close()
        return jsonify({'error': 'Diagnosis not found or access denied'}), 404
    
    history = conn.execute('SELECT role, content FROM diagnoses_chat_history WHERE diagnosis_id = ? ORDER BY created_at ASC', (diagnosis_id,)).fetchall()
    conn.execute('INSERT INTO diagnoses_chat_history (diagnosis_id, role, content) VALUES (?, ?, ?)', (diagnosis_id, 'user', question))
    conn.commit()
    conversation_for_gemini = "Initial Diagnosis Report:\n" + diagnosis['report_html'] + "\n\n"
    for message in history:
        conversation_for_gemini += f"{message['role'].capitalize()}: {message['content']}\n"
    conversation_for_gemini += f"User: {question}\n\nAs a plant pathology expert, provide a detailed, helpful answer to the user's question about their plant diagnosis."
    try:
        if not gemini_model:
            conn.close()
            return jsonify({'error': 'Plant diagnosis service is currently unavailable. Please configure your Gemini API key.'}), 503
        response = gemini_model.generate_content(conversation_for_gemini)
        answer = response.text
        conn.execute('INSERT INTO diagnoses_chat_history (diagnosis_id, role, content) VALUES (?, ?, ?)', (diagnosis_id, 'assistant', answer))
        conn.commit()
        conn.close()
        return jsonify({'answer': markdown.markdown(answer)})
    except Exception as e:
        conn.close()
        print(f"An error occurred in diagnosis follow-up: {e}")
        return jsonify({'error': 'Sorry, an error occurred.'}), 500

# --- ENHANCED HEALTH CHECK ENDPOINT ---
@app.route('/api/health', methods=['HEAD', 'GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'services': {
            'gemini_api': 'available' if gemini_model else 'unavailable',
            'database': 'available' if DATABASE_ENV == 'development' else ('available' if DATABASE_URL else 'unconfigured')
        },
        'version': '3.0.0',
        'ai_model': 'Gemini 2.5 Flash',
        'database_env': DATABASE_ENV,
        'features': ['farm_planning', 'plant_diagnosis', 'chat_support', 'pdf_export', 'showcase_sharing']
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

# --- MAIN EXECUTION BLOCK ---
# --- MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)