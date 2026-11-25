import pytest
import validators

class TestBoundaryValueAnalysis:
    """
    Boundary Value Analysis (BVA) focuses on the boundaries of input domains
    where errors commonly happen:
    Points: Min - 1 (Invalid), Min (Valid), Min + 1 (Valid),
            Nominal (Valid), Max - 1 (Valid), Max (Valid), Max + 1 (Invalid)
    """

    # ==========================================
    # Marks BVA: Permitted Range is [0.0, 100.0]
    # ==========================================

    def test_bva_marks_below_min_extreme(self):
        """Value: -999.0 -> Expected: Rejected"""
        ok, msg = validators.validate_marks("-999.0")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_bva_marks_below_min_integer(self):
        """Value: -1 (Min - 1) -> Expected: Rejected"""
        ok, msg = validators.validate_marks("-1")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_bva_marks_below_min_decimal(self):
        """Value: -0.01 (Just below min) -> Expected: Rejected"""
        ok, msg = validators.validate_marks("-0.01")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_bva_marks_at_min_boundary(self):
        """Value: 0.0 (Min Boundary) -> Expected: Accepted"""
        ok, res = validators.validate_marks("0.0")
        assert ok is True
        assert res == 0.0
        assert validators.calculate_grade(res) == "F"

    def test_bva_marks_above_min_decimal(self):
        """Value: 0.01 (Just above min) -> Expected: Accepted"""
        ok, res = validators.validate_marks("0.01")
        assert ok is True
        assert res == 0.01

    def test_bva_marks_above_min_integer(self):
        """Value: 1.0 (Min + 1) -> Expected: Accepted"""
        ok, res = validators.validate_marks("1.0")
        assert ok is True
        assert res == 1.0

    def test_bva_marks_nominal_midpoint(self):
        """Value: 50.0 (Nominal passing boundary) -> Expected: Accepted"""
        ok, res = validators.validate_marks("50.0")
        assert ok is True
        assert res == 50.0
        assert validators.calculate_grade(res) == "D"

    def test_bva_marks_below_max_integer(self):
        """Value: 99.0 (Max - 1) -> Expected: Accepted"""
        ok, res = validators.validate_marks("99.0")
        assert ok is True
        assert res == 99.0
        assert validators.calculate_grade(res) == "A+"

    def test_bva_marks_below_max_decimal(self):
        """Value: 99.99 (Just below max) -> Expected: Accepted"""
        ok, res = validators.validate_marks("99.99")
        assert ok is True
        assert res == 99.99

    def test_bva_marks_at_max_boundary(self):
        """Value: 100.0 (Max Boundary) -> Expected: Accepted"""
        ok, res = validators.validate_marks("100.0")
        assert ok is True
        assert res == 100.0
        assert validators.calculate_grade(res) == "A+"

    def test_bva_marks_above_max_decimal(self):
        """Value: 100.01 (Just above max) -> Expected: Rejected"""
        ok, msg = validators.validate_marks("100.01")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_bva_marks_above_max_integer(self):
        """Value: 101.0 (Max + 1) -> Expected: Rejected"""
        ok, msg = validators.validate_marks("101.0")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_bva_marks_above_max_project_example(self):
        """Value: 105 (Explicit PDF example: 'enters -5 or 105') -> Expected: Rejected"""
        ok, msg = validators.validate_marks("105")
        assert ok is False
        assert "between 0 and 100" in msg

    def test_bva_marks_below_min_project_example(self):
        """Value: -5 (Explicit PDF example: 'enters -5 or 105') -> Expected: Rejected"""
        ok, msg = validators.validate_marks("-5")
        assert ok is False
        assert "between 0 and 100" in msg

    # ==========================================
    # Register Number Length BVA: Exact 9 digits (e.g. 192210378)
    # ==========================================

    def test_bva_reg_no_length_below_exact(self):
        """Length: 8 digits (Target - 1) -> Expected: Rejected"""
        ok, msg = validators.validate_register_number("19221037")
        assert ok is False
        assert "exactly 9 digits" in msg

    def test_bva_reg_no_length_at_exact(self):
        """Length: 9 digits (Exact valid format) -> Expected: Accepted"""
        ok, res = validators.validate_register_number("192210378")
        assert ok is True
        assert res == "192210378"

    def test_bva_reg_no_length_above_exact(self):
        """Length: 10 digits (Target + 1) -> Expected: Rejected"""
        ok, msg = validators.validate_register_number("1922103789")
        assert ok is False
        assert "exactly 9 digits" in msg

    def test_bva_reg_no_length_extreme_short(self):
        """Length: 1 digit -> Expected: Rejected"""
        ok, msg = validators.validate_register_number("1")
        assert ok is False
        assert "exactly 9 digits" in msg

    # ==========================================
    # Student Name Length BVA: [2, 50] chars
    # ==========================================

    def test_bva_name_length_below_min(self):
        """Length: 1 char (Min - 1) -> Expected: Rejected"""
        ok, msg = validators.validate_name("A")
        assert ok is False
        assert "between 2 and 50" in msg

    def test_bva_name_length_at_min(self):
        """Length: 2 chars (Min) -> Expected: Accepted"""
        ok, res = validators.validate_name("Ed")
        assert ok is True
        assert res == "Ed"

    def test_bva_name_length_at_max(self):
        """Length: 50 chars (Max) -> Expected: Accepted"""
        val = "Alexander Christopher Montgomery Fitzpatrick James"[:50]
        ok, res = validators.validate_name(val)
        assert ok is True
        assert len(res) == 50

    def test_bva_name_length_above_max(self):
        """Length: 51 chars (Max + 1) -> Expected: Rejected"""
        val = "A" * 51
        ok, msg = validators.validate_name(val)
        assert ok is False
        assert "between 2 and 50" in msg
