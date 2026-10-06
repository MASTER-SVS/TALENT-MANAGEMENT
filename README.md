# TalentSphere — Employee Career Growth Platform

TalentSphere is a local-first, Python-only Streamlit application for building a professional profile, setting a target role, comparing current skills with role requirements, and tracking a practical development plan. It includes resume import and PDF generation, self-assessments, offline recommendations, and a current-data career report.

## Features

- Email registration and login with PBKDF2 password hashes
- Private per-user profile, skills, assessments, and progress in SQLite
- Profile completion and rule-based profile strength scoring
- Ten sample role profiles and deterministic role-fit/skill-gap analysis
- ATS resume preview, PDF export, and PDF/DOCX text import
- Offline career coaching and prioritized development recommendations
- Progress tracking, JSON export, and multi-page ReportLab career report
- Optional environment configuration for a future Gemini integration; the current app does not require an API

## Technology and architecture

Python 3.10+, Streamlit, SQLite, pandas, Plotly, ReportLab, pypdf, python-docx, python-dotenv. `app.py` contains the Streamlit presentation layer; `services/core.py` owns database and business logic; `services/reports.py` builds the PDF. The default database is created at `data/talentsphere.db` on first launch.

```text
talentsphere_elevate/
├── app.py
├── requirements.txt
├── services/
│   ├── core.py
│   └── reports.py
├── data/              # created automatically; local database
└── tests/
    └── test_core.py
```

## Install and run

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Create an account in the opening screen. Passwords require at least eight characters. The database is private to the local instance; do not share it as an app hosting strategy for multiple organizations.

## Configuration

Copy `.env.example` to `.env`. The app runs in deterministic local mode without `GEMINI_API_KEY`. Set `DATABASE_PATH` to override the SQLite file path. No key is required or currently sent to an external provider.

## Run tests

```bash
pytest
```

## Publish a live demo

The project is organized for Streamlit Community Cloud: `app.py`, `requirements.txt`, and `.streamlit/config.toml` are at the repository root. Push this folder to a GitHub repository, then in [Streamlit Community Cloud](https://share.streamlit.io/) choose **Create app**, select that repository and branch, and set the entrypoint to `app.py`. The deployer needs admin access to the GitHub repository.

**Important data limitation:** this starter uses a local SQLite file. On a hosted instance, that file is on the app container and should be treated as temporary; it is not a durable multi-employee production database. Use fictional demo records only until storage is migrated to a managed persistent database and deployment security has been reviewed. Do not add `.env`, the SQLite database, or `.venv` to GitHub. No AI secret is needed for the current offline features.

## Notes and future scope

This is a functional demonstration foundation, not a hardened enterprise identity system. Add migrations, rate limiting, email verification, secure hosted secrets, persistent encrypted storage, audit logging, and a validated LLM provider adapter before production deployment. Role requirements are transparent sample data intended to be adapted to a real organization's competency framework. Resume suggestions should be verified by the employee; the app does not generate fictional work history.
