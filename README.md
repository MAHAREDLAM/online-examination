# 📝 Online Examination System

A **Flask + MongoDB Atlas** based online examination system with proctoring, negative marking, certificate generation, and an admin dashboard.

---

## 🚀 Features

| Feature | Details |
|---|---|
| 🔐 Student Login | Name/roll number based login, no password needed |
| 📋 Random Questions | Questions shuffled per session from MongoDB |
| ⏱ Timed Exam | 10-minute countdown, auto-submits on timeout |
| 🧮 Negative Marking | +1 for correct, −0.25 for wrong, 0 for unattempted |
| 🎓 Certificate | PDF certificate generated for passing students (≥50%) |
| 📊 Admin Dashboard | Add/delete questions, view all student results |
| 📥 Excel Export | Download results as `.xlsx` |
| 🛡 Proctoring | Tab-switch, copy, right-click, keyboard shortcut detection |
| ☁️ MongoDB Atlas | Cloud-hosted NoSQL database |

---

## 🗂 Project Structure

```
exam_mongodb/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel deployment config
├── .env.example           # Environment variable template
├── .gitignore
├── static/
│   └── Style.css          # Stylesheet
└── templates/
    ├── login.html          # Student login page
    ├── exam.html           # Exam interface
    ├── result.html         # Score display
    ├── admin_login.html    # Admin login
    └── admin.html          # Admin dashboard
```

---

## ⚙️ Local Setup (Step-by-Step)

### Prerequisites
- Python 3.9+
- A free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account

---

### Step 1 — Clone / Download the Project

```bash
git clone https://github.com/your-username/exam-system.git
cd exam-system
```

Or just download and extract the zip.

---

### Step 2 — Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Set Up MongoDB Atlas

1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com) and sign in (or register free).
2. Click **"Build a Database"** → choose **Free (M0 Shared)** → any cloud provider → **Create**.
3. Set a **username** and **password** (save these!).
4. Under **"Network Access"** → **Add IP Address** → click **"Allow Access from Anywhere"** (`0.0.0.0/0`) → Confirm.
5. Go to **Database** → Click **"Connect"** on your cluster → **"Drivers"**.
6. Copy the **connection string** — it looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
   ```

---

### Step 5 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
MONGO_URI=mongodb+srv://youruser:yourpassword@cluster0.xxxxx.mongodb.net/exam_system?retryWrites=true&w=majority
SECRET_KEY=any_long_random_string_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

> ⚠️ **Never commit `.env` to Git.** It's already in `.gitignore`.

---

### Step 6 — Run the App

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

On first run, 5 sample questions are automatically seeded into the database.

---

## 🧪 Test Cases — Verified Scenarios

### ✅ Student Flow
| Test | Expected Result |
|---|---|
| Open `/` | Login page shows |
| Submit empty username | Browser validation blocks it |
| Submit valid username | Redirected to `/exam` |
| Questions displayed | Randomized each session |
| Click palette number | Jumps to that question |
| Click Next/Previous | Navigates correctly |
| Answer a question | Palette button turns green |
| Submit with unanswered | Confirmation dialog shown |
| Submit exam | Score calculated, saved to DB, redirect to `/result` |
| View result | Score and percentage shown |
| Score ≥ 50% | Certificate download button visible |
| Download certificate | PDF downloaded with name and score |
| Logout | Session cleared, back to login |

### ✅ Proctoring
| Test | Expected Result |
|---|---|
| Switch tab | Alert shown, activity logged in MongoDB |
| Right-click on exam page | Blocked, logged |
| Ctrl+C on exam page | Blocked, alerted, logged |
| Timer reaches 0 | Auto-submit triggered |

### ✅ Admin Flow
| Test | Expected Result |
|---|---|
| Visit `/admin` without login | Redirected to `/admin_login` |
| Wrong credentials | Error message shown |
| Correct credentials | Dashboard loads |
| Add question with blank fields | Error message shown |
| Add question with valid data | Success message, question appears in table |
| Add question with invalid correct option | Error message shown |
| Delete question | Question removed from list |
| Click "Download Results" | `.xlsx` file downloaded |
| Logout | Session cleared |

### ✅ Edge Cases
| Test | Expected Result |
|---|---|
| Visit `/exam` without login | Redirected to `/` |
| Visit `/result` without exam | Redirected to `/` |
| Admin visits `/export` when no results | Returns 404 message |
| No questions in DB | Exam shows friendly error message |

---

## 🌐 Deploy to Vercel (Step-by-Step)

> **Note:** Vercel runs serverless functions. Flask apps work but some limitations apply (no persistent file storage — that's why we use MongoDB Atlas and in-memory BytesIO for file generation).

### Step 1 — Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/exam-system.git
git push -u origin main
```

### Step 2 — Import to Vercel

1. Go to [https://vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **"Add New Project"** → select your repository.
3. Vercel auto-detects Python. Leave settings as-is (it reads `vercel.json`).

### Step 3 — Set Environment Variables in Vercel

In the Vercel project settings → **Environment Variables**, add:

| Name | Value |
|---|---|
| `MONGO_URI` | `mongodb+srv://user:pass@cluster.mongodb.net/exam_system?...` |
| `SECRET_KEY` | Any long random string |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | Your secure password |

### Step 4 — Deploy

Click **"Deploy"**. Wait ~60 seconds. Your app will be live at:
```
https://your-project-name.vercel.app
```

### Step 5 — Seed Questions

After deployment, visit `/admin_login` → log in as admin → add questions manually from the dashboard. (The auto-seeder runs on first local start; on Vercel serverless, add via the admin panel.)

---

## 🔒 Security Notes

- Change `ADMIN_PASSWORD` from the default `admin123` before deploying.
- Set `SECRET_KEY` to a long random string (e.g., `python -c "import secrets; print(secrets.token_hex(32))"`)
- Use MongoDB Atlas **Network Access** to restrict IPs in production if needed.
- Do **not** commit `.env` to Git.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | MongoDB Atlas (via PyMongo) |
| Frontend | Jinja2 Templates, HTML5, CSS3, Vanilla JS |
| PDF | ReportLab |
| Excel | Pandas + openpyxl |
| Deployment | Vercel (Serverless) |

---

## 📬 Admin Credentials (default)

```
Username: admin
Password: admin123
```
> Change these via environment variables before going live!
