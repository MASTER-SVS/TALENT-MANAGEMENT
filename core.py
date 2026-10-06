"""Local-first career platform logic and SQLite persistence."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "talentsphere.db"))
ROLE_CATALOG: dict[str, dict[str, Any]] = {
    "Senior Software Engineer": {"skills": {"Python": 4, "System Design": 3, "SQL": 3, "Cloud": 2, "Communication": 3}, "experience": 4, "department": "Engineering", "criteria": "Owns technical design, mentors peers, and delivers reliable systems."},
    "Technical Lead": {"skills": {"System Design": 4, "Python": 4, "Leadership": 4, "Cloud": 3, "Communication": 4}, "experience": 6, "department": "Engineering", "criteria": "Leads delivery, architecture decisions, and team development."},
    "Engineering Manager": {"skills": {"Leadership": 4, "Communication": 4, "Project Management": 3, "System Design": 3}, "experience": 7, "department": "Engineering", "criteria": "Builds teams, sets direction, and improves delivery outcomes."},
    "Data Analyst": {"skills": {"SQL": 3, "Python": 2, "Data Visualization": 3, "Communication": 3}, "experience": 1, "department": "Analytics", "criteria": "Produces trusted analysis and communicates actionable insights."},
    "Senior Data Analyst": {"skills": {"SQL": 4, "Python": 3, "Data Visualization": 4, "Statistics": 3, "Communication": 4}, "experience": 4, "department": "Analytics", "criteria": "Owns analytical projects and advises stakeholders."},
    "Business Analyst": {"skills": {"Requirements Analysis": 3, "SQL": 2, "Communication": 3, "Process Improvement": 3}, "experience": 1, "department": "Business", "criteria": "Maps needs into clear requirements and measurable outcomes."},
    "Senior Business Analyst": {"skills": {"Requirements Analysis": 4, "SQL": 3, "Communication": 4, "Process Improvement": 4, "Leadership": 2}, "experience": 4, "department": "Business", "criteria": "Leads complex analysis and aligns cross-functional teams."},
    "HR Manager": {"skills": {"Talent Management": 4, "Communication": 4, "Leadership": 4, "Analytics": 3, "Employment Law": 3}, "experience": 5, "department": "Human Resources", "criteria": "Leads people programs and improves workforce outcomes."},
    "Project Manager": {"skills": {"Project Management": 4, "Communication": 4, "Risk Management": 3, "Leadership": 3}, "experience": 3, "department": "Operations", "criteria": "Delivers cross-functional projects on time, scope, and budget."},
    "SAP Consultant": {"skills": {"SAP": 4, "Requirements Analysis": 3, "Communication": 3, "Process Improvement": 3}, "experience": 2, "department": "Technology", "criteria": "Configures business systems and delivers adoption outcomes."},
}
LEVELS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, phone TEXT DEFAULT '', location TEXT DEFAULT '', job_title TEXT DEFAULT '', department TEXT DEFAULT '', company TEXT DEFAULT '', industry TEXT DEFAULT '', employment_type TEXT DEFAULT '', years_experience REAL DEFAULT 0, summary TEXT DEFAULT '', linkedin TEXT DEFAULT '', github TEXT DEFAULT '', portfolio TEXT DEFAULT '', target_role TEXT DEFAULT '', target_level TEXT DEFAULT '', target_industry TEXT DEFAULT '', timeline TEXT DEFAULT '', career_goal TEXT DEFAULT '', education TEXT DEFAULT '', certifications TEXT DEFAULT '', projects TEXT DEFAULT '', experience TEXT DEFAULT '', resume_text TEXT DEFAULT '', updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS skills(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, category TEXT NOT NULL, proficiency TEXT NOT NULL, years REAL DEFAULT 0, UNIQUE(user_id,name));
        CREATE TABLE IF NOT EXISTS assessments(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, category TEXT NOT NULL, score INTEGER NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS progress(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, item TEXT NOT NULL, percent INTEGER NOT NULL, status TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(user_id,item));
        """)


def _password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        return hmac.compare_digest(_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1], digest_hex)
    except (ValueError, TypeError):
        return False


