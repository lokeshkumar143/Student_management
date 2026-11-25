import pytest
import validators

class TestValidatorUnit:
    """
    Unit testing for isolated validator functions.
    """

    # --- Marks Validation ---
    def test_validate_marks_valid_integer(self):
        ok, res = validators.validate_marks("85")
        assert ok is True
        assert res == 85.0

    def test_validate_marks_valid_float(self):
        ok, res = validators.validate_marks("92.75")
        assert ok is True
        assert res == 92.75

    def test_validate_marks_empty(self):
        ok, msg = validators.validate_marks("")
        assert ok is False
        assert "required" in msg.lower()

    def test_validate_marks_none(self):
        ok, msg = validators.validate_marks(None)
        assert ok is False
        assert "required" in msg.lower()

    def test_validate_marks_non_numeric(self):
        ok, msg = validators.validate_marks("abc")
        assert ok is False
        assert "valid number" in msg.lower()

    def test_validate_marks_negative(self):
        ok, msg = validators.validate_marks("-10")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_validate_marks_exceed_100(self):
        ok, msg = validators.validate_marks("105")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_validate_marks_nan_and_inf_rejected(self):
        for bad_val in ["nan", "NaN", "inf", "-inf", float("nan"), float("inf")]:
            ok, msg = validators.validate_marks(bad_val)
            assert ok is False
            assert "valid number" in msg.lower()

    # --- Grade Calculation ---
    def test_calculate_grade_a_plus(self):
        assert validators.calculate_grade(95) == "A+"
        assert validators.calculate_grade(90) == "A+"

    def test_calculate_grade_a(self):
        assert validators.calculate_grade(85) == "A"
        assert validators.calculate_grade(80) == "A"

    def test_calculate_grade_b(self):
        assert validators.calculate_grade(75) == "B"
        assert validators.calculate_grade(70) == "B"

    def test_calculate_grade_c(self):
        assert validators.calculate_grade(65) == "C"
        assert validators.calculate_grade(60) == "C"

    def test_calculate_grade_d(self):
        assert validators.calculate_grade(55) == "D"
        assert validators.calculate_grade(50) == "D"

    def test_calculate_grade_f(self):
        assert validators.calculate_grade(49.9) == "F"
        assert validators.calculate_grade(0) == "F"

    def test_calculate_grade_invalid(self):
        assert validators.calculate_grade(None) == "N/A"
        assert validators.calculate_grade("xyz") == "N/A"

    # --- Register Number Validation (9-digit numeric e.g. 192210378) ---
    def test_validate_register_number_valid(self):
        ok, res = validators.validate_register_number("192210378")
        assert ok is True
        assert res == "192210378"

    def test_validate_register_number_empty(self):
        ok, msg = validators.validate_register_number("")
        assert ok is False
        assert "required" in msg.lower()

    def test_validate_register_number_too_short(self):
        ok, msg = validators.validate_register_number("19221037")
        assert ok is False
        assert "exactly 9 digits" in msg

    def test_validate_register_number_too_long(self):
        ok, msg = validators.validate_register_number("1922103789")
        assert ok is False
        assert "exactly 9 digits" in msg

    def test_validate_register_number_invalid_characters(self):
        ok, msg = validators.validate_register_number("19221037A")
        assert ok is False
        assert "only digits" in msg

    # --- Name Validation ---
    def test_validate_name_valid(self):
        ok, res = validators.validate_name("Alan Turing")
        assert ok is True
        assert res == "Alan Turing"

    def test_validate_name_empty(self):
        ok, msg = validators.validate_name("")
        assert ok is False
        assert "required" in msg.lower()

    def test_validate_name_too_short(self):
        ok, msg = validators.validate_name("A")
        assert ok is False
        assert "between 2 and 50" in msg

    def test_validate_name_too_long(self):
        ok, msg = validators.validate_name("A" * 51)
        assert ok is False
        assert "between 2 and 50" in msg

    def test_validate_name_with_numbers(self):
        ok, msg = validators.validate_name("John Doe 2nd")
        assert ok is False
        assert "alphabetic" in msg.lower()

    # --- Department Validation ---
    def test_validate_department_valid(self):
        ok, res = validators.validate_department("Computer Science")
        assert ok is True
        assert res == "Computer Science"

    def test_validate_department_invalid(self):
        ok, msg = validators.validate_department("Astrology")
        assert ok is False
        assert "Invalid department" in msg

    def test_validate_department_empty(self):
        ok, msg = validators.validate_department("")
        assert ok is False
        assert "required" in msg.lower()

    # --- Email Validation ---
    def test_validate_email_valid(self):
        ok, res = validators.validate_email("student@university.edu")
        assert ok is True
        assert res == "student@university.edu"

    def test_validate_email_empty(self):
        ok, msg = validators.validate_email("")
        assert ok is False
        assert "required" in msg.lower()

    def test_validate_email_missing_at(self):
        ok, msg = validators.validate_email("studentuniversity.edu")
        assert ok is False
        assert "Invalid email" in msg

    def test_validate_email_missing_domain(self):
        ok, msg = validators.validate_email("student@")
        assert ok is False
        assert "Invalid email" in msg

    def test_validate_email_whitespace(self):
        ok, msg = validators.validate_email("stu dent@univ.edu")
        assert ok is False
        assert "Invalid email" in msg

    def test_validate_student_composite_success(self):
        data = {
            'register_number': '192210378',
            'name': 'Valid Name',
            'department': 'Computer Science',
            'email': 'valid@student.org',
            'marks': '88.5'
        }
        ok, errors, cleaned = validators.validate_student(data)
        assert ok is True
        assert len(errors) == 0
        assert cleaned['marks'] == 88.5

    def test_validate_student_composite_all_errors(self):
        data = {
            'register_number': '',
            'name': '1',
            'department': 'InvalidDept',
            'email': 'not_an_email',
            'marks': '200'
        }
        ok, errors, cleaned = validators.validate_student(data)
        assert ok is False
        assert 'register_number' in errors
        assert 'name' in errors
        assert 'department' in errors
        assert 'email' in errors
        assert 'marks' in errors

