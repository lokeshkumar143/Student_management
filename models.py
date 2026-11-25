import sqlite3
import os
import hmac
from datetime import datetime
from config import Config

def get_db_connection(db_path=None):
    """
    Creates and returns a SQLite database connection with row factory enabled.
    """
    if db_path is None:
        db_path = Config.DATABASE
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None):
    """
    Initializes database tables: students, defects, and test_executions.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            marks REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Defects / Bug Tracker Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bug_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            steps_to_reproduce TEXT,
            module TEXT NOT NULL,
            severity TEXT NOT NULL CHECK(severity IN ('Critical', 'High', 'Medium', 'Low')),
            status TEXT NOT NULL CHECK(status IN ('Open', 'In Progress', 'Resolved', 'Closed')),
            found_by_test TEXT,
            reported_date TEXT NOT NULL,
            resolution_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Test Executions History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            total_tests INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            failed INTEGER NOT NULL,
            skipped INTEGER NOT NULL,
            duration REAL NOT NULL,
            coverage_percent REAL NOT NULL,
            results_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Administrator Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Administrator',
            last_login TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # System Audit Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            details TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


# ==========================================
# Student CRUD Operations
# ==========================================

def create_student(register_number, name, department, email, marks, db_path=None):
    """
    Inserts a new student record. Returns the new student id or raises an error.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (register_number, name, department, email, marks, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (register_number, name, department, email, float(marks)))
        conn.commit()
        student_id = cursor.lastrowid
        return student_id
    finally:
        conn.close()


def get_student_by_id(student_id, db_path=None):
    """
    Retrieves a student by ID. Returns a dict or None.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_student_by_reg_no(register_number, db_path=None):
    """
    Retrieves a student by Register Number. Returns a dict or None.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE LOWER(register_number) = LOWER(?)", (register_number,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_students(search_query=None, department=None, db_path=None):
    """
    Retrieves all students, with optional search query and department filter.
    Search checks: register_number, name, email.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        sql = "SELECT * FROM students WHERE 1=1"
        params = []
        
        if search_query and search_query.strip():
            escaped = (
                search_query.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            sq = f"%{escaped}%"
            sql += " AND (register_number LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\')"
            params.extend([sq, sq, sq])
            
        if department and department.strip() and department != "All":
            sql += " AND department = ?"
            params.append(department.strip())
            
        sql += " ORDER BY id DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_student(student_id, register_number, name, department, email, marks, db_path=None):
    """
    Updates an existing student record. Returns True on success, False if student not found.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE students
            SET register_number = ?, name = ?, department = ?, email = ?, marks = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (register_number, name, department, email, float(marks), student_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_student(student_id, db_path=None):
    """
    Deletes a student record by ID. Returns True on success, False otherwise.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_student_count(db_path=None):
    """
    Returns total count of students.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM students")
        return cursor.fetchone()[0]
    finally:
        conn.close()


ALLOWED_STUDENT_SORT_COLUMNS = {
    "id": "id",
    "register_number": "register_number",
    "name": "name",
    "department": "department",
    "marks": "marks",
    "created_at": "created_at",
}


def get_students_paginated(search_query=None, department=None, sort_by="id", sort_dir="desc", page=1, per_page=10, db_path=None):
    """
    Retrieves paginated and sorted students along with total matching count.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        where_sql = " WHERE 1=1"
        params = []

        if search_query and search_query.strip():
            escaped = (
                search_query.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            sq = f"%{escaped}%"
            where_sql += " AND (register_number LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\')"
            params.extend([sq, sq, sq])

        if department and department.strip() and department != "All":
            where_sql += " AND department = ?"
            params.append(department.strip())

        cursor.execute(f"SELECT COUNT(*) FROM students{where_sql}", params)
        total_matching = cursor.fetchone()[0]

        sort_col = ALLOWED_STUDENT_SORT_COLUMNS.get(sort_by, "id")
        direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"
        offset = max(0, (int(page) - 1) * int(per_page))

        query_sql = f"SELECT * FROM students{where_sql} ORDER BY {sort_col} {direction}, id DESC LIMIT ? OFFSET ?"
        cursor.execute(query_sql, [*params, int(per_page), offset])
        rows = [dict(r) for r in cursor.fetchall()]
        return rows, total_matching
    finally:
        conn.close()


def get_department_stats(db_path=None):
    """
    Returns average marks and student count grouped by department.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT department, COUNT(*) AS count, ROUND(AVG(marks), 1) AS avg_marks
            FROM students
            GROUP BY department
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ==========================================
# Defect / Bug Tracking Operations
# ==========================================

def create_defect(bug_id, title, description, steps_to_reproduce, module, severity, status, found_by_test=None, resolution_notes=None, db_path=None):
    """
    Inserts a new defect record.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    reported_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT INTO defects (bug_id, title, description, steps_to_reproduce, module, severity, status, found_by_test, reported_date, resolution_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bug_id, title, description, steps_to_reproduce, module, severity, status, found_by_test, reported_date, resolution_notes))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_defects(status=None, severity=None, db_path=None):
    """
    Retrieves all defects with optional status or severity filters.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        sql = "SELECT * FROM defects WHERE 1=1"
        params = []
        if status and status != "All":
            sql += " AND status = ?"
            params.append(status)
        if severity and severity != "All":
            sql += " AND severity = ?"
            params.append(severity)
        sql += " ORDER BY id DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_defect_by_id(defect_id, db_path=None):
    """
    Retrieves a defect by ID.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM defects WHERE id = ?", (defect_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_defect(defect_id, title, description, steps_to_reproduce, module, severity, status, resolution_notes=None, db_path=None):
    """
    Updates an existing defect.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE defects
            SET title = ?, description = ?, steps_to_reproduce = ?, module = ?, severity = ?, status = ?, resolution_notes = ?
            WHERE id = ?
        """, (title, description, steps_to_reproduce, module, severity, status, resolution_notes, defect_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_defect(defect_id, db_path=None):
    """
    Deletes a defect by ID.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM defects WHERE id = ?", (defect_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_defect_stats(db_path=None):
    """
    Returns aggregated defect statistics: total, open, in progress, resolved, closed, severity counts.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM defects")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM defects GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        cursor.execute("SELECT severity, COUNT(*) FROM defects GROUP BY severity")
        severity_counts = dict(cursor.fetchall())
        
        return {
            "total": total,
            "open": status_counts.get("Open", 0),
            "in_progress": status_counts.get("In Progress", 0),
            "resolved": status_counts.get("Resolved", 0),
            "closed": status_counts.get("Closed", 0),
            "critical": severity_counts.get("Critical", 0),
            "high": severity_counts.get("High", 0),
            "medium": severity_counts.get("Medium", 0),
            "low": severity_counts.get("Low", 0),
        }
    finally:
        conn.close()


# ==========================================
# Test Run History Operations
# ==========================================

def record_test_run(run_timestamp, total_tests, passed, failed, skipped, duration, coverage_percent, results_json, db_path=None):
    """
    Records a completed test execution run in the database.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO test_runs (run_timestamp, total_tests, passed, failed, skipped, duration, coverage_percent, results_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_timestamp, total_tests, passed, failed, skipped, duration, coverage_percent, results_json))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_latest_test_run(db_path=None):
    """
    Retrieves the most recent test run record.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM test_runs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_recent_test_runs(limit=10, db_path=None):
    """
    Retrieves recent test run summaries for Test Monitoring & Control history.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, run_timestamp, total_tests, passed, failed, skipped, duration, coverage_percent
            FROM test_runs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ==========================================
