import pytest
import models
import validators

class TestRegression:
    """
    Regression Testing suite ensures that previously identified defects and edge cases
    do not reoccur as new features or modifications are introduced.
    """

    def test_regression_bug_101_marks_exact_100_accepted(self):
        """
        Regression Check for BUG-101:
        Ensure that marks = 100.0 is accepted without boundary overflow rejection.
        """
        ok, res = validators.validate_marks("100.0")
        assert ok is True
        assert res == 100.0
        assert validators.calculate_grade(res) == "A+"

    def test_regression_bug_102_duplicate_reg_no_whitespace_trimmed(self, temp_db):
        """
        Regression Check for BUG-102:
        Register number uniqueness check must catch duplicates even with leading/trailing spaces.
        """
        models.create_student("192210378", "Existing Student", "Computer Science", "existing@test.com", 80.0, db_path=temp_db)
        
        conn = models.get_db_connection(temp_db)
        try:
            ok, msg = validators.validate_register_number(" 192210378 ", existing_student_id=None, db=conn)
            assert ok is False
            assert "already exists" in msg
        finally:
            conn.close()

    def test_regression_bug_103_edit_self_not_flagged_as_duplicate(self, temp_db):
        """
        Regression Check for BUG-103:
        When updating a student's marks or name without changing their register number,
        the system must not flag their own register number as a duplicate.
        """
        sid = models.create_student("192210380", "Self Update", "Information Technology", "self@test.com", 75.0, db_path=temp_db)
        
        conn = models.get_db_connection(temp_db)
        try:
            ok, res = validators.validate_register_number("192210380", existing_student_id=sid, db=conn)
            assert ok is True
            assert res == "192210380"
        finally:
            conn.close()

    def test_regression_bug_104_input_sanitization_leading_trailing_spaces(self):
        """
        Regression Check for BUG-104:
        Leading and trailing whitespace must be automatically trimmed.
        """
        ok, res = validators.validate_name("   Barbara Liskov   ")
        assert ok is True
        assert res == "Barbara Liskov"

        ok, res = validators.validate_email("  barbara@mit.edu  ")
        assert ok is True
        assert res == "barbara@mit.edu"

    def test_regression_bug_105_marks_grade_threshold_boundaries(self):
        """
        Regression Check for BUG-105:
        Verify all grade boundaries strictly match grading scale:
        90+: A+, 80-89: A, 70-79: B, 60-69: C, 50-59: D, <50: F
        """
        assert validators.calculate_grade(89.99) == "A"
        assert validators.calculate_grade(90.0) == "A+"
        assert validators.calculate_grade(79.99) == "B"
        assert validators.calculate_grade(80.0) == "A"
        assert validators.calculate_grade(49.99) == "F"
        assert validators.calculate_grade(50.0) == "D"

    def test_regression_bug_105_search_like_wildcards_escaped(self, temp_db):
        """
        Regression Check for BUG-105:
        Searching with SQL LIKE wildcards ('%' or '_') must not match unrelated records.
        """
        models.create_student("192210399", "Normal Student", "Computer Science", "normal@test.com", 82.0, db_path=temp_db)
        results_percent = models.get_all_students(search_query="%", db_path=temp_db)
        assert len(results_percent) == 0

        results_underscore = models.get_all_students(search_query="_", db_path=temp_db)
        assert len(results_underscore) == 0
