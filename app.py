import os, re, json, random, threading
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "portal_data.json")
_store_lock = threading.Lock()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

ROLE_SKILLS = {
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "Git", "Responsive Design"],
    "Python Developer": ["Python", "OOP", "Flask", "SQL", "APIs", "Git"],
    "Data Analyst": ["Python", "SQL", "Excel", "Statistics", "Power BI", "Data Visualization"],
    "Java Developer": ["Java", "OOP", "DSA", "SQL", "Spring Boot", "Git"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "Python", "SQL", "APIs"],
    "Cloud Engineer": ["Linux", "Networking", "Python", "AWS", "Docker", "Git"],
}
ALL_SKILLS = sorted({s for skills in ROLE_SKILLS.values() for s in skills} |
                    {"C", "C++", "Communication", "Problem Solving", "Machine Learning"})

JOB_CATEGORIES = ["Software & IT", "Data & Analytics", "Cybersecurity", "Cloud & DevOps", "Banking & Finance", "Accounting", "Government & Public Sector", "Healthcare", "Pharmaceuticals", "Teaching & Education", "Marketing", "Sales", "Human Resources", "Customer Support", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Architecture", "Graphic & UI/UX Design", "Media & Communications", "Logistics & Supply Chain", "Hospitality & Tourism", "Legal", "Research", "Operations", "Product Management"]
JOB_TITLES = ["Software Developer", "Frontend Developer", "Backend Developer", "Full Stack Developer", "Data Analyst", "Data Scientist", "Cybersecurity Analyst", "Cloud Engineer", "DevOps Engineer", "QA Engineer", "Business Analyst", "Accountant", "Financial Analyst", "Banking Associate", "Project Coordinator", "HR Executive", "Digital Marketing Executive", "Sales Associate", "Customer Success Specialist", "Teacher", "Nurse", "Lab Technician", "Mechanical Engineer", "Civil Engineer", "Electrical Engineer", "Graphic Designer", "UI/UX Designer", "Content Writer", "Operations Associate", "Research Assistant"]
# A broad illustrative directory: generated sample employer names, not real verified companies or vacancies.
_COMPANY_PREFIXES = ["Aster", "BluePeak", "Cedar", "Dawn", "Evergreen", "Futura", "Globe", "Horizon", "Indigo", "Juniper", "Keystone", "Lumen", "Meridian", "Nova", "Oakridge", "Pioneer", "Quantum", "Riverstone", "Summit", "Vertex", "Willow", "Zenith", "Apex", "BrightPath", "Core", "Delta", "Evolve", "Frontier", "Greenfield", "Helix", "Insight", "Jade", "Kinetic", "Luminary", "Metro", "Northstar", "Orbit", "Prime", "Quest", "Redwood", "Silverline", "TruNorth", "Unity", "Vantage", "Westbridge", "Yellowfin"]
_COMPANY_SUFFIXES = ["Technologies", "Solutions", "Systems", "Global", "Consulting", "Industries", "Services", "Group", "Labs", "Digital", "Enterprises", "Partners"]
COMPANIES = [{"name": f"{a} {b}", "category": JOB_CATEGORIES[i % len(JOB_CATEGORIES)], "roles": JOB_TITLES[i % len(JOB_TITLES)]} for i, (a,b) in enumerate(( (a,b) for a in _COMPANY_PREFIXES for b in _COMPANY_SUFFIXES))]

QUESTION_BANK = {
"Frontend Developer": [
("Which HTML element is used for the main navigation links?", ["<nav>", "<head>", "<meta>", "<footer>"], 0, "HTML"),
("Which CSS layout is one-dimensional?", ["Grid", "Flexbox", "Table", "Float"], 1, "CSS"),
("Which JavaScript keyword declares a block-scoped variable?", ["var", "let", "define", "dim"], 1, "JavaScript"),
("What does DOM stand for?", ["Data Object Model", "Document Object Model", "Digital Ordinance Model", "Document Order Map"], 1, "JavaScript"),
("Which CSS rule helps a page adapt to screen sizes?", ["@media", "@font-face", "@import-only", "@keyframes-only"], 0, "Responsive Design"),
("Which tool commonly tracks source-code changes?", ["Git", "Figma", "Excel", "Postman"], 0, "Git"),
],
"Python Developer": [
("Which Python structure stores key-value pairs?", ["List", "Tuple", "Dictionary", "Set"], 2, "Python"),
("Which keyword defines a function?", ["func", "def", "function", "method"], 1, "Python"),
("What is the purpose of a class?", ["Store only numbers", "Blueprint for objects", "Run SQL", "Style a page"], 1, "OOP"),
("Which HTTP method is commonly used to update a resource?", ["GET", "PUT", "TRACE", "HEAD"], 1, "APIs"),
("Which language is commonly used to query relational databases?", ["SQL", "CSS", "HTML", "XML"], 0, "SQL"),
("Flask is primarily a:", ["Python web framework", "Database", "Browser", "Operating system"], 0, "Flask"),
],
"Data Analyst": [
("Which SQL clause filters grouped results?", ["WHERE", "ORDER BY", "HAVING", "LIMIT"], 2, "SQL"),
("Which measure is most affected by extreme outliers?", ["Median", "Mode", "Mean", "Quartile"], 2, "Statistics"),
("Which chart is useful for comparing categories?", ["Bar chart", "Scatter plot only", "Map only", "Network graph"], 0, "Data Visualization"),
("In Excel, which function adds values meeting a condition?", ["COUNTBLANK", "SUMIF", "LEFT", "CONCAT"], 1, "Excel"),
("Which Python library is widely used for tabular data?", ["Pandas", "Turtle", "Tkinter", "Pygame"], 0, "Python"),
("Power BI is commonly used for:", ["Dashboards and reporting", "Writing operating systems", "Image editing", "Compiling Java"], 0, "Power BI"),
],
"Java Developer": [
("Which keyword creates a subclass in Java?", ["implements", "extends", "inherits", "superclass"], 1, "Java"),
("Which concept bundles data and methods together?", ["Encapsulation", "Iteration", "Compilation", "Indexing"], 0, "OOP"),
("Which data structure follows FIFO?", ["Stack", "Queue", "Tree", "Graph"], 1, "DSA"),
("Which SQL command retrieves rows?", ["SELECT", "INSERT", "DROP", "ALTER"], 0, "SQL"),
("Which collection does not allow duplicate elements?", ["ArrayList", "HashSet", "LinkedList", "Vector"], 1, "Java"),
("Git is used for:", ["Version control", "Database hosting", "Styling", "Testing hardware"], 0, "Git"),
],
"Full Stack Developer": [
("What does CSS primarily control?", ["Page presentation", "Database storage", "Server routing", "Authentication tokens"], 0, "CSS"),
("Which JavaScript feature handles asynchronous work?", ["Promises", "Selectors", "Classes only", "Comments"], 0, "JavaScript"),
("Which SQL command adds a row?", ["INSERT", "SELECT", "UPDATE", "GRANT"], 0, "SQL"),
("What is an API commonly used for?", ["Communication between software systems", "Drawing icons", "Compressing images", "Formatting disks"], 0, "APIs"),
("Which HTML attribute provides alternative text for an image?", ["href", "alt", "srcset", "target"], 1, "HTML"),
("Which language can be used for a Flask backend?", ["Python", "CSS", "HTML", "SVG"], 0, "Python"),
],
"Cloud Engineer": [
("Which command lists files in many Linux shells?", ["ls", "show", "dirlist", "files"], 0, "Linux"),
("What does DNS translate?", ["Domain names to IP addresses", "HTML to CSS", "Files to folders", "SQL to Python"], 0, "Networking"),
("Which AWS service provides virtual servers?", ["EC2", "S3", "Route 53", "CloudFront"], 0, "AWS"),
("Which tool packages applications into containers?", ["Docker", "Excel", "Figma", "Jupyter"], 0, "Docker"),
("Which protocol is commonly used for secure web traffic?", ["HTTPS", "FTP", "SMTP", "Telnet"], 0, "Networking"),
("Which language is useful for cloud automation?", ["Python", "CSS", "HTML", "Markdown"], 0, "Python"),
],
}

RESOURCES = {
"HTML": ("HTML Full Course", "https://www.youtube.com/results?search_query=HTML+full+course+beginner", "HTML and CSS: Design and Build Websites — Jon Duckett"),
"CSS": ("CSS Full Course", "https://www.youtube.com/results?search_query=CSS+full+course+beginner", "HTML and CSS: Design and Build Websites — Jon Duckett"),
"JavaScript": ("JavaScript Tutorial", "https://www.youtube.com/results?search_query=JavaScript+full+course", "Eloquent JavaScript — Marijn Haverbeke"),
"Python": ("Python Beginner Course", "https://www.youtube.com/results?search_query=Python+beginner+full+course", "Python Crash Course — Eric Matthes"),
"OOP": ("OOP Concepts", "https://www.youtube.com/results?search_query=OOP+concepts+tutorial", "Head First Object-Oriented Analysis and Design"),
"SQL": ("SQL Tutorial", "https://www.youtube.com/results?search_query=SQL+full+course", "Learning SQL — Alan Beaulieu"),
"DSA": ("Data Structures and Algorithms", "https://www.youtube.com/results?search_query=data+structures+algorithms+beginner", "Grokking Algorithms — Aditya Bhargava"),
"Statistics": ("Statistics for Data Analysis", "https://www.youtube.com/results?search_query=statistics+for+data+analysis", "Naked Statistics — Charles Wheelan"),
"Excel": ("Excel Beginner Tutorial", "https://www.youtube.com/results?search_query=Excel+beginner+tutorial", "Excel 365 Bible"),
"Power BI": ("Power BI Tutorial", "https://www.youtube.com/results?search_query=Power+BI+beginner+course", "The Definitive Guide to DAX — Marco Russo and Alberto Ferrari"),
"Data Visualization": ("Data Visualization Tutorial", "https://www.youtube.com/results?search_query=data+visualization+beginner", "Storytelling with Data — Cole Nussbaumer Knaflic"),
"Java": ("Java Full Course", "https://www.youtube.com/results?search_query=Java+full+course+beginner", "Head First Java — Kathy Sierra and Bert Bates"),
"Git": ("Git and GitHub Tutorial", "https://www.youtube.com/results?search_query=Git+GitHub+beginner+tutorial", "Pro Git — Scott Chacon and Ben Straub"),
"Flask": ("Flask Beginner Tutorial", "https://www.youtube.com/results?search_query=Python+Flask+beginner+tutorial", "Flask Web Development — Miguel Grinberg"),
"APIs": ("REST API Tutorial", "https://www.youtube.com/results?search_query=REST+API+beginner+tutorial", "API Design Patterns — JJ Geewax"),
"React": ("React Beginner Course", "https://www.youtube.com/results?search_query=React+beginner+course", "The Road to React — Robin Wieruch"),
"Responsive Design": ("Responsive Web Design", "https://www.youtube.com/results?search_query=responsive+web+design+CSS", "Responsive Web Design with HTML5 and CSS — Ben Frain"),
"Linux": ("Linux Command Line", "https://www.youtube.com/results?search_query=Linux+command+line+beginner", "The Linux Command Line — William Shotts"),
"Networking": ("Computer Networking Course", "https://www.youtube.com/results?search_query=computer+networking+course", "Computer Networking: A Top-Down Approach"),
"AWS": ("AWS Cloud Practitioner", "https://www.youtube.com/results?search_query=AWS+cloud+practitioner+course", "AWS Certified Cloud Practitioner Study Guide"),
"Docker": ("Docker Beginner Course", "https://www.youtube.com/results?search_query=Docker+beginner+course", "Docker Deep Dive — Nigel Poulton"),
}
def load_store():
    if not os.path.exists(DB_PATH):
        return {"users": [], "applications": [], "results": [], "jobs": [], "next_ids": {"users": 1, "applications": 1, "results": 1, "jobs": 1}}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in ("users", "applications", "results", "jobs"):
            data.setdefault(key, [])
        data.setdefault("next_ids", {"users": 1, "applications": 1, "results": 1, "jobs": 1})
        data["next_ids"].setdefault("jobs", 1)
        return data
    except (json.JSONDecodeError, OSError):
        return {"users": [], "applications": [], "results": [], "jobs": [], "next_ids": {"users": 1, "applications": 1, "results": 1, "jobs": 1}}

def save_store(data):
    temp = DB_PATH + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp, DB_PATH)