# User / Administrator Authentication
# ==========================================

def create_user(username, full_name, email, password, role="Administrator", db_path=None):
    """
    Creates a new user account storing the password in the users table.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, full_name, email, password, role, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (username.strip(), full_name.strip(), email.strip().lower(), password, role))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_username(username, db_path=None):
    """
    Retrieves a user by username (case-insensitive).
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id, db_path=None):
    """
    Retrieves a user by ID.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def verify_user_credentials(username, password, db_path=None):
    """
    Verifies username and password. Returns user dict if valid, else None.
    """
    if not username or not password:
        return None
    user = get_user_by_username(username, db_path=db_path)
    if user and hmac.compare_digest(user["password"], password):
        return user
    return None


def update_last_login(user_id, db_path=None):
    """
    Records the latest login timestamp for a user.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user_id))
        conn.commit()
    finally:
        conn.close()


def get_user_count(db_path=None):
    """
    Returns total count of registered users.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def ensure_default_admin(db_path=None):
    """
    Ensures the default capstone administrator account exists if no users are present.
    """
    if get_user_count(db_path=db_path) == 0:
        create_user(
            username="admin",
            full_name="System Administrator",
            email="admin@acadverify.edu",
            password="Admin@123",
            role="Administrator",
            db_path=db_path
        )


def update_user_password(user_id, new_password, db_path=None):
    """
    Updates a user's password.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (new_password, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ==========================================
# System Audit Log Operations
# ==========================================

def log_activity(actor, action, entity_type, entity_id=None, details=None, db_path=None):
    """
    Records an administrative or QA event in the audit_logs table.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT INTO audit_logs (actor, action, entity_type, entity_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (actor, action, entity_type, str(entity_id) if entity_id is not None else None, details, now_str))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_recent_audit_logs(limit=30, db_path=None):
    """
    Retrieves the most recent audit log events.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
