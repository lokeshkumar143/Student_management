import os
from config import Config
import models

def seed_database():
    db_path = Config.DATABASE
    models.init_db(db_path)

    # 0. Seed Default Administrator & QA Tester Users
    models.ensure_default_admin(db_path=db_path)
    if not models.get_user_by_username("qa_tester", db_path=db_path):
        models.create_user(
            username="qa_tester",
            full_name="QA Test Engineer",
            email="qa@eduquality.edu",
            password="Tester@123",
            role="QA Engineer",
            db_path=db_path
        )
    
    # 1. Seed Students (9-digit numeric register numbers e.g. 192210378)
    students_data = [
        ("192210378", "Aarav Sharma", "Computer Science", "aarav.sharma@college.edu", 94.5),
        ("192210379", "Diya Patel", "Information Technology", "diya.patel@college.edu", 88.0),
        ("192210380", "Rohan Verma", "Electronics & Communication", "rohan.v@college.edu", 76.5),
        ("192210381", "Ananya Iyer", "Data Science", "ananya.iyer@college.edu", 98.0),
        ("192210382", "Vikramaditya Rao", "Mechanical Engineering", "vikram.rao@college.edu", 68.5),
        ("192210383", "Sneha Kulkarni", "Artificial Intelligence", "sneha.k@college.edu", 85.0),
        ("192210384", "Karthik Nair", "Electrical & Electronics", "karthik.n@college.edu", 54.0),
        ("192210385", "Meera Sen", "Civil Engineering", "meera.sen@college.edu", 42.5),
        ("192210386", "Arjun Reddy", "Computer Science", "arjun.reddy@college.edu", 91.0),
        ("192210387", "Pooja Hegde", "Information Technology", "pooja.h@college.edu", 73.0)
    ]
    
    for reg_no, name, dept, email, marks in students_data:
        existing = models.get_student_by_reg_no(reg_no, db_path=db_path)
        if not existing:
            models.create_student(reg_no, name, dept, email, marks, db_path=db_path)
            
    # 2. Seed Defects (Representing Software Testing Life Cycle)
    defects_data = [
        (
            "BUG-101",
            "Marks boundary test fails on exact score of 100",
            "When submitting marks = 100.0, the validation logic previously used '< 100' instead of '<= 100', causing max boundary to be rejected.",
            "1. Enter student details\n2. Enter marks = 100\n3. Click Save Record",
            "Input Validation & BVA",
            "High",
            "Closed",
            "tests/test_bva.py::test_bva_marks_at_max_boundary",
            "Fixed conditional expression in validators.py to check 0 <= marks <= 100. Verified via Pytest BVA suite."
        ),
        (
            "BUG-102",
            "Register number duplicate check bypassed with trailing spaces",
            "Entering ' 192210378 ' when '192210378' already exists allowed duplicate records in SQLite.",
            "1. Add student with 192210378\n2. Add another student with ' 192210378 '\n3. Both inserted successfully",
            "Database Integrity & Constraints",
            "High",
            "Resolved",
            "tests/test_regression.py::test_regression_bug_102_duplicate_reg_no_whitespace_trimmed",
            "Added .strip() normalization before SQLite uniqueness query. Verified with regression test."
        ),
        (
            "BUG-103",
            "Editing student without changing reg number triggered self-duplicate error",
            "When editing student marks, submitting the form failed with 'Register number already exists'.",
            "1. Open Edit Student\n2. Modify marks only\n3. Click Update",
            "Student Record Management",
            "Medium",
            "Resolved",
            "tests/test_regression.py::test_regression_bug_103_edit_self_not_flagged_as_duplicate",
            "Added existing_student_id parameter to exclude current record ID during uniqueness query."
        ),
        (
            "BUG-104",
            "White-space around email addresses resulted in validation rejection",
            "Users copying emails with accidental trailing spaces received 'Invalid email address' error.",
            "1. Enter email ' user@college.edu '\n2. Click Save",
            "Input Validation & BVA",
            "Low",
            "Closed",
            "tests/test_regression.py::test_regression_bug_104_input_sanitization_leading_trailing_spaces",
            "Added .strip() to all validator functions before regex matching."
        ),
        (
            "BUG-105",
            "Search query special characters caused unexpected SQL match",
            "Special characters ('%' or '_') in search box acted as LIKE wildcards in SQLite.",
            "1. Enter '%' in search box\n2. All records returned unintentionally",
            "Student Record Management",
            "Low",
            "Resolved",
            "tests/test_regression.py::test_regression_bug_105_search_like_wildcards_escaped",
            "Escaped '\\', '%', and '_' with ESCAPE '\\' in models.get_all_students() and verified via regression test."
        )
    ]
    
    for bug_id, title, desc, steps, module, sev, status, found_by, res_notes in defects_data:
        existing_defect = models.get_all_defects(db_path=db_path)
        if not any(d["bug_id"] == bug_id for d in existing_defect):
            models.create_defect(
                bug_id=bug_id,
                title=title,
                description=desc,
                steps_to_reproduce=steps,
                module=module,
                severity=sev,
                status=status,
                found_by_test=found_by,
                resolution_notes=res_notes,
                db_path=db_path
            )

    print("Seed data initialized successfully.")

if __name__ == "__main__":
    seed_database()