def register(name: str, email: str, password: str) -> tuple[bool, str]:
    name, email = name.strip(), email.strip().lower()
    if not name or "@" not in email or len(password) < 8:
        return False, "Enter a name, valid email, and password with at least 8 characters."
    try:
        with connect() as db:
            cur = db.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)", (name, email, _password(password), datetime.now().isoformat()))
            db.execute("INSERT INTO profiles(user_id,updated_at) VALUES(?,?)", (cur.lastrowid, datetime.now().isoformat()))
        return True, "Account created. You can sign in now."
    except sqlite3.IntegrityError:
        return False, "An account with that email already exists."


def login(email: str, password: str) -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if row and verify_password(password, row["password_hash"]):
        return {"id": row["id"], "name": row["name"], "email": row["email"]}
    return None


PROFILE_FIELDS = ["phone", "location", "job_title", "department", "company", "industry", "employment_type", "years_experience", "summary", "linkedin", "github", "portfolio", "target_role", "target_level", "target_industry", "timeline", "career_goal", "education", "certifications", "projects", "experience", "resume_text"]


def get_profile(user_id: int) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT u.name,u.email,p.* FROM users u JOIN profiles p ON u.id=p.user_id WHERE u.id=?", (user_id,)).fetchone()
    return dict(row) if row else {}


def save_profile(user_id: int, values: dict[str, Any]) -> None:
    fields = [f for f in PROFILE_FIELDS if f in values]
    if not fields:
        return
    sql = ",".join(f"{f}=?" for f in fields) + ",updated_at=?"
    with connect() as db:
        db.execute(f"UPDATE profiles SET {sql} WHERE user_id=?", [values[f] for f in fields] + [datetime.now().isoformat(), user_id])


def list_skills(user_id: int) -> list[dict[str, Any]]:
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM skills WHERE user_id=? ORDER BY category,name", (user_id,))]


def add_skill(user_id: int, name: str, category: str, proficiency: str, years: float) -> tuple[bool, str]:
    try:
        with connect() as db:
            db.execute("INSERT INTO skills(user_id,name,category,proficiency,years) VALUES(?,?,?,?,?)", (user_id, name.strip(), category, proficiency, years))
        return True, "Skill added."
    except sqlite3.IntegrityError:
        return False, "That skill is already in your profile."


def delete_skill(user_id: int, skill_id: int) -> None:
    with connect() as db:
        db.execute("DELETE FROM skills WHERE id=? AND user_id=?", (skill_id, user_id))


def add_assessment(user_id: int, category: str, score: int) -> None:
    with connect() as db:
        db.execute("INSERT INTO assessments(user_id,category,score,created_at) VALUES(?,?,?,?)", (user_id, category, score, date.today().isoformat()))


def get_assessments(user_id: int) -> list[dict[str, Any]]:
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM assessments WHERE user_id=? ORDER BY created_at DESC", (user_id,))]


def save_progress(user_id: int, item: str, percent: int) -> None:
    with connect() as db:
        db.execute("INSERT INTO progress(user_id,item,percent,status,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(user_id,item) DO UPDATE SET percent=excluded.percent,status=excluded.status,updated_at=excluded.updated_at", (user_id, item, percent, "Complete" if percent == 100 else "In progress", date.today().isoformat()))


def get_progress(user_id: int) -> list[dict[str, Any]]:
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM progress WHERE user_id=? ORDER BY item", (user_id,))]


def profile_completion(profile: dict[str, Any], skills: list[dict[str, Any]]) -> tuple[int, list[str]]:
    checks = {"Phone and location": bool(profile.get("phone") and profile.get("location")), "Current role and employer": bool(profile.get("job_title") and profile.get("company")), "Professional summary": bool(profile.get("summary")), "Education": bool(profile.get("education")), "Skills": bool(skills), "Experience": bool(profile.get("experience")), "Certifications": bool(profile.get("certifications")), "Projects": bool(profile.get("projects")), "Career goal and target role": bool(profile.get("career_goal") and profile.get("target_role")), "Professional link": bool(profile.get("linkedin") or profile.get("github") or profile.get("portfolio")), "Resume content": bool(profile.get("resume_text"))}
    missing = [label for label, done in checks.items() if not done]
    return round(100 * (len(checks) - len(missing)) / len(checks)), missing


