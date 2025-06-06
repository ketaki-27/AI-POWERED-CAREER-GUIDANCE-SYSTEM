from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import pandas as pd
from collections import defaultdict
from datetime import datetime
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'abc123'  # Change this to a strong secret key in production

# In-memory user store: username -> password_hash
users = {}

print("✅ Starting Flask app...")
print("📂 Current Working Directory:", os.getcwd())

# Load data safely
try:
    interest_questions_df = pd.read_csv('data/RIASEC_Interest_Questions_HighSchool.csv', encoding="utf-8")
    personality_questions_df = pd.read_csv('data/Personality_Questions_BigFive_HighSchool.csv', encoding="utf-8")
    career_dataset = pd.read_csv('new.csv', encoding="utf-8")
    with open('data/career_resources.json', 'r', encoding='utf-8') as f:
        career_resources = json.load(f)
    print("✅ All datasets loaded successfully.")
except Exception as e:
    print(f"❌ Error loading datasets: {e}")
    raise
 
# Single login_required decorator definition
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            print("User  not logged in; redirecting to login page.")
            flash('You need to login first to access the quiz.', 'error')
            return redirect(url_for('login'))
        else:
            print(f"User  '{session['username']}' logged in; access granted.")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        try:
            send_email(name, email, subject, message)
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            print(f"Error: {e}")
            flash("Something went wrong. Please try again later.", "danger")
        
        return redirect(url_for('contact'))  # Or redirect to 'index' if preferred
    
    # If GET request, just show the contact form
    return render_template('contact.html')

@app.route('/career_path')
@login_required  # Optional — remove if you want public access
def career_path():
    return render_template('career_path.html')


def send_email(name, sender_email, subject, body):
    # Configure this with your email details
    EMAIL_ADDRESS = 'ketakisonawane27@email.com'
    EMAIL_PASSWORD = 'ketaki@2025'

    msg = EmailMessage()
    msg['Subject'] = subject or 'New Contact Form Message'
    msg['From'] = sender_email
    msg['To'] = EMAIL_ADDRESS
    msg.set_content(f"From: {name} <{sender_email}>\n\n{body}")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not password or not confirm_password:
            flash('Please fill all fields', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        if username in users:
            flash('Username already taken', 'error')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        users[username] = password_hash
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        print(f"Attempting to log in with username: {username}")  # Debugging line

        if username not in users:
            flash('Invalid username or password', 'error')
            print("Username not found.")  # Debugging line
            return redirect(url_for('login'))

        password_hash = users.get(username)
        if not check_password_hash(password_hash, password):
            flash('Invalid username or password', 'error')
            print("Password does not match.")  # Debugging line
            return redirect(url_for('login'))

        session['username'] = username
        flash(f'Welcome {username}!', 'success')
        return redirect(url_for('quiz'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    print(f"User  '{session.get('username')}' accessed quiz page.")  # Debug print

    if request.method == 'POST':
        print("📝 Processing quiz form submission...")

        # Score Interests
        interest_scores = defaultdict(int)
        for idx, row in interest_questions_df.iterrows():
            try:
                answer = int(request.form.get(f'iq{idx}', '3'))
            except ValueError:
                answer = 3
            interest_scores[row['Interest Category']] += answer

        # Score Personality
        personality_scores = defaultdict(int)
        for idx, row in personality_questions_df.iterrows():
            try:
                answer = int(request.form.get(f'pq{idx}', '3'))
            except ValueError:
                answer = 3
            personality_scores[row['Personality Trait']] += answer

        # Top scoring categories
        top_interests = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        top_traits = sorted(personality_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        top_interest_names = [i[0] for i in top_interests]
        top_trait_names = [p[0] for p in top_traits]

        print("🔍 Top Interests:", top_interest_names)
        print("🔍 Top Personality Traits:", top_trait_names)

        # Filter careers by interest
        interest_matches = career_dataset[
            (career_dataset['Interest 1'].isin(top_interest_names)) &
            (career_dataset['Interest 2'].isin(top_interest_names))
        ]
        if interest_matches.empty:
            interest_matches = career_dataset[
                (career_dataset['Interest 1'].isin(top_interest_names)) |
                (career_dataset['Interest 2'].isin(top_interest_names))
            ]
        print(f"🎯 Careers matching interests: {len(interest_matches)}")

        # Filter by personality
        final_careers_df = interest_matches[
            (interest_matches['Personality 1'].isin(top_trait_names)) |
            (interest_matches['Personality 2'].isin(top_trait_names))
        ]
        if final_careers_df.empty:
            final_careers_df = interest_matches

        print(f"✅ Final matched careers: {len(final_careers_df)}")

        # Prepare recommendations
        careers = []
        for _, row in final_careers_df.iterrows():
            career_title = row.get('Career', 'Unknown')
            matched_interests = [i for i in top_interest_names if i in [row['Interest 1'], row['Interest 2']]]
            matched_traits = [t for t in top_trait_names if t in [row['Personality 1'], row['Personality 2']]]

            explanation = f"This career matches your interest in {', '.join(matched_interests)}"
            if matched_traits:
                explanation += f" and aligns with your personality traits like {', '.join(matched_traits)}"
            explanation += "."

            resources = career_resources.get(career_title, {})

            careers.append({
                "title": career_title,
                "description": row.get('Description', 'No description available.'),
                "experience": row.get('Work Experience', 'N/A'),
                "salary": row.get('Salary', 'N/A'),
                "skills": [s.strip() for s in str(row.get('Skills', '')).split(',') if s.strip()],
                "explanation": explanation,
                "learning_path": row.get('Learning Path', 'N/A'),
                "resources": resources
            })

        if not careers:
            print("⚠️ No careers matched.")
            careers = [{
                "title": "No perfect match found.",
                "description": "Try adjusting your preferences or exploring more career options.",
                "experience": "",
                "salary": "",
                "skills": [],
                "explanation": "",
                "learning_path": "",
                "resources": {}
            }]

        # Save user result
        try:
            user_data = {
                'timestamp': datetime.now().isoformat(),
                'top_interest_1': top_interest_names[0],
                'top_interest_2': top_interest_names[1],
                'top_personality_1': top_trait_names[0],
                'top_personality_2': top_trait_names[1],
                'matched_careers': ', '.join([c["title"] for c in careers])
            }
            user_df = pd.DataFrame([user_data])
            csv_path = 'user_responses.csv'
            if os.path.exists(csv_path):
                user_df.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                user_df.to_csv(csv_path, index=False)
            print("💾 User response saved.")
        except Exception as e:
            print(f"❌ Error saving user response: {e}")

        return render_template('result.html',
                               top_interests=top_interest_names,
                               top_traits=top_trait_names,
                               careers=careers,
                               learning_resources=career_resources)

    print("🧠 Rendering quiz form...")
    return render_template('quiz.html',
                           interest_questions=interest_questions_df.iterrows(),
                           personality_questions=personality_questions_df.iterrows())

@app.route('/templates')
@login_required
def templates_page():
    return render_template('templates_page.html')

@app.route('/template/<int:template_id>')
@login_required
def show_resume_template(template_id):
    if template_id in [1, 2, 3,4]:
        return render_template(f'template{template_id}.html')
    flash("Template not found.", "error")
    return redirect(url_for('templates_page'))


if __name__ == '__main__':
    print("🚀 Running Flask app (debug=True)...")
    app.run(debug=False)
