import pytest
import models

class TestDatabaseModels:
    """
    Unit tests for SQLite database operations in models.py.
    """

    def test_create_and_get_student_by_id(self, temp_db):
        sid = models.create_student(
            register_number="192210378",
            name="Grace Hopper",
            department="Computer Science",
            email="grace@navy.mil",
            marks=98.5,
            db_path=temp_db
        )
        assert sid is not None
        student = models.get_student_by_id(sid, db_path=temp_db)
        assert student is not None
        assert student["register_number"] == "192210378"
        assert student["name"] == "Grace Hopper"
        assert student["marks"] == 98.5

    def test_get_student_by_reg_no(self, temp_db):
        models.create_student("192210379", "Ada Lovelace", "Information Technology", "ada@lovelace.org", 95.0, db_path=temp_db)
        student = models.get_student_by_reg_no("192210379", db_path=temp_db)
        assert student is not None
        assert student["name"] == "Ada Lovelace"

    def test_get_all_students_and_search(self, temp_db):
        models.create_student("192210380", "Charles Babbage", "Mechanical Engineering", "charles@diff.eng", 75.0, db_path=temp_db)
        models.create_student("192210381", "Claude Shannon", "Information Technology", "claude@bell.labs", 88.0, db_path=temp_db)
        
        all_s = models.get_all_students(db_path=temp_db)
        assert len(all_s) == 2
        
        # Search by name
        res = models.get_all_students(search_query="Shannon", db_path=temp_db)
        assert len(res) == 1
        assert res[0]["register_number"] == "192210381"
        
        # Filter by department
        res_dept = models.get_all_students(department="Mechanical Engineering", db_path=temp_db)
        assert len(res_dept) == 1
        assert res_dept[0]["name"] == "Charles Babbage"

    def test_update_student(self, temp_db):
        sid = models.create_student("192210382", "Nikola Tesla", "Electrical & Electronics", "nikola@wardenclyffe.com", 91.0, db_path=temp_db)
        success = models.update_student(sid, "192210382", "Nikola Tesla", "Electrical & Electronics", "nikola@wardenclyffe.com", 99.0, db_path=temp_db)
        assert success is True
        
        updated = models.get_student_by_id(sid, db_path=temp_db)
        assert updated["marks"] == 99.0

    def test_delete_student(self, temp_db):
        sid = models.create_student("192210383", "Test Delete", "Civil Engineering", "del@example.com", 60.0, db_path=temp_db)
        assert models.get_student_by_id(sid, db_path=temp_db) is not None
        
        models.delete_student(sid, db_path=temp_db)
        assert models.get_student_by_id(sid, db_path=temp_db) is None

    def test_defect_lifecycle_in_models(self, temp_db):
        did = models.create_defect(
            bug_id="BUG-201",
            title="Boundary check error",
            description="Marks allowed over 100",
            steps_to_reproduce="Submit marks = 105",
            module="Student Record Management",
            severity="High",
            status="Open",
            found_by_test="test_bva_marks",
            resolution_notes=None,
            db_path=temp_db
        )
        assert did is not None
        
        defect = models.get_defect_by_id(did, db_path=temp_db)
        assert defect["bug_id"] == "BUG-201"
        assert defect["status"] == "Open"
        
        # Update defect
        models.update_defect(
            defect_id=did,
            title="Boundary check error",
            description="Marks allowed over 100",
            steps_to_reproduce="Submit marks = 105",
            module="Student Record Management",
            severity="High",
            status="Resolved",
            resolution_notes="Added 0 <= marks <= 100 validation in validators.py",
            db_path=temp_db
        )
        updated = models.get_defect_by_id(did, db_path=temp_db)
        assert updated["status"] == "Resolved"
        
        # Verify stats
        stats = models.get_defect_stats(db_path=temp_db)
        assert stats["total"] == 1
        assert stats["resolved"] == 1
        assert stats["open"] == 0

    def test_student_count_and_edge_queries(self, temp_db):
        assert models.get_student_count(db_path=temp_db) == 0
        models.create_student("192210384", "Student One", "Data Science", "s1@test.com", 70.0, db_path=temp_db)
        models.create_student("192210385", "Student Two", "Data Science", "s2@test.com", 80.0, db_path=temp_db)
        assert models.get_student_count(db_path=temp_db) == 2
        
        # Test non-existent get
        assert models.get_student_by_id(99999, db_path=temp_db) is None
        assert models.get_student_by_reg_no("NONEXISTENT", db_path=temp_db) is None
        
        # Test non-existent defect
        assert models.get_defect_by_id(99999, db_path=temp_db) is None
        
        # Filter defects by status and severity
        d_filtered = models.get_all_defects(status="Open", severity="Critical", db_path=temp_db)
        assert isinstance(d_filtered, list)

    def test_user_auth_models_and_recent_runs(self, temp_db):
        models.ensure_default_admin(temp_db)
        assert models.get_user_count(temp_db) == 1
        admin_user = models.verify_user_credentials("admin", "Admin@123", db_path=temp_db)
        assert admin_user is not None
        assert admin_user["password"] == "Admin@123"
        assert models.verify_user_credentials("admin", "WrongPass", db_path=temp_db) is None

        models.record_test_run("2026-11-25 08:30:00", 10, 10, 0, 0, 0.5, 95.0, "{}", db_path=temp_db)
        runs = models.get_recent_test_runs(limit=5, db_path=temp_db)
        assert len(runs) == 1
        assert runs[0]["coverage_percent"] == 95.0

    def test_pagination_department_stats_and_audit_logs(self, temp_db):
        for i in range(1, 13):
            dept = "Computer Science" if i % 2 == 0 else "Data Science"
            models.create_student(f"1922104{i:02d}", f"Student {i}", dept, f"s{i}@test.com", 50.0 + i, db_path=temp_db)

        page1, total = models.get_students_paginated(sort_by="marks", sort_dir="asc", page=1, per_page=5, db_path=temp_db)
        assert total == 12
        assert len(page1) == 5
        assert page1[0]["marks"] == 51.0

        dept_stats = models.get_department_stats(db_path=temp_db)
        assert len(dept_stats) == 2

        models.log_activity("admin", "CREATE", "Student", "1", "Test audit log", db_path=temp_db)
        logs = models.get_recent_audit_logs(limit=5, db_path=temp_db)
        assert len(logs) == 1
        assert logs[0]["action"] == "CREATE"