def add_record(collection, values):
    with _store_lock:
        data = load_store()
        record = dict(values)
        record["id"] = data["next_ids"][collection]
        data["next_ids"][collection] += 1
        data[collection].append(record)
        save_store(data)
        return record

def update_record(collection, record_id, user_id, values):
    with _store_lock:
        data = load_store()
        for row in data[collection]:
            if row.get("id") == record_id and row.get("user_id") == user_id:
                row.update(values)
                save_store(data)
                return True
        return False

def init_db():
    if not os.path.exists(DB_PATH):
        save_store({"users": [], "applications": [], "results": [], "jobs": [], "next_ids": {"users": 1, "applications": 1, "results": 1, "jobs": 1}})
init_db()

@app.context_processor
def inject_user():
    return {"current_user": current_user()}

def current_user():
    if not session.get("user_id"): return None
    data = load_store()
    return next((u for u in data["users"] if u["id"] == session["user_id"]), None)

def is_employer(user):
    return bool(user and user.get("account_type") == "employer")

def employer_required(user):
    if not user: return redirect(url_for("login"))
    if not is_employer(user):
        flash("This area is for employer accounts.", "error")
        return redirect(url_for("dashboard"))
    return None

def extract_resume_text(path):
    if not PdfReader: return ""
    try:
        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)[:20000]
    except Exception:
        return ""

