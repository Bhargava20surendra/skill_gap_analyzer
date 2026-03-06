from flask import Flask, render_template, request, redirect, session,flash,url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'skill_gap'

mysql = MySQL(app)
app.secret_key = "supersecretkey"
@app.route('/')
def home():
    return render_template("index.html")
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # ✅ Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered. Please login instead.", "danger")
            return redirect(url_for('register'))

        # ✅ Insert new user
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        mysql.connection.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        account = cursor.fetchone()

        if account and check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['name'] = account['name']

            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "danger")

    return render_template('login.html')

def analyze_skill_gap(role_id, user_skills):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Required skills
    cursor.execute("""
        SELECT skills.id, skills.skill_name
        FROM role_skills
        JOIN skills ON role_skills.skill_id = skills.id
        WHERE role_skills.role_id = %s
    """, (role_id,))
    required_skills = cursor.fetchall()

    missing_skills = []
    matched_count = 0

    for skill in required_skills:
        if str(skill['id']) not in user_skills:
            missing_skills.append(skill)
        else:
            matched_count += 1

    total_required = len(required_skills)
    match_percentage = int((matched_count / total_required) * 100) if total_required > 0 else 0
    cursor.execute("""INSERT INTO analysis_history (user_id, role_id, percentage)
    VALUES (%s, %s, %s)""", (session['id'], role_id, match_percentage))

    mysql.connection.commit()
    # Roadmap
    cursor.execute("SELECT * FROM roadmap WHERE role_id=%s ORDER BY step_number", (role_id,))
    roadmap_steps = cursor.fetchall()

    # Resources for missing skills
    resources = []
    for skill in missing_skills:
        cursor.execute("SELECT resource_link FROM resources WHERE skill_id=%s", (skill['id'],))
        res = cursor.fetchall()
        if res:
            resources.append({
                'skill': skill['skill_name'],
                'links': res
            })

    return render_template(
        "result.html",
        required_skills=required_skills,
        missing_skills=missing_skills,
        match_percentage=match_percentage,
        roadmap_steps=roadmap_steps,
        resources=resources
    )

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():

    # 🔐 Protect Route
    if 'loggedin' not in session:
        return redirect('/login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()

    cursor.execute("SELECT * FROM skills")
    skills = cursor.fetchall()

    if request.method == 'POST':
        role_id = request.form['role']
        user_skills = request.form.getlist('skills')

        return analyze_skill_gap(role_id, user_skills)

    return render_template('dashboard.html', roles=roles, skills=skills)

@app.route('/analytics')
def analytics():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT r.role_name, a.percentage, a.created_at
        FROM analysis_history a
        JOIN roles r ON a.role_id = r.id
        WHERE a.user_id = %s
        ORDER BY a.created_at ASC
    """, (session['id'],))

    rows = cursor.fetchall()

    # ✅ Convert datetime to string
    history = []
    for row in rows:
        history.append({
            "role_name": row['role_name'],
            "percentage": row['percentage'],
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M")
        })

    return render_template('analytics.html', history=history)

@app.route('/resume-analyzer', methods=['GET', 'POST'])
def resume_analyzer():

    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        resume = request.files["resume"]
        jobdesc = request.form["jobdesc"]

        file_path = os.path.join("uploads", resume.filename)
        resume.save(file_path)

        resume_skills = extract_skills_from_resume(file_path)
        job_skills = extract_skills_from_jobdesc(jobdesc)

        matched, missing, score = compare_skills(resume_skills, job_skills)

        # store result in session
        session["resume_result"] = {
            "resume_skills": resume_skills,
            "job_skills": job_skills,
            "matched": matched,
            "missing": missing,
            "score": score
        }

        # redirect to GET
        return redirect(url_for('resume_analyzer'))

    result = session.pop("resume_result", None)

    return render_template(
        "resume_analyzer.html",
        resume_skills=result["resume_skills"] if result else None,
        job_skills=result["job_skills"] if result else None,
        matched=result["matched"] if result else None,
        missing=result["missing"] if result else None,
        score=result["score"] if result else None
    )
import PyPDF2
import docx

def extract_text(file_path):
    
    text = ""
    
    if file_path.endswith(".pdf"):
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text

    return text.lower()
def compare_skills(resume_skills, job_skills):

    matched_skills = list(set(resume_skills) & set(job_skills))

    missing_skills = list(set(job_skills) - set(resume_skills))

    if len(job_skills) > 0:
        match_score = (len(matched_skills) / len(job_skills)) * 100
    else:
        match_score = 0

    return matched_skills, missing_skills, round(match_score, 2)
def extract_skills_from_resume(file_path):

    text = extract_text(file_path)

    skills_list = [
       "python","java","c","c++","html","css","javascript",
       "flask","django","sql","mysql","mongodb",
       "machine learning","deep learning","nlp",
       "aws","docker","git","pandas","numpy","matplotlib","seaborn",
       "excel","excel vba",
        "api","sdk",
        "mariadb","postgresql",
        "data analysis","data science"]

    found_skills = []

    for skill in skills_list:
        if skill in text:
            found_skills.append(skill)

    return found_skills

import re

def extract_skills_from_jobdesc(jobdesc):

    jobdesc = jobdesc.lower()

    # replace special characters with space
    jobdesc = re.sub(r'[^\w\s+#.]', ' ', jobdesc)

    skills_list = [
        "python","java","c","c++","html","css","javascript",
        "flask","django","sql","mysql","mongodb",
        "machine learning","deep learning","nlp",
        "aws","docker","git",
        "pandas","numpy","matplotlib","seaborn",
        "excel","excel vba",
        "api","sdk",
        "mariadb","postgresql",
        "data analysis","data science"
    ]

    job_skills = []

    for skill in skills_list:
        if re.search(r'\b' + re.escape(skill) + r'\b', jobdesc):
            job_skills.append(skill)

    return job_skills


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
if __name__ == '__main__':
    app.run(debug=True)