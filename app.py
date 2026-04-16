import os
import random
import io
from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "exam_secret_key_change_in_prod")

# ── MongoDB Connection ──────────────────────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI", "")

_mongo_client = None

def get_client():
    global _mongo_client
    if _mongo_client is None:
        if not MONGO_URI:
            raise RuntimeError("MONGO_URI is not set. Please add it to your .env file.")
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _mongo_client

def get_db():
    return get_client()["exam_system"]


# ── Seed sample questions if DB is empty ────────────────────────────────────────
def seed_questions():
    try:
        db = get_db()
        if db.questions.count_documents({}) == 0:
            print("Seeding sample questions...")
    except Exception as e:
        print(f"⚠️  Could not connect to MongoDB: {e}")
        print("   Check your MONGO_URI in .env file.")
        return

    if db.questions.count_documents({}) == 0:
        sample = [
            {
                "question": "What does HTML stand for?",
                "option_a": "Hyper Text Markup Language",
                "option_b": "High Tech Modern Language",
                "option_c": "Hyper Transfer Markup Language",
                "option_d": "Home Tool Markup Language",
                "correct_option": "A",
            },
            {
                "question": "Which language is used for styling web pages?",
                "option_a": "HTML",
                "option_b": "Python",
                "option_c": "CSS",
                "option_d": "Java",
                "correct_option": "C",
            },
            {
                "question": "Which of the following is a NoSQL database?",
                "option_a": "MySQL",
                "option_b": "PostgreSQL",
                "option_c": "SQLite",
                "option_d": "MongoDB",
                "correct_option": "D",
            },
            {
                "question": "What does CPU stand for?",
                "option_a": "Central Processing Unit",
                "option_b": "Computer Personal Unit",
                "option_c": "Central Peripheral Utility",
                "option_d": "Core Processing Utility",
                "correct_option": "A",
            },
            {
                "question": "Which symbol is used for comments in Python?",
                "option_a": "//",
                "option_b": "/* */",
                "option_c": "#",
                "option_d": "--",
                "correct_option": "C",
            },
        ]
        db.questions.insert_many(sample)
        print(f"✅ Seeded {len(sample)} sample questions.")


# ── Helper: convert MongoDB doc to tuple-like list for templates ────────────────
def doc_to_row(doc):
    """Return a list [id, question, a, b, c, d, correct] matching old tuple format."""
    return [
        str(doc["_id"]),
        doc.get("question", ""),
        doc.get("option_a", ""),
        doc.get("option_b", ""),
        doc.get("option_c", ""),
        doc.get("option_d", ""),
        doc.get("correct_option", ""),
    ]


# ── Error Handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(500)
def internal_error(e):
    return f"""
    <div style="font-family:sans-serif;text-align:center;margin-top:80px;">
      <h2>⚠️ Server Error</h2>
      <p>{str(e)}</p>
      <p>Check that your <b>MONGO_URI</b> in <b>.env</b> is correct.</p>
      <a href="/">Go Home</a>
    </div>""", 500


# ── LOGIN ───────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            error = "Username cannot be empty."
        else:
            session.clear()
            session["user"] = username
            return redirect("/exam")
    return render_template("login.html", error=error)


# ── EXAM ────────────────────────────────────────────────────────────────────────
@app.route("/exam", methods=["GET", "POST"])
def exam():
    if "user" not in session:
        return redirect("/")

    db = get_db()

    # Randomize & cache in session once per attempt
    if "questions" not in session:
        docs = list(db.questions.find())
        random.shuffle(docs)
        questions = [doc_to_row(d) for d in docs]
        session["questions"] = questions
    else:
        questions = session["questions"]

    if not questions:
        return render_template(
            "exam.html",
            questions=[],
            error="No questions found. Please ask the admin to add questions.",
        )

    if request.method == "POST":
        score = 0.0
        for q in questions:
            qid = q[0]
            correct = q[6]
            ans = request.form.get(qid)
            if ans == correct:
                score += 1
            elif ans is not None:
                score -= 0.25          # negative marking

        db.results.insert_one({
            "username": session["user"],
            "score": round(score, 2),
            "total": len(questions),
            "timestamp": datetime.utcnow(),
        })
        session["last_score"] = round(score, 2)
        session["total_questions"] = len(questions)
        session.pop("questions", None)   # clear for next attempt
        return redirect("/result")

    return render_template("exam.html", questions=questions)


