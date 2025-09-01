# 1. Import necessary libraries
import os
import sqlite3
import uuid
import markdown
import requests
from flask import (
    Flask, render_template, request, jsonify, abort, redirect, url_for, flash,
    make_response, session
)
from dotenv import load_dotenv
import groq
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

# Load environment variables from .env file
load_dotenv()

# 2. Initialize Flask and extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize security extensions
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- API KEY & AI CLIENT SETUP ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

groq_client = groq.Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# --- DATABASE SETUP & HELPERS ---
def get_db_connection():
    conn = sqlite3.connect('yieldwise.db', check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL, name TEXT NOT NULL
        );
    ''')
    # Farm plans table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS farm_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            location TEXT NOT NULL, country TEXT, currency TEXT,
            plan_html TEXT NOT NULL, showcase_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    # Chat history for plans
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES farm_plans (id)
        );
    ''')
    # Diagnoses table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            title TEXT NOT NULL, crop_type TEXT, report_html TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    # Chat history for diagnoses
    conn.execute('''
        CREATE TABLE IF NOT EXISTS diagnoses_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, diagnosis_id INTEGER NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (diagnosis_id) REFERENCES diagnoses (id)
        );
    ''')
    conn.commit()
    conn.close()

# Custom Jinja filter for date formatting
@app.template_filter('dateformat')
def dateformat(value, format='%Y-%m-%d'):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value # Return original string if parsing fails
    if hasattr(value, 'strftime'):
        return value.strftime(format)
    return value

# --- USER CLASS & LOADER ---
class User(UserMixin):
    def __init__(self, id, email, password, name):
        self.id = id
        self.email = email
        self.password = password
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['email'], user_data['password'], user_data['name'])
    return None

# --- CORE AI & SEARCH FUNCTIONS ---
def search_google(query):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': GOOGLE_API_KEY, 'cx': SEARCH_ENGINE_ID, 'q': query, 'num': 5}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        search_results = response.json()
        snippets = [item.get('snippet', '') for item in search_results.get('items', [])]
        return "\n".join(snippets)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during Google search: {e}")
        return f"Error: Could not connect to the real-time search service. Please check API keys. ({e})"

def generate_farm_plan(location, space, budget, country, currency):
    search_query = f"most profitable fast-growing crops for small space farming in {location} {country}"
    search_context = search_google(search_query)

    if search_context.startswith("Error:"):
        return f"<p class='error-message'>{search_context}</p>", []

    try:
        master_prompt = f"""
        **CRITICAL INSTRUCTION: Your response must be in two parts, separated by "---SUGGESTIONS---". First, the business plan. Second, three follow-up questions.**

        **User's Details:**
        - Location: {location}, {country}
        - Budget: {currency} {budget}

        **Live Research Data:**
        ---
        {search_context}
        ---

        **Part 1: Business Plan (Markdown Format)**
        1.  **🌱 Recommended Crop:** Research and choose ONE highly profitable, fast-growing crop.
        2.  **💰 Budget Breakdown (in {currency}):** Create a markdown table for the EXACT budget.
        3.  **🛍️ Supplies & Sourcing:** Create markdown links searching for each budget item on Jumia Nigeria. Format: `* [Item Name](https://www.jumia.com.ng/catalog/?q=item+name)`.
        4.  **🗓️ 90-Day Action Plan:** A simple 4-step timeline.
        5.  **📈 Realistic Earnings Projection:** Estimate harvest quantity and earnings in {currency}.
        6.  **🛒 Simple Market Strategy:** ONE sentence on the easiest way to sell.
        7.  **⚠️ Risk & Mitigation:** ONE major risk and ONE simple mitigation.

        ---SUGGESTIONS---

        **Part 2: Suggested Follow-up Questions**
        Provide three brief, insightful follow-up questions a user might ask.
        """
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": master_prompt}],
            model="llama3-70b-8192", temperature=0.5, max_tokens=2048
        )
        full_response = chat_completion.choices[0].message.content
        
        if "---SUGGESTIONS---" in full_response:
            plan_text, suggestions_text = full_response.split("---SUGGESTIONS---", 1)
            suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and s.strip().startswith(('1', '2', '3', '- '))]
        else:
            plan_text = full_response
            suggestions = []
            
        return plan_text.strip(), suggestions

    except Exception as e:
        print(f"An error occurred with the Groq API: {e}")
        return "<p>Sorry, an error occurred while generating the plan.</p>", []

