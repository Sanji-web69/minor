#import dependencies
import requests
import random
import sqlite3
from bs4 import BeautifulSoup as bs
import time
from flask import Flask, render_template,request, url_for, redirect,session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta


app= Flask(__name__)
app.secret_key="secretkey"

#SQlAlchemy configure
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
db = SQLAlchemy(app)

#database model
class User(db.Model):
    id=db.Column(db.Integer, primary_key =True)
    username=db.Column(db.String(25), unique=True, nullable=False)
    password_hash=db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash=generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    full_name = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    nationality = db.Column(db.String(50))
    address = db.Column(db.String(200))
    state = db.Column(db.String(50))
    email = db.Column(db.String(100))
    category = db.Column(db.String(20))
    income = db.Column(db.String(20))
    parent_occupation = db.Column(db.String(100))
    disability = db.Column(db.String(100))
    contact = db.Column(db.String(15))
    education_level = db.Column(db.String(100))
    institution = db.Column(db.String(100))
    board = db.Column(db.String(100))
    passing_year = db.Column(db.String(10))
    score_10 = db.Column(db.String(10))
    score_12 = db.Column(db.String(10))
    score_ug = db.Column(db.String(10))
    score_pg = db.Column(db.String(10))
    current_cgpa = db.Column(db.String(10))

    user = db.relationship("User", backref="profile")


#routing
@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('login'))

    profile_data = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile_data:
        return redirect(url_for('form'))

    profile = {
        "full_name": profile_data.full_name,
        "dob": profile_data.dob,
        "gender": profile_data.gender,
        "nationality": profile_data.nationality,
        "address": profile_data.address,
        "state": profile_data.state,
        "email": profile_data.email,
        "category": profile_data.category,
        "income": profile_data.income,
        "disability": profile_data.disability,
        "contact": profile_data.contact,
        "education_level": profile_data.education_level,
        "institution": profile_data.institution,
        "board": profile_data.board,
        "passing_year": profile_data.passing_year,
        "score_10": profile_data.score_10,
        "score_12": profile_data.score_12,
        "score_ug": profile_data.score_ug,
        "score_pg": profile_data.score_pg,
        "current_cgpa": profile_data.current_cgpa,
        "parent_occupation": profile_data.parent_occupation
    }

    gender = profile_data.gender.strip().lower()
    category = profile_data.category.strip().lower()
    state = profile_data.state.strip().lower()

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        # Gender condition
        if gender == 'male':
            gender_condition = """
                LOWER(REPLACE(overview, ' ', '')) LIKE '%gender:forall%'
            """
        else:
            gender_condition = """
                (LOWER(REPLACE(overview, ' ', '')) LIKE '%gender:female%'
                 OR LOWER(REPLACE(overview, ' ', '')) LIKE '%gender:forall%')
            """

        # Final query
        query = f"""
            SELECT title, overview, how_to_apply
            FROM scholarships
            WHERE {gender_condition}
              AND (LOWER(REPLACE(overview, ' ', '')) LIKE '%category:{category}%' OR LOWER(REPLACE(overview, ' ', '')) LIKE '%category:forall%')
              AND (LOWER(REPLACE(overview, ' ', '')) LIKE '%state:{state}%' OR LOWER(REPLACE(overview, ' ', '')) LIKE '%state:allindia%')
        """

        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        conn.close()

    matched_scholarships = [
        {'title': row[0], 'overview': row[1], 'how_to_apply': row[2]}
        for row in rows
    ]

    return render_template('dashboard.html', scholarships=matched_scholarships, profile=profile)

    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user:
            return render_template("register.html", error="User already registered")
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('form'))
    
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route("/form", methods=["GET", "POST"])
def form():
    if "username" not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == "POST":
        profile = UserProfile(
            user_id=user.id,
            full_name=request.form.get("full_name"),
            dob=request.form.get("dob"),
            gender=request.form.get("gender"),
            nationality=request.form.get("nationality"),
            address=request.form.get("address"),
            state=request.form.get("state"),
            email=request.form.get("email"),
            category=request.form.get("category"),
            income=request.form.get("income"),
            parent_occupation=request.form.get("parent_occupation"),
            disability=request.form.get("disability"),
            contact=request.form.get("contact"),
            education_level=request.form.get("education_level"),
            institution=request.form.get("institution"),
            board=request.form.get("board"),
            passing_year=request.form.get("passing_year"),
            score_10=request.form.get("score_10"),
            score_12=request.form.get("score_12"),
            score_ug=request.form.get("score_ug"),
            score_pg=request.form.get("score_pg"),
            current_cgpa=request.form.get("current_cgpa")
        )
        db.session.add(profile)
        db.session.commit()
        return redirect(url_for('dashboard'))
    print(request.form)


    return render_template("form.html", username=session['username'])


@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    profile_data = UserProfile.query.filter_by(user_id=user.id).first()

    return render_template("profile.html", user=user, profile=profile_data)