def gap_analysis(target_role: str, skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required = ROLE_CATALOG.get(target_role, {}).get("skills", {})
    current = {s["name"].strip().lower(): LEVELS.get(s["proficiency"], 1) for s in skills}
    result = []
    for skill, level in required.items():
        have = current.get(skill.lower(), 0)
        gap = max(0, level - have)
        result.append({"skill": skill, "current": have, "required": level, "gap": gap, "priority": "High" if gap >= 2 else "Medium" if gap == 1 else "On track"})
    return sorted(result, key=lambda x: x["gap"], reverse=True)


def recommendations(profile: dict[str, Any], skills: list[dict[str, Any]]) -> list[dict[str, str]]:
    completion, missing = profile_completion(profile, skills)
    gaps = gap_analysis(profile.get("target_role", ""), skills)
    items = []
    if completion < 80:
        items.append({"priority": "High", "title": "Complete your professional profile", "description": f"Add the missing sections: {', '.join(missing[:4])}. This gives the career matching engine better evidence."})
    for gap in gaps:
        if gap["gap"]:
            items.append({"priority": gap["priority"], "title": f"Develop {gap['skill']}", "description": f"Your target role expects level {gap['required']}; your recorded level is {gap['current']}. Choose a practical project or learning path to build evidence."})
    if not profile.get("resume_text"):
        items.append({"priority": "Medium", "title": "Create a role-aligned resume", "description": "Use your profile details to draft an ATS-friendly resume and add measurable outcomes drawn from your actual work."})
    if not items:
        items.append({"priority": "Medium", "title": "Build evidence for your next step", "description": "Document a recent project with scope, your contribution, and measurable impact. Revisit your target role quarterly."})
    return items[:8]


def profile_analysis(profile: dict[str, Any], skills: list[dict[str, Any]]) -> dict[str, Any]:
    completion, missing = profile_completion(profile, skills)
    gaps = gap_analysis(profile.get("target_role", ""), skills)
    strength = min(100, round(completion * .55 + min(len(skills) * 4, 24) + (12 if profile.get("summary") else 0) + (9 if profile.get("experience") else 0)))
    strengths = []
    if skills: strengths.append(f"A skills profile with {len(skills)} recorded capabilities")
    if profile.get("experience"): strengths.append("Work history is documented")
    if profile.get("projects"): strengths.append("Project evidence is available")
    if not strengths: strengths.append("A clear opportunity to build a complete career baseline")
    weaknesses = [f"Missing profile evidence: {', '.join(missing[:3])}"] if missing else []
    weaknesses += [f"{g['skill']} is {g['gap']} level(s) below target" for g in gaps if g["gap"]][:3]
    return {"score": strength, "completion": completion, "strengths": strengths, "weaknesses": weaknesses or ["Keep adding recent evidence and measurable outcomes."], "recommendations": [r["title"] for r in recommendations(profile, skills)[:4]]}


def role_match(target_role: str, skills: list[dict[str, Any]], years: float = 0) -> int:
    spec = ROLE_CATALOG.get(target_role)
    if not spec: return 0
    required = spec["skills"]
    levels = {s["name"].lower(): LEVELS.get(s["proficiency"], 1) for s in skills}
    fit = sum(min(levels.get(name.lower(), 0), level) / level for name, level in required.items()) / max(1, len(required))
    exp_fit = min(1, years / max(1, spec["experience"]))
    return round(100 * (fit * .85 + exp_fit * .15))


def export_user_data(user_id: int) -> dict[str, Any]:
    profile = get_profile(user_id)
    with connect() as db:
        user = db.execute("SELECT name,email,created_at FROM users WHERE id=?", (user_id,)).fetchone()
    return {"employee": dict(user) if user else {}, "profile": profile, "skills": list_skills(user_id), "assessments": get_assessments(user_id), "progress": get_progress(user_id), "generated_at": datetime.now().isoformat()}