def clean_skills(raw):
    return [s for s in ALL_SKILLS if re.search(r"(?<!\w)" + re.escape(s) + r"(?!\w)", raw, re.I)]

def analyse(user):
    resume = (user["resume_text"] or "") + " " + (user["skills"] or "")
    found = clean_skills(resume)
    needed = ROLE_SKILLS.get(user["target_role"], [])
    matched = [s for s in needed if s.lower() in [x.lower() for x in found]]
    missing = [s for s in needed if s not in matched]
    skill_score = (len(matched) / max(1, len(needed))) * 55
    text = (user["resume_text"] or "").lower()
    completeness_checks = [bool(re.search(r"\b(email|@)\b", text)), bool(re.search(r"\b(experience|internship|employment)\b", text)), bool(re.search(r"\b(education|university|college|degree)\b", text)), bool(re.search(r"\b(project|portfolio)\b", text)), bool(re.search(r"\b(summary|objective|profile)\b", text)), len(text.split()) >= 120]
    completeness_score = (sum(completeness_checks) / len(completeness_checks)) * 30 if text else 0
    action_score = 15 if (user["resume_file"] or user["skills"]) else 0
    score = round(min(100, skill_score + completeness_score + action_score))
    return found, matched, missing, score

@app.route("/")
def home():
    if current_user(): return redirect(url_for("employer_dashboard" if is_employer(current_user()) else "dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email, password = request.form.get("name","").strip(), request.form.get("email","").strip().lower(), request.form.get("password","")
        if not name or not email or len(password) < 6:
            flash("Enter your name, a valid email and a password of at least 6 characters.", "error")
        else:
            data = load_store()
            if any(u["email"] == email for u in data["users"]):
                flash("That email is already registered. Please sign in.", "error")
            else:
                account_type = request.form.get("account_type", "candidate")
                if account_type not in ["candidate", "employer"]: account_type = "candidate"
                if account_type == "employer" and not request.form.get("company_name", "").strip():
                    flash("Enter your company name for an employer account.", "error")
                    return render_template("auth.html", mode="Register")
                user = add_record("users", {"name":name, "email":email, "password":generate_password_hash(password), "account_type":account_type, "company_name":request.form.get("company_name", "").strip() if account_type == "employer" else "",
                    "education":"", "skills":"", "target_role":"Frontend Developer", "resume_text":"",
                    "resume_file":"", "created_at":datetime.now().isoformat(timespec="seconds")})
                session["user_id"] = user["id"]
                return redirect(url_for("employer_dashboard" if account_type == "employer" else "profile"))
    return render_template("auth.html", mode="Register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = load_store()
        user = next((u for u in data["users"] if u["email"] == request.form.get("email","").lower()), None)
        if user and check_password_hash(user["password"], request.form.get("password","")):
            session["user_id"] = user["id"]
            return redirect(url_for("employer_dashboard" if is_employer(user) else "dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("auth.html", mode="Login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = current_user()
    if not user: return redirect(url_for("login"))
    if request.method == "POST":
        skills = ", ".join(request.form.getlist("skills"))
        extra = request.form.get("extra_skills","").strip()
        if extra: skills = (skills + ", " + extra).strip(", ")
        with _store_lock:
            data = load_store()
            for row in data["users"]:
                if row["id"] == user["id"]:
                    row.update(education=request.form.get("education",""), skills=skills,
                               target_role=request.form.get("target_role","Frontend Developer"))
                    break
            save_store(data)
        flash("Your skills were saved. Now complete the task-based skill test to improve your job matches.", "success")
        return redirect(url_for("assessment", role=request.form.get("target_role", "Frontend Developer")))
    return render_template("profile.html", user=user, roles=list(ROLE_SKILLS), all_skills=ALL_SKILLS)

@app.route("/resume", methods=["GET", "POST"])
def resume():
    user = current_user()
    if not user: return redirect(url_for("login"))
    if request.method == "POST":
        f = request.files.get("resume")
        if not f or not f.filename.lower().endswith(".pdf"):
            flash("Please select a PDF resume.", "error")
            return redirect(url_for("resume"))
        filename = secure_filename(f"{user['id']}_{f.filename}")
        path = os.path.join(UPLOAD_DIR, filename)
        f.save(path)
        text = extract_resume_text(path)
        with _store_lock:
            data = load_store()
            for row in data["users"]:
                if row["id"] == user["id"]:
                    row.update(resume_file=filename, resume_text=text)
                    break
            save_store(data)
        flash("Resume uploaded. Review the extracted skills below; scanned PDFs may need manual skill entry.", "success")
        return redirect(url_for("resume"))
    found, matched, missing, score = analyse(user)
    return render_template("resume.html", user=user, found=found, matched=matched, missing=missing, score=score)

@app.route("/resume-builder", methods=["GET", "POST"])
def resume_builder():
    user = current_user()
    if not user: return redirect(url_for("login"))
    if request.method == "POST":
        data = {key: request.form.get(key, "").strip() for key in [
            "full_name", "email", "phone", "location", "linkedin", "github",
            "headline", "summary", "education", "experience", "projects", "skills", "certifications"
        ]}
        if not data["full_name"] or not data["email"] or not data["summary"]:
            flash("Please fill in your name, email and professional summary.", "error")
            return render_template("resume_builder.html", user=user, data=data)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="NameTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#6045a1"), alignment=0, spaceAfter=5))
        styles.add(ParagraphStyle(name="SectionHead", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#7556bd"), spaceBefore=13, spaceAfter=5))
        styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9, leading=13, textColor=colors.HexColor("#393342")))
        story = [Paragraph(data["full_name"], styles["NameTitle"])]
        contact = " | ".join(x for x in [data["email"], data["phone"], data["location"], data["linkedin"], data["github"]] if x)
        if contact: story += [Paragraph(contact.replace("&", "&amp;"), styles["BodySmall"]), Spacer(1, 8)]
        if data["headline"]: story.append(Paragraph(data["headline"].replace("&", "&amp;"), styles["Heading3"]))
        sections = [("PROFESSIONAL SUMMARY", "summary"), ("EDUCATION", "education"), ("EXPERIENCE", "experience"), ("PROJECTS", "projects"), ("SKILLS", "skills"), ("CERTIFICATIONS", "certifications")]
        for heading, key in sections:
            if data[key]:
                story.append(Paragraph(heading, styles["SectionHead"]))
                story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#e4dcf2"), spaceAfter=6))
                for line in data[key].splitlines():
                    line = line.strip()
                    if line:
                        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(safe, styles["BodySmall"]))
                        story.append(Spacer(1, 3))
        doc.build(story)
        buffer.seek(0)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", data["full_name"]).strip("_") or "My"
        return send_file(buffer, as_attachment=True, download_name=f"{safe_name}_Resume.pdf", mimetype="application/pdf")
    return render_template("resume_builder.html", user=user, data={})

@app.route("/save-resume-skills", methods=["POST"])
def save_resume_skills():
    user = current_user()
    if not user: return redirect(url_for("login"))
    skills = request.form.get("skills", "").strip()
    with _store_lock:
        data = load_store()
        for row in data["users"]:
            if row["id"] == user["id"]:
                row["skills"] = skills
                break
        save_store(data)
    flash("Resume skills saved. Your skill quiz is starting now.", "success")
    return redirect(url_for("assessment", role=user.get("target_role", "Frontend Developer")))

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user: return redirect(url_for("login"))
    found, matched, missing, score = analyse(user)
    data = load_store()
    apps = sorted([r for r in data["applications"] if r["user_id"] == user["id"]], key=lambda r:r["id"], reverse=True)[:5]
    results = sorted([r for r in data["results"] if r["user_id"] == user["id"]], key=lambda r:r["id"], reverse=True)[:5]
    app_count = sum(1 for r in data["applications"] if r["user_id"] == user["id"])
    return render_template("dashboard.html", user=user, found=found, matched=matched, missing=missing,
        score=score, apps=apps, results=results, app_count=app_count)

def questions_for_user(user, role):
    # Build a skill-focused quiz from questions tagged with skills the candidate entered.
    selected = [x.strip().lower() for x in (user.get("skills", "") or "").split(",") if x.strip()]
    pool = []
    for bank in QUESTION_BANK.values():
        for question in bank:
            if question[3].lower() in selected and question not in pool:
                pool.append(question)
    if len(pool) < 3:
        pool = list(QUESTION_BANK.get(role, QUESTION_BANK["Frontend Developer"]))
    rng = random.Random(f"{user.get('id', 0)}:{role}:{user.get('skills', '')}")
    rng.shuffle(pool)
    return pool[:min(10, max(6, len(pool)))]

@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    user = current_user()
    if not user: return redirect(url_for("login"))
    role = request.args.get("role") or user["target_role"]
    if role not in QUESTION_BANK: role = "Frontend Developer"
    questions = questions_for_user(user, role)
    if request.method == "POST":
        answers = request.form
        correct = sum(1 for i,q in enumerate(questions) if answers.get(f"q{i}") == str(q[2]))
        score = round(correct/len(questions)*100)
        add_record("results", {"user_id":user["id"], "role":role, "score":score, "total":len(questions),
                               "created_at":datetime.now().isoformat(timespec="seconds")})
        return render_template("result.html", role=role, score=score, correct=correct, total=len(questions),
            questions=questions, answers=answers, skills=[q[3] for q in questions])
    return render_template("assessment.html", role=role, questions=questions)

@app.route("/jobs")
def jobs():
    user = current_user()
    if not user: return redirect(url_for("login"))
    found, matched, missing, profile_score = analyse(user)
    data = load_store()
    latest_rows = sorted([r for r in data["results"] if r["user_id"] == user["id"]], key=lambda r:r["id"], reverse=True)
    latest = latest_rows[0] if latest_rows else None
    test_score = latest["score"] if latest else None
    roles = []
    for role, skills in ROLE_SKILLS.items():
        overlap = len(set(s.lower() for s in found) & set(s.lower() for s in skills))
        skill_match = round(overlap/max(1,len(skills))*100)
        assessment_component = test_score if latest and latest["role"] == role else 50
        match = round(skill_match*.65 + assessment_component*.35)
        roles.append({"role":role,"match":match,"skills":skills,"missing":[s for s in skills if s.lower() not in [x.lower() for x in found]]})
    roles.sort(key=lambda x:x["match"], reverse=True)
    q = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "")
    catalog = []
    for i, company in enumerate(COMPANIES):
        title = JOB_TITLES[i % len(JOB_TITLES)]
        cat = company["category"]
        item = {"company": company["name"], "role": title, "category": cat,
                "match": min(99, max(35, round(profile_score * .65 + (test_score or 50) * .35))),
                "skills": ROLE_SKILLS.get(user["target_role"], ["Communication", "Problem Solving"])}
        if (not q or q in company["name"].lower() or q in title.lower() or q in cat.lower()) and (not category or category == cat):
            catalog.append(item)
    posted_jobs = []
    for job in data.get("jobs", []):
        applied_count = sum(1 for a in data["applications"] if a.get("job_id") == job["id"])
        if (not q or q in job["title"].lower() or q in job["company"].lower() or q in job["category"].lower()) and (not category or category == job["category"]):
            required = [x.strip() for x in job.get("skills", "").split(",") if x.strip()]
            user_skills = [x.lower() for x in found]
            overlap = sum(1 for x in required if x.lower() in user_skills)
            job_match = round(overlap / max(1, len(required)) * 100) if required else 50
            posted_jobs.append({**job, "applied_count": applied_count, "match": job_match,
                                "already_applied": any(a.get("job_id") == job["id"] and a.get("user_id") == user["id"] for a in data["applications"])})
    return render_template("jobs.html", roles=roles, user=user, test_score=test_score,
                           catalog=catalog, posted_jobs=posted_jobs, categories=JOB_CATEGORIES, query=request.args.get("q", ""),
                           selected_category=category, company_count=len(COMPANIES))

