<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="YieldWise AI Banner" width="800"/>
</p>

<div align="center">

# 🌱 YieldWise AI

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Flask-2.0-black?style=for-the-badge&logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/Frontend-HTML%2FCSS%2FJS-orange?style=for-the-badge&logo=javascript" alt="Frontend">
  <img src="https://img.shields.io/badge/Hackathon-VIBE%20CODING%203.0-brightgreen?style=for-the-badge" alt="Hackathon">
</p>

> An all-in-one platform for African farmers to plan profitable farms, diagnose plant diseases with a photo, and build their agricultural business using the power of AI.

**Developed by Onyeka Nwokike**

</div>

---

### **[🚀 View Live Demo](https://yieldwise-ai.onrender.com/)**

---

## 📖 About The Project

In Nigeria and across Africa, millions of smallholder farmers face a critical information gap. Limited access to expert agronomic advice, the high cost of soil testing, and the devastating impact of pests and diseases lead to reduced yields and financial instability. This directly impacts food security and economic growth, a core challenge of **SDG 2: Zero Hunger**.

**YieldWise AI** is our solution. It's a web-based platform that puts an AI-powered agronomist and a plant pathologist in the pocket of every farmer, for free. By leveraging state-of-the-art AI, we provide instant, actionable intelligence that empowers farmers to make smarter, data-driven decisions, increase their profitability, and contribute to a more food-secure future.

---

## ✨ Core Features

Our platform is a suite of powerful, easy-to-use tools:

| Feature               | Description                                                                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **📝 AI Farm Planner** | Describe your land, budget, and location, and our AI generates a detailed, step-by-step business plan using the lightning-fast `Groq Llama 3.1` model. |
| **🔬 AI Plant Doctor** | Upload a photo of an affected plant leaf, and our multimodal AI (`Google Gemini 1.5 Flash`) will diagnose the disease and suggest treatments.        |
| **🚀 Shareable Showcases** | Turn any farm plan into a beautiful, public webpage to share with potential partners, investors, or customers.                                         |
| **📄 Professional PDFs** | Download any farm plan as a professionally formatted PDF document, perfect for printing or sharing.                                                  |
| **💬 Interactive Chat** | Ask follow-up questions about your plans and diagnoses to get deeper, context-aware insights from the AI.                                              |
| **👤 Full User System** | A complete user registration and login system allows users to save and manage their history of farm plans and diagnoses.                             |

---

## 🛠️ Tech Stack

We chose a modern, scalable, and efficient tech stack to bring this vision to life:

<p align="center">
  <a href="https://www.python.org/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="python" width="40" height="40"/> </a>
  <a href="https://flask.palletsprojects.com/" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/pocoo_flask/pocoo_flask-icon.svg" alt="flask" width="40" height="40"/> </a>
  <a href="https://www.sqlite.org/" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/sqlite/sqlite-icon.svg" alt="sqlite" width="40" height="40"/> </a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/javascript/javascript-original.svg" alt="javascript" width="40" height="40"/> </a>
  <a href="https://www.w3.org/html/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/html5/html5-original-wordmark.svg" alt="html5" width="40" height="40"/> </a>
  <a href="https://www.w3schools.com/css/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/css3/css3-original-wordmark.svg" alt="css3" width="40" height="40"/> </a>
</p>

-   **Backend:**
    -   Framework: `Flask` (Python)
    -   Database: `SQLite 3`
    -   AI Integration: `LangChain` with `Groq API` (Llama 3.1) & `Google Gemini 1.5 Flash API`
    -   User Management: `Flask-Login`
    -   Security: `Werkzeug` (password hashing), `Flask-Limiter` (rate limiting)
-   **Frontend:**
    -   Templating: `Jinja2`
    -   Styling: `Vanilla HTML5` & `CSS3`
    -   Scripting: `Vanilla JavaScript`
-   **PDF Generation:**
    -   `WeasyPrint` for converting HTML & CSS to high-quality PDF reports.

---

## ⚙️ Getting Started

To get a local copy up and running, follow these simple steps.

### **Prerequisites**

-   Python 3.10+
-   `pip` and `venv`

### **Installation & Setup**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Nwokike/yieldwise-ai.git](https://github.com/Nwokike/yieldwise-ai.git)
    cd yieldwise-ai
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows (Git Bash)
    python -m venv venv
    source venv/Scripts/activate

    # For macOS/Linux
    # python3 -m venv venv
    # source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a file named `.env` in the project root and add your secret API keys.
    ```env
    # Get your key from [https://console.groq.com/](https://console.groq.com/)
    GROQ_API_KEY="gsk_..."

    # Get your key from [https://aistudio.google.com/](https://aistudio.google.com/)
    GOOGLE_API_KEY="AIzaSy..."
    ```

5.  **Initialize the database and run the app:**
    The database will be created automatically on the first run.
    ```bash
    python app.py
    ```

    The application will then be available at `http://127.0.0.1:5000`.

---

## 👨‍💻 About The Author

**Onyeka Nwokike**

I am an Agricultural and Bioresources Engineer and a Software Developer, uniquely positioned at the intersection of sustainable agriculture and scalable technology. My background includes professional experience with the National Agricultural Seeds Council of Nigeria, giving me firsthand insight into the challenges our farmers face. As a current student at PLP Africa, I am passionate about leveraging AI to create practical, impactful solutions.

<p align="left">
  <a href="https://github.com/Nwokike" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/>
  </a>
  <a href="https://nwokike.github.io/portfolio" target="_blank">
    <img src="https://img.shields.io/badge/Portfolio-0077B5?style=for-the-badge&logo=website&logoColor=white" alt="Portfolio"/>
  </a>
  <a href="mailto:nwokikeonyeka@gmail.com">
    <img src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Gmail"/>
  </a>
</p>