details_part1 = [
    'https://scholarshipforme.com/scholarships/the-education-future-international-scholarship',
    'https://scholarshipforme.com/scholarships/national-scholarship-for-higher-education-of-st-students',
    'https://scholarshipforme.com/scholarships/ugc-national-fellowship-for-scheduled-caste-students-nfsc-',
    'https://scholarshipforme.com/scholarships/national-fellowship-and-scholarship-for-higher-education-of-st-students',
    'https://scholarshipforme.com/scholarships/tata-housing-scholarships-for-meritorious-girl-students',
    'https://scholarshipforme.com/scholarships/national-scheme-of-incentive-to-girls-for-secondary-education-nsigse-',
    'https://scholarshipforme.com/scholarships/central-sector-scheme-of-scholarship-for-college-and-university-students2167',
    'https://scholarshipforme.com/scholarships/post-graduate-scholarship-for-professional-courses-for-sc-st-students',
    'https://scholarshipforme.com/scholarships/top-class-education-scheme-for-sc-students',
    'https://scholarshipforme.com/scholarships/-life-s-good-scholarship-program-2024',
]
details_part2 = [
    'https://scholarshipforme.com/scholarships/kotak-kanya-scholarship',
    'https://scholarshipforme.com/scholarships/dxc-progressing-minds-scholarship-2023-24',
    'https://scholarshipforme.com/scholarships/fuel-business-school-csr-scholarship-2023-24',
    'https://scholarshipforme.com/scholarships/aauw-international-fellowship-2023',
    'https://scholarshipforme.com/scholarships/amazon-future-engineer-scholarship',
    'https://scholarshipforme.com/scholarships/u-go-scholarship-programme',
    'https://scholarshipforme.com/scholarships/women-scientist-scheme-c-wos-c-',
    'https://scholarshipforme.com/scholarships/indira-gandhi-scholarship-for-single-girl',
    'https://scholarshipforme.com/scholarships/cbse-single-girl-child-scholarship',
    'https://scholarshipforme.com/scholarships/clinic-plus-scholarship',
]
details_part3 = [
    'https://scholarshipforme.com/scholarships/adobe-india-women-in-technology-scholarship',
    'https://scholarshipforme.com/scholarships/-life-s-good-scholarship-program-2024',
    'https://scholarshipforme.com/scholarships/dr-a-p-j-abdul-kalam-ignite',
    'https://scholarshipforme.com/scholarships/clp-india-this-scholarship',
    'https://scholarshipforme.com/scholarships/drdo-itr-chandipur-graduate-technician-diploma-apprenticeship-2023',
    'https://scholarshipforme.com/scholarships/the-medhaavi-engineering-scholarship-program-2023-24',
    'https://scholarshipforme.com/scholarships/empowerment-and-equity-opportunities-for-excellence-in-science',
    'https://scholarshipforme.com/scholarships/h-h-dalai-lama-sasakawa-scholarship',
    'https://scholarshipforme.com/scholarships/aicte-civil-engineering-internship-cei-9214',
    'https://scholarshipforme.com/scholarships/university-of-southampton---great-scholarships',
]
urls_details = details_part1 + details_part2 + details_part3


# SQLite Setup
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    overview TEXT,
    how_to_apply TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS update_info (
    id INTEGER PRIMARY KEY,
    last_run TIMESTAMP
)
''')


conn.commit()

# Check If Update Needed
cursor.execute("SELECT COUNT(*) FROM scholarships")
count = cursor.fetchone()[0]

cursor.execute("SELECT last_run FROM update_info WHERE id = 1")
last_run_row = cursor.fetchone()

should_update = False
now = datetime.now()

if count == 0:
    should_update = True
elif last_run_row:
    last_run_time = datetime.strptime(last_run_row[0], "%Y-%m-%d %H:%M:%S")
    if now - last_run_time >= timedelta(hours=24):
        should_update = True
else:
    should_update = True

print("🕒 Last update time:", last_run_row[0] if last_run_row else "None")
print("🔄 Should update:", should_update)


def fetch_page(url):
    headers = {
        'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Mozilla/5.0 (X11; Linux x86_64)',
        ])
    }
    try:
        print(f"🔍 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ Status Code {response.status_code} for URL: {url}")
    except Exception as e:
        print(f"🚫 Failed to fetch {url}: {e}")
    return None

# parsing
def parse_details(html):
    soup = bs(html, 'html.parser')

    title_tag = soup.find('h1', class_='title')
    title_text = title_tag.get_text(strip=True) if title_tag else "No Title Found"
    
    # Overview
    overview_list = soup.select("ul.job-overview li")
    overview_text = "\n".join([li.get_text(strip=True) for li in overview_list])


    # How to Apply
    apply_text = ""
    job_details_div = soup.find("div", class_="job-details-body")
    if job_details_div:
        p_tags = job_details_div.find_all("p")
        if p_tags:
            apply_text = p_tags[-1].get_text(strip=True)

    return title_text, overview_text, apply_text

# Data Update Logic

if should_update:
    print("Starting update...")

    max_entries = 30
    for index, url in enumerate(urls_details[:max_entries]):
        html = fetch_page(url)
        if html:
            title, overview, apply = parse_details(html)

            if index < count:
                # Update existing record
                cursor.execute('''
                    UPDATE scholarships
                    SET title=?, overview = ?, how_to_apply = ?, last_updated = ?
                    WHERE id = ?
                ''', (title, overview, apply, now, index + 1))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO scholarships (title, overview,  how_to_apply, last_updated)
                    VALUES ( ?, ?, ?, ?)
                ''', (title, overview, apply, now))

            conn.commit()
        time.sleep(random.uniform(1, 2))

    # Update metadata table
    cursor.execute('''
        INSERT INTO update_info (id, last_run)
        VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET last_run=excluded.last_run
    ''', (now.strftime("%Y-%m-%d %H:%M:%S"),))

    conn.commit()
    print(" Scholarships updated successfully.")
else:
    print(" No update needed. Less than 24 hours since last fetch.")

conn.close()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)