# ── RESULT ──────────────────────────────────────────────────────────────────────
@app.route("/result")
def result():
    if "user" not in session:
        return redirect("/")

    score = session.get("last_score")
    total = session.get("total_questions", 0)

    if score is None:
        # Fallback: fetch latest from DB
        db = get_db()
        rec = db.results.find_one(
            {"username": session["user"]}, sort=[("timestamp", -1)]
        )
        if rec:
            score = rec["score"]
            total = rec.get("total", 0)
        else:
            return redirect("/")

    return render_template("result.html", score=score, total=total)


# ── ADMIN LOGIN ─────────────────────────────────────────────────────────────────
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        admin_user = os.environ.get("ADMIN_USERNAME", "admin")
        admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
        if username == admin_user and password == admin_pass:
            session["admin"] = username
            return redirect("/admin")
        error = "Invalid credentials."
    return render_template("admin_login.html", error=error)


# ── ADMIN DASHBOARD ─────────────────────────────────────────────────────────────
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect("/admin_login")

    db = get_db()
    success = None
    error = None

    if request.method == "POST":
        q = request.form.get("q", "").strip()
        a = request.form.get("a", "").strip()
        b = request.form.get("b", "").strip()
        c = request.form.get("c", "").strip()
        d = request.form.get("d", "").strip()
        correct = request.form.get("correct", "").strip().upper()

        if not all([q, a, b, c, d, correct]) or correct not in ("A", "B", "C", "D"):
            error = "All fields are required and correct option must be A, B, C or D."
        else:
            db.questions.insert_one({
                "question": q,
                "option_a": a,
                "option_b": b,
                "option_c": c,
                "option_d": d,
                "correct_option": correct,
                "created_at": datetime.utcnow(),
            })
            success = "Question added successfully!"

    questions = [doc_to_row(d) for d in db.questions.find()]
    results = list(db.results.find({}, {"_id": 0}))
    return render_template(
        "admin.html",
        questions=questions,
        results=results,
        success=success,
        error=error,
    )


# ── DELETE QUESTION ─────────────────────────────────────────────────────────────
@app.route("/delete_question/<qid>", methods=["POST"])
def delete_question(qid):
    if "admin" not in session:
        return redirect("/admin_login")
    db = get_db()
    try:
        db.questions.delete_one({"_id": ObjectId(qid)})
    except Exception:
        pass
    return redirect("/admin")


# ── EXPORT RESULTS TO EXCEL ─────────────────────────────────────────────────────
@app.route("/export")
def export():
    if "admin" not in session:
        return "Access Denied", 403

    db = get_db()
    data = list(db.results.find({}, {"_id": 0}))

    if not data:
        return "No results to export.", 404

    df = pd.DataFrame(data)
    df.rename(columns={"username": "Username", "score": "Score",
                        "total": "Total Questions", "timestamp": "Timestamp"}, inplace=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="results.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ── CERTIFICATE ─────────────────────────────────────────────────────────────────
@app.route("/certificate")
def certificate():
    if "user" not in session:
        return redirect("/")

    score = session.get("last_score", 0)
    username = session["user"]

    output = io.BytesIO()
    styles = getSampleStyleSheet()
    pdf = SimpleDocTemplate(output, pagesize=letter)

    content = [
        Paragraph("🎓 Certificate of Completion", styles["Title"]),
        Spacer(1, 30),
        Paragraph(f"This is to certify that <b>{username}</b>", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(
            "has successfully completed the <b>Online Examination</b>.", styles["Normal"]
        ),
        Spacer(1, 12),
        Paragraph(f"Score Achieved: <b>{score}</b>", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(
            f"Date: {datetime.utcnow().strftime('%d %B %Y')}", styles["Normal"]
        ),
    ]
    pdf.build(content)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f"certificate_{username}.pdf",
        mimetype="application/pdf",
    )


# ── PROCTORING LOG ──────────────────────────────────────────────────────────────
@app.route("/log", methods=["POST"])
def log():
    if "user" not in session:
        return "Unauthorized", 401

    db = get_db()
    activity = request.form.get("activity", "unknown")
    db.logs.insert_one({
        "username": session["user"],
        "activity": activity,
        "timestamp": datetime.utcnow(),
    })
    return "logged", 200


# ── LOGOUT ──────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ── ENTRY POINT ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting Flask server with MongoDB Atlas...")
    if not MONGO_URI:
        print("❌ ERROR: MONGO_URI is not set in your .env file!")
        print("   Copy .env.example to .env and fill in your MongoDB Atlas connection string.")
    else:
        seed_questions()
    app.run(debug=True)