@app.route("/applications", methods=["GET","POST"])
def applications():
    user = current_user()
    if not user: return redirect(url_for("login"))
    if request.method == "POST":
        job_id_raw = request.form.get("job_id", "").strip()
        job_id = int(job_id_raw) if job_id_raw.isdigit() else None
        if job_id:
            data = load_store()
            job = next((j for j in data.get("jobs", []) if j["id"] == job_id and j.get("active", True)), None)
            if not job:
                flash("This job is no longer available.", "error")
                return redirect(url_for("jobs"))
            if any(a.get("job_id") == job_id and a.get("user_id") == user["id"] for a in data["applications"]):
                flash("You have already applied for this job.", "error")
                return redirect(url_for("jobs"))
            company, role = job["company"], job["title"]
        else:
            company, role = request.form.get("company","").strip(), request.form.get("role","").strip()
        add_record("applications", {"user_id":user["id"], "company":company,
            "role":role, "job_id":job_id, "status":"Applied", "employer_note":"",
            "created_at":datetime.now().isoformat(timespec="seconds")})
        flash("Application added to your tracker.", "success")
        return redirect(url_for("applications"))
    data = load_store()
    rows = sorted([r for r in data["applications"] if r["user_id"] == user["id"]], key=lambda r:r["id"], reverse=True)
    return render_template("applications.html", rows=rows)

