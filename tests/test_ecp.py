import pytest
import validators

class TestEquivalenceClassPartitioning:
    """
    Equivalence Class Partitioning (ECP) divides input ranges into valid and invalid classes.
    """

    # --- Marks Partitions ---
    # Partition 1: Valid Numeric Range [0, 100]
    def test_ecp_marks_valid_partition(self):
        for val in ["0", "35", "75.5", "100"]:
            ok, res = validators.validate_marks(val)
            assert ok is True
            assert 0.0 <= res <= 100.0

    # Partition 2: Invalid Negative Numbers (< 0)
    def test_ecp_marks_invalid_negative_partition(self):
        for val in ["-0.001", "-5", "-50", "-999"]:
            ok, msg = validators.validate_marks(val)
            assert ok is False
            assert "between 0 and 100" in msg

    # Partition 3: Invalid Excessive Numbers (> 100)
    def test_ecp_marks_invalid_excessive_partition(self):
        for val in ["100.1", "105", "500", "99999"]:
            ok, msg = validators.validate_marks(val)
            assert ok is False
            assert "between 0 and 100" in msg

    # Partition 4: Invalid Non-Numeric Input
    def test_ecp_marks_invalid_non_numeric_partition(self):
        for val in ["hundred", "90%", "ten", "$45", None]:
            ok, msg = validators.validate_marks(val)
            assert ok is False

    # --- Email Partitions ---
    # Partition 1: Valid RFC Format
    def test_ecp_email_valid_partition(self):
        for email in ["student@university.edu", "first.last@college.ac.in", "user_123@domain.org"]:
            ok, res = validators.validate_email(email)
            assert ok is True

    # Partition 2: Invalid Missing Domain
    def test_ecp_email_invalid_missing_domain(self):
        ok, msg = validators.validate_email("user@")
        assert ok is False

    # Partition 3: Invalid Missing @ Symbol
    def test_ecp_email_invalid_missing_at(self):
        ok, msg = validators.validate_email("userdomain.com")
        assert ok is False

    # Partition 4: Invalid Spaces
    def test_ecp_email_invalid_spaces(self):
        ok, msg = validators.validate_email("user name@domain.com")
        assert ok is False

    # --- Department Partitions ---
    # Partition 1: Valid Approved Departments
    def test_ecp_department_valid_partition(self):
        for dept in validators.VALID_DEPARTMENTS:
            ok, res = validators.validate_department(dept)
            assert ok is True
            assert res == dept

    # Partition 2: Invalid Unapproved Departments
    def test_ecp_department_invalid_partition(self):
        for dept in ["Music", "Astrology", "Unknown"]:
            ok, msg = validators.validate_department(dept)
            assert ok is False
            assert "Invalid department" in msg

    # --- Register Number Partitions (9-digit numeric) ---
    def test_ecp_reg_no_valid_partition(self):
        for reg in ["192210378", "192210001", "202311500"]:
            ok, res = validators.validate_register_number(reg)
            assert ok is True
            assert res == reg

    def test_ecp_reg_no_invalid_non_numeric_partition(self):
        for reg in ["REG1001", "19221037A", "1922-1037", "1922 1037"]:
            ok, msg = validators.validate_register_number(reg)
            assert ok is False
            assert "only digits" in msg