def diagnose_plant_issue(image_file, crop_type):
    try:
        img = Image.open(image_file)
        prompt_parts = [
            f"""
            Analyze the attached image of a {crop_type} leaf. Your response must be in two parts, separated by "---SUGGESTIONS---".

            Part 1: Diagnosis Report (Markdown Format)
            1.  **Title:** A short, descriptive title.
            2.  **Analysis:** Identify the likely pest or disease.
            3.  **Symptoms:** Describe the symptoms shown in the image.
            4.  **Organic Treatment:** Recommend one organic method for a Nigerian farmer.
            5.  **Chemical Treatment:** Recommend one chemical method.
            **IMPORTANT: Do not apologize for image quality. Provide the best possible diagnosis based on what you see.**

            ---SUGGESTIONS---

            Part 2: Suggested Follow-up Questions
            Provide three brief follow-up questions. **IMPORTANT: Do not suggest showing images or videos.**
            """,
            img,
        ]
        response = gemini_model.generate_content(prompt_parts)
        full_response = response.text

        if "---SUGGESTIONS---" in full_response:
            report_text, suggestions_text = full_response.split("---SUGGESTIONS---", 1)
            title_line = report_text.strip().split('\n')[0]
            title = title_line.replace('**Title:**', '').strip() if '**Title:**' in title_line else f"Diagnosis for {crop_type}"
            suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and s.strip().startswith(('1', '2', '3', '- '))]
        else:
            report_text = full_response
            title = f"General Diagnosis for {crop_type}"
            suggestions = []
            
        return title, report_text.strip(), suggestions

    except Exception as e:
        print(f"An error occurred during Gemini image analysis: {e}")
        return "Error", "<p>Sorry, an error occurred while analyzing the image.</p>", []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- WEBSITE ROUTES ---
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

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
            plan_html = markdown.markdown(guest_plan['plan_text'], extensions=['tables'])
            conn.execute(
                'INSERT INTO farm_plans (user_id, location, country, currency, plan_html) VALUES (?, ?, ?, ?, ?)',
                (new_user_id, guest_plan['location'], guest_plan['country'], guest_plan['currency'], plan_html)
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
        email = request.form.get('email')
        password = request.form.get('password')

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
    if plan is None:
        abort(404)
    return render_template('showcase.html', plan=plan)

@app.route('/download_pdf/<int:plan_id>')
@login_required
def download_pdf(plan_id):
    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    conn.close()
    if plan is None:
        return abort(404)
    
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

    plan_text, suggestions = generate_farm_plan(
        data['location'], data['space'], data['budget'], data['country'], data['currency']
    )
    
    if plan_text.startswith("<p class='error-message'>"):
        return jsonify({'error': plan_text}), 500

    plan_html = markdown.markdown(plan_text, extensions=['tables'])

    if not current_user.is_authenticated:
        if session.get('free_plan_used'):
            return jsonify({'error': 'Free plan already used. Please register.'}), 429
        session['free_plan_used'] = True
        session['guest_plan'] = {'plan_text': plan_text, 'location': data['location'], 'country': data['country'], 'currency': data['currency']}
        return jsonify({'plan': plan_html, 'plan_id': None, 'suggestions': suggestions})

    conn = get_db_connection()
    cursor = conn.cursor()
    showcase_id = str(uuid.uuid4())
    cursor.execute(
        'INSERT INTO farm_plans (user_id, location, country, currency, plan_html, showcase_id) VALUES (?, ?, ?, ?, ?, ?)',
        (current_user.id, data['location'], data['country'], data['currency'], plan_html, showcase_id)
    )
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

    file = request.files['plant_image']
    crop_type = request.form['crop_type']

    if file.filename == '' or not crop_type:
        return jsonify({'error': 'No selected file or crop type'}), 400

    if file and allowed_file(file.filename):
        title, report_text, suggestions = diagnose_plant_issue(file, crop_type)
        report_html = markdown.markdown(report_text, extensions=['tables'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO diagnoses (user_id, title, crop_type, report_html) VALUES (?, ?, ?, ?)',
            (current_user.id, title, crop_type, report_html)
        )
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
    if not plan_id:
        return jsonify({'error': 'Plan ID is required'}), 400
    showcase_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute('UPDATE farm_plans SET showcase_id = ? WHERE id = ? AND user_id = ?', (showcase_id, plan_id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'showcase_id': showcase_id})

@app.route('/api/get_plan/<int:plan_id>', methods=['GET'])
@login_required
def get_plan(plan_id):
    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    chat_history = conn.execute('SELECT role, content FROM chat_history WHERE plan_id = ? ORDER BY created_at ASC', (plan_id,)).fetchall()
    conn.close()
    if plan is None: return jsonify({'error': 'Plan not found'}), 404
    return jsonify({
        'plan': dict(plan),
        'chat_history': [dict(row) for row in chat_history]
    })

@app.route('/api/delete_plan/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    conn = get_db_connection()
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

    conn = get_db_connection()
    plan = conn.execute('SELECT * FROM farm_plans WHERE id = ? AND user_id = ?', (plan_id, current_user.id)).fetchone()
    history = conn.execute('SELECT role, content FROM chat_history WHERE plan_id = ? ORDER BY created_at ASC', (plan_id,)).fetchall()
    
    conn.execute('INSERT INTO chat_history (plan_id, role, content) VALUES (?, ?, ?)', (plan_id, 'user', question))
    conn.commit()
    
    conversation_history = [{"role": "system", "content": "You are a helpful agricultural assistant. The user's initial plan is as follows:" + plan['plan_html']}]
    for message in history:
        conversation_history.append({"role": "user" if message['role'] == 'user' else "assistant", "content": message['content']})
    conversation_history.append({"role": "user", "content": question})

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": msg['role'], "content": msg['content']} for msg in conversation_history], model="llama3-70b-8192",
            temperature=0.7, max_tokens=1024
        )
        answer = chat_completion.choices[0].message.content
        
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
    return jsonify({
        'diagnosis': dict(diagnosis),
        'chat_history': [dict(row) for row in chat_history]
    })
    
@app.route('/api/delete_diagnosis/<int:diagnosis_id>', methods=['DELETE'])
@login_required
def delete_diagnosis(diagnosis_id):
    conn = get_db_connection()
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

    conn = get_db_connection()
    diagnosis = conn.execute('SELECT * FROM diagnoses WHERE id = ? AND user_id = ?', (diagnosis_id, current_user.id)).fetchone()
    history = conn.execute('SELECT role, content FROM diagnoses_chat_history WHERE diagnosis_id = ? ORDER BY created_at ASC', (diagnosis_id,)).fetchall()
    
    conn.execute('INSERT INTO diagnoses_chat_history (diagnosis_id, role, content) VALUES (?, ?, ?)', (diagnosis_id, 'user', question))
    conn.commit()
    
    conversation_history = [{"role": "system", "content": "You are a helpful plant disease diagnostics assistant. The user's initial diagnosis report is:" + diagnosis['report_html']}]
    for message in history:
        conversation_history.append({"role": "user" if message['role'] == 'user' else "assistant", "content": message['content']})
    conversation_history.append({"role": "user", "content": question})

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": msg['role'], "content": msg['content']} for msg in conversation_history], model="llama3-70b-8192",
            temperature=0.7, max_tokens=1024
        )
        answer = chat_completion.choices[0].message.content
        
        conn.execute('INSERT INTO diagnoses_chat_history (diagnosis_id, role, content) VALUES (?, ?, ?)', (diagnosis_id, 'assistant', answer))
        conn.commit()
        conn.close()
        
        return jsonify({'answer': markdown.markdown(answer)})
    except Exception as e:
        conn.close()
        print(f"An error occurred in diagnosis follow-up: {e}")
        return jsonify({'error': 'Sorry, an error occurred.'}), 500

# --- MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True, use_reloader=False)

