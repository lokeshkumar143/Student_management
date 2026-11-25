# AcadVerify — Student Management System with Automated Software Testing
> **Enterprise Software Testing & Academic Records Platform**  
> Built with **Python**, **Flask (Blueprints)**, **SQLite**, **Bootstrap 5**, **Pytest**, and **Coverage.py**.

---

## 1. Project Overview

**AcadVerify** is a web-based **Student Management System with Automated Software Testing** built to manage student academic records securely while demonstrating rigorous software testing and quality assurance workflows.

The system covers all three core modules:
1. **Student Record Management**: Administrator-authenticated CRUD operations, sorting, pagination, multi-field search (Register Number, Name, Email), department filtering, CSV roster export, and strict input validation.
2. **Automated Test Case Execution (Pytest)**: 127 automated tests implementing **Unit Testing**, **Integration Testing**, **Black-Box Testing**, **Boundary Value Analysis (BVA)**, **Equivalence Class Partitioning (ECP)**, **Regression Testing**, and **CSRF/Auth Security Testing**.
3. **Bug Tracking & QA Test Report Dashboard**: Live AJAX Pytest suite runner (supporting full or selective suite re-runs), **Coverage.py** statement & missing-line breakdown, test completion gates, execution history, defect lifecycle tracker, and system audit trail.

---

## 2. Project Architecture

```text
├── app.py                     # Flask application factory & CSRF/session lifecycle
├── config.py                  # Development & Test configurations
├── security.py                # Per-session CSRF protection & @login_required guard
├── models.py                  # SQLite data layer (students, defects, test_runs, users, audit_logs)
├── validators.py              # Pure input validators (BVA, ECP, NaN/Inf guards, auth checks)
├── test_runner.py             # Programmatic Pytest + Coverage.py runner & XML/JSON parser
├── seed_data.py               # Seeds default admins, sample students, and defect records
├── pyproject.toml             # Pytest & Coverage.py configuration
├── requirements.txt           # Project dependencies
├── routes/                    # Modular Flask Blueprints
│   ├── auth.py                # /login, /register, /logout, /profile
│   ├── students.py            # /students CRUD, sorting, pagination, /students/export
│   └── testing.py             # /testing/dashboard, /testing/run, /testing/defects, /testing/audit
├── static/
│   ├── css/app.css            # Enterprise sidebar shell, accessible tables, animations
│   └── js/app.js              # Live AJAX test runner, ARIA validation sync, BVA range helper
├── templates/                 # Semantic Bootstrap 5 Jinja2 templates
│   ├── base.html              # Responsive sidebar + mobile offcanvas navigation shell
│   ├── auth/                  # login.html, register.html, profile.html
│   ├── students/              # index.html, add.html, edit.html, view.html
│   └── testing/               # dashboard.html, defects.html, defect_form.html, defect_view.html, audit.html, methodology.html
├── reports/                   # Generated test_report.xml & coverage.json artifacts
└── tests/                     # Automated Pytest Suite (127 Test Cases)
    ├── conftest.py            # Isolated SQLite DB, unauthenticated & authenticated test clients
    ├── test_auth.py           # Auth validators, login/register/logout, password change, CSRF tests
    ├── test_bva.py            # Boundary Value Analysis tests
    ├── test_ecp.py            # Equivalence Class Partitioning tests
    ├── test_validators.py     # Unit tests for validation & NaN/Inf edge cases
    ├── test_models.py         # Unit tests for SQLite CRUD, pagination, audit logs
    ├── test_integration.py    # End-to-end Flask Blueprint HTTP tests
    └── test_regression.py     # Regression checks for resolved defects (BUG-101 to BUG-105)
```

---

## 3. Running the Project

### 1. Setup & Seed Database
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed_data.py
```

### 2. Run Automated Tests & Code Coverage
```bash
pytest
python test_runner.py
coverage report -m
```

### 3. Start the Web Server
```bash
python app.py
```
Open `http://127.0.0.1:5001` in your browser.

### 4. Default Administrator Credentials
- **Username**: `admin`
- **Password**: `Admin@123`
- *(Additional QA user: `qa_tester` / `Tester@123`. New accounts can also be created at `/register`, and passwords can be updated at `/profile`.)*
# Student_management