@app.route("/application/<int:app_id>/status", methods=["POST"])
def update_application(app_id):
    user = current_user()
    if not user: return redirect(url_for("login"))
    status = request.form.get("status")
    if status not in ["Applied","Shortlisted","Interview","Offer","Rejected"]: status = "Applied"
    data = load_store()
    row = next((r for r in data["applications"] if r["id"] == app_id and r["user_id"] == user["id"]), None)
    if row and not row.get("job_id"):
        update_record("applications", app_id, user["id"], {"status":status})
    return redirect(url_for("applications"))

@app.route("/learning")
def learning():
    user = current_user()
    if not user: return redirect(url_for("login"))
    found, matched, missing, score = analyse(user)
    items = []
    for skill in missing:
        title, link, book = RESOURCES.get(skill, (f"{skill} tutorial", f"https://www.youtube.com/results?search_query={skill.replace(' ','+')}+tutorial", "Search for a beginner-friendly reference book"))
        items.append({"skill":skill,"title":title,"link":link,"book":book})
    return render_template("learning.html", items=items, found=found, matched=matched)

@app.route("/chat", methods=["GET","POST"])
def chat():
    user = current_user()
    if not user: return redirect(url_for("login"))
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip().lower()
        if not message:
            return jsonify({"reply": "Tell me what you want help with: jobs, skills, resume marks, interviews or your task test."})
        found, matched, missing, score = analyse(user)
        role = user["target_role"]
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                import urllib.request
                model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
                body = {"model": model, "messages": [
                    {"role": "system", "content": f"You are CareerBloom, a practical job and resume mentor. User target role: {role}. Education: {user.get('education','')}. Skills: {user.get('skills','')}. Resume skills found: {', '.join(found)}. Missing target-role skills: {', '.join(missing)}. Give concise, actionable, honest guidance. Do not claim sample jobs are verified vacancies."},
                    {"role": "user", "content": str(payload.get("message", ""))[:2000]}], "temperature": 0.5}
                req = urllib.request.Request(os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions", data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=25) as response:
                    ai_data = json.loads(response.read().decode())
                ai_reply = ai_data["choices"][0]["message"]["content"].strip()
                return jsonify({"reply": ai_reply, "mode": "ai"})
            except Exception:
                pass
        if any(w in message for w in ["skill", "improve", "learn", "weak"]):
            reply = f"For {role}, your profile shows {score}/100 resume-readiness points. Skills already identified: {', '.join(found) if found else 'none yet'}. Your next focus areas are: {', '.join(missing) if missing else 'build projects and practise interviews'}. Open Learning Hub for a study plan."
        elif any(w in message for w in ["job", "role", "career", "company", "match"]):
            reply = f"I can match you across {len(COMPANIES)} sample employer profiles and {len(JOB_CATEGORIES)} job sectors. Your current target is {role}. Open Job Matches and filter by title, employer or sector. These directory entries are illustrative and are not confirmed live vacancies."
        elif any(w in message for w in ["resume", "ats", "cv", "mark", "score"]):
            reply = f"Your current resume-readiness score is {score}/100. Improve it with a clear summary, contact details, education, relevant skills, projects and measurable experience. Use the Resume Analyzer to see detected skills and gaps."
        elif any(w in message for w in ["interview", "test", "assessment", "task"]):
            reply = f"Your {role} task test is available from Skill Test. It contains role-related questions with a timer. Read each task carefully, submit your answers, then review the explanations and retake after practising."
        elif any(w in message for w in ["salary", "pay", "package"]):
            reply = "Pay varies by location, seniority, employer and role. Compare current salary ranges from reliable local job listings and check whether figures are gross or net."
        elif any(w in message for w in ["hello", "hi", "hey"]):
            reply = f"Hi {user['name'].split()[0]}! I'm your CareerBloom career assistant. Ask me about job sectors, company matching, resume marks, skills or task tests."
        else:
            reply = ("The AI chatbot is not configured yet, so I can only answer a limited set of career questions. "
                     "Ask the portal administrator to configure OPENAI_API_KEY on the server to enable open-ended questions. "
                     "For now, try asking about skills, jobs, resume score, interviews or assessments.")
        return jsonify({"reply": reply, "mode": "limited"})
    return render_template("chat.html", user=user)


@app.route("/employer")
def employer_dashboard():
    user = current_user()
    guard = employer_required(user)
    if guard: return guard
    data = load_store()
    my_jobs = [j for j in data.get("jobs", []) if j.get("employer_id") == user["id"]]
    applications = [a for a in data["applications"] if any(j["id"] == a.get("job_id") for j in my_jobs)]
    candidate_map = {u["id"]: {"name": u.get("name", "Candidate"), "email": u.get("email", ""), "skills": u.get("skills", ""), "education": u.get("education", "")} for u in data["users"]}
    return render_template("employer.html", user=user, jobs=my_jobs, applications=applications, candidate_map=candidate_map,
                           applicants_count=len(applications), open_seats=sum(max(0, int(j.get("seats", 0)) - sum(1 for a in applications if a.get("job_id")==j["id"] and a.get("status")=="Accepted")) for j in my_jobs))

@app.route("/employer/jobs/new", methods=["GET", "POST"])
def employer_new_job():
    user = current_user()
    guard = employer_required(user)
    if guard: return guard
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        skills = request.form.get("skills", "").strip()
        try: seats = max(1, min(10000, int(request.form.get("seats", "1"))))
        except ValueError: seats = 1
        if not title or not category or not skills:
            flash("Add a job title, category and required skills.", "error")
        else:
            add_record("jobs", {"employer_id":user["id"], "company":user["company_name"], "title":title,
                "category":category, "skills":skills, "description":request.form.get("description", "").strip(),
                "seats":seats, "active":True, "created_at":datetime.now().isoformat(timespec="seconds")})
            flash("Your job vacancy is now published.", "success")
            return redirect(url_for("employer_dashboard"))
    return render_template("employer_job.html", categories=JOB_CATEGORIES)

@app.route("/employer/application/<int:app_id>/decision", methods=["POST"])
def employer_decision(app_id):
    user = current_user()
    guard = employer_required(user)
    if guard: return guard
    status = request.form.get("status", "Waiting")
    if status not in ["Accepted", "Rejected", "Waiting"]: status = "Waiting"
    note = request.form.get("note", "").strip()[:500]
    with _store_lock:
        data = load_store()
        own_job_ids = {j["id"] for j in data.get("jobs", []) if j.get("employer_id") == user["id"]}
        row = next((a for a in data["applications"] if a["id"] == app_id and a.get("job_id") in own_job_ids), None)
        if row:
            row.update(status=status, employer_note=note)
            save_store(data)
    flash("Applicant decision saved.", "success")
    return redirect(url_for("employer_dashboard"))

@app.route("/health")
def health():
    return jsonify({"status":"ok","app":"Smart Resume & Job Portal"})

if __name__ == "__main__":
    # 0.0.0.0 makes the site reachable from phones on the same Wi-Fi.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
