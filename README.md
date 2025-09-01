# 🌱 YieldWise AI

**AI-powered farm planning & crop diagnosis platform**

---

## 📖 About the Project

Smallholder farmers in Africa face **low yields**, **pest infestations**, and **limited access to expert guidance**. **YieldWise AI** tackles these by offering:

* 📝 **AI-generated farm business plans** (tailored to location, budget, and crops).
* 🩺 **Plant disease diagnosis from images** using Google Gemini.
* 📄 **Exportable PDF reports** for easy sharing and record-keeping.
* 🌍 **Real-time research integration** via Google Custom Search API.

This project directly supports **SDG 2: Zero Hunger** by enabling farmers to make smarter, data-driven decisions.

---

## ✨ Features

* User registration & authentication (Flask-Login)
* Rate limiting for API endpoints (Flask-Limiter)
* Generate farm plans using Groq (LLaMA 3)
* Diagnose plant diseases from uploaded images using Google Gemini
* Save plans & diagnoses to SQLite
* Export plans as PDF (WeasyPrint)
* Guest mode with one free plan generation

---

## 🛠️ Tech Stack

* **Frontend:** Flask (Jinja2 templates), HTML5, CSS3, JavaScript
* **Backend:** Python (Flask), SQLite3
* **AI APIs:**

  * Groq (LLaMA 3) — farm plan generation
  * Google Gemini — plant disease diagnosis (image + text)
  * Google Custom Search API — live crop research snippets
* **Other Tools:** WeasyPrint, Pillow
* **Security & Utilities:** Flask-Login, Flask-Limiter, python-dotenv

---

## ⚙️ Installation & Setup

Follow these steps to run the project locally.

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/yieldwise-ai.git
cd yieldwise-ai
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment variables

Create a file named `.env` in the project root and add the following (replace placeholders):

```env
SECRET_KEY=replace_with_a_random_secret
GROQ_API_KEY=replace_with_your_groq_api_key
GOOGLE_API_KEY=replace_with_your_google_api_key
SEARCH_ENGINE_ID=replace_with_your_search_engine_id
```

> **Tip:** Add `.env` to your `.gitignore` so you don’t accidentally commit it.

### 5. Initialize the database & run

The app will auto-initialize the SQLite DB on first run.

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## 📁 Project Structure

```
├── app.py              # Main Flask app
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── templates/          # Jinja2 HTML templates
├── static/             # CSS, JS, images
├── uploads/            # Uploaded plant images (create if missing)
├── yieldwise.db        # SQLite DB (auto-generated)
└── README.md           # This file
```

---

## 🧪 Testing / Quick Checks

* Register a user and log in.
* Generate a farm plan via the UI or the `/api/generate` endpoint.
* Upload a plant image to `/api/diagnose` and confirm the diagnosis is saved.
* Export a plan PDF from the dashboard.

If you hit API errors, check that the environment variables are set and valid.

---

## 🧾 API Endpoints (Quick Reference)

* `POST /api/generate` — Generate a farm plan (rate-limited).
* `POST /api/diagnose` — Upload an image and get a diagnosis (login required).
* `GET /api/get_plan/<plan_id>` — Retrieve a saved plan and chat history.
* `POST /api/follow_up` — Ask follow-up questions about a plan.
* `GET /download_pdf/<plan_id>` — Download PDF for a plan (login required).

---

## 👨‍🌾 Usage Notes

* Guest users can generate one free plan (session-based). Registered users can save plans and diagnoses.
* Rate limits are enforced using Flask-Limiter — adjust `default_limits` or per-route limits as needed for production.

---

## 👨‍💻 Author

**Onyeka Nwokike** — Software Developer & Research Writer

> I build clean, responsive, and user-focused web applications. My goal is to create impactful and sustainable technology by combining my development skills with a data-driven, research-oriented approach.

### Quick Bio

From Agricultural & Bioresources Engineering to Software Development — I blend domain knowledge in agriculture with software engineering to create practical tools for farmers and communities.

### Skills

* HTML5, CSS3, Tailwind
* JavaScript (vanilla)
* Python (Flask), SQLite, SQL
* WordPress & SEO
* Image handling with Pillow

---

## 📬 Contact

* Email: `nwokikeonyeka@gmail.com`
* Portfolio: ([My Portfolio](https://nwokike.github.io/portfolio/))

---

## 🔮 Future Improvements

* Mobile-friendly PWA
* Multi-language support (Yoruba, Hausa, Swahili)
* SMS-based diagnosis for low-internet regions
* Integrate IntaSend for payments and marketplace features

---
## 📚 License

Add a license file (`LICENSE`) if you want to specify reuse terms. For hackathons, MIT is common.

```text
MIT License

Copyright (c) 2025 Onyeka Nwokike

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction... (truncate/remove as desired)
```
