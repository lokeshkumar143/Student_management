import re
import math

VALID_DEPARTMENTS = [
    "Computer Science",
    "Information Technology",
    "Electronics & Communication",
    "Electrical & Electronics",
    "Mechanical Engineering",
    "Civil Engineering",
    "Data Science",
    "Artificial Intelligence"
]

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
NAME_REGEX = re.compile(r"^[A-Za-z\s.'-]+$")
REG_NO_REGEX = re.compile(r"^\d{9}$")
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_.-]+$")

def validate_register_number(reg_no, existing_student_id=None, db=None):
    """
    Validates student register number:
    - Must not be empty
    - Must contain only digits (e.g., 192210378)
    - Must be exactly 9 digits
    - Must be unique across records in database
    """
    if reg_no is None or not str(reg_no).strip():
        return False, "Register number is required."
    
    clean_reg_no = str(reg_no).strip()
    if not clean_reg_no.isdigit():
        return False, "Register number must contain only digits (e.g., 192210378)."
    
    if not REG_NO_REGEX.match(clean_reg_no):
        return False, "Register number must be exactly 9 digits (e.g., 192210378)."
    
    if db is not None:
        cursor = db.cursor()
        if existing_student_id:
            cursor.execute(
                "SELECT id FROM students WHERE register_number = ? AND id != ?",
                (clean_reg_no, existing_student_id)
            )
        else:
            cursor.execute(
                "SELECT id FROM students WHERE register_number = ?",
                (clean_reg_no,)
            )
        if cursor.fetchone():
            return False, f"Register number '{clean_reg_no}' already exists."
            
    return True, clean_reg_no


def validate_name(name):
    """
    Validates student name:
    - Must not be empty
    - Must be between 2 and 50 characters
    - Must contain only letters, spaces, dots, hyphens, and apostrophes
    """
    if name is None or not str(name).strip():
        return False, "Name is required."
    
    clean_name = str(name).strip()
    if len(clean_name) < 2 or len(clean_name) > 50:
        return False, "Name must be between 2 and 50 characters."
        
    if not NAME_REGEX.match(clean_name):
        return False, "Name can only contain alphabetic characters, spaces, and punctuation (.'-)."
        
    return True, clean_name


def validate_department(department):
    """
    Validates department selection:
    - Must not be empty
    - Must belong to approved department list
    """
    if department is None or not str(department).strip():
        return False, "Department is required."
        
    clean_dept = str(department).strip()
    if clean_dept not in VALID_DEPARTMENTS:
        return False, f"Invalid department. Must be one of: {', '.join(VALID_DEPARTMENTS)}."
        
    return True, clean_dept


def validate_email(email):
    """
    Validates student email address:
    - Must not be empty
    - Must follow standard RFC email format
    """
    if email is None or not str(email).strip():
        return False, "Email address is required."
        
    clean_email = str(email).strip().lower()
    if len(clean_email) > 100:
        return False, "Email address cannot exceed 100 characters."
        
    if not EMAIL_REGEX.match(clean_email):
        return False, "Invalid email address format (e.g., student@college.edu)."
        
    return True, clean_email


def validate_marks(marks):
    """
    Validates student marks:
    - Must be a valid numeric value (int or float)
    - Boundary Value Analysis: 0.0 <= marks <= 100.0
    - Equivalence Class Partitioning:
      - Valid partition: [0, 100]
      - Invalid lower partition: (< 0)
      - Invalid upper partition: (> 100)
      - Invalid type partition: non-numeric string / None
    """
    if marks is None or str(marks).strip() == "":
        return False, "Marks field is required."
        
    try:
        marks_float = float(marks)
    except (ValueError, TypeError):
        return False, "Marks must be a valid number between 0 and 100."

    if math.isnan(marks_float) or math.isinf(marks_float):
        return False, "Marks must be a valid number between 0 and 100."

    if marks_float < 0 or marks_float > 100:
        return False, "Marks must be between 0 and 100."
        
    # Round to 2 decimal places
    return True, round(marks_float, 2)


def calculate_grade(marks):
    """
    Calculates grade based on marks obtained:
    90 - 100 -> A+
    80 - 89.99 -> A
    70 - 79.99 -> B
    60 - 69.99 -> C
    50 - 59.99 -> D
    0 - 49.99 -> F
    """
    if marks is None:
        return "N/A"
    try:
        m = float(marks)
    except (ValueError, TypeError):
        return "N/A"
        
    if m >= 90:
        return "A+"
    elif m >= 80:
        return "A"
    elif m >= 70:
        return "B"
    elif m >= 60:
        return "C"
    elif m >= 50:
        return "D"
    else:
        return "F"


def validate_student(data, existing_student_id=None, db=None):
    """
    Validates complete student form submission.
    Returns: (is_valid: bool, errors: dict, cleaned_data: dict)
    """
    errors = {}
    cleaned = {}
    
    # 1. Register Number
    ok, res = validate_register_number(data.get("register_number"), existing_student_id, db)
    if ok:
        cleaned["register_number"] = res
    else:
        errors["register_number"] = res
        
    # 2. Name
    ok, res = validate_name(data.get("name"))
    if ok:
        cleaned["name"] = res
    else:
        errors["name"] = res
        
    # 3. Department
    ok, res = validate_department(data.get("department"))
    if ok:
        cleaned["department"] = res
    else:
        errors["department"] = res
        
    # 4. Email
    ok, res = validate_email(data.get("email"))
    if ok:
        cleaned["email"] = res
    else:
        errors["email"] = res
        
    # 5. Marks
    ok, res = validate_marks(data.get("marks"))
    if ok:
        cleaned["marks"] = res
    else:
        errors["marks"] = res
        
    is_valid = len(errors) == 0
    return is_valid, errors, cleaned


# ==========================================
# Authentication / User Validation
# ==========================================

def validate_username(username, db=None):
    """
    Validates administrator username:
    - Required, 3 to 20 characters
    - Allowed chars: letters, digits, underscore, dot, hyphen
    - Unique (case-insensitive) across users table
    """
    if username is None or not str(username).strip():
        return False, "Username is required."

    clean_username = str(username).strip()
    if len(clean_username) < 3 or len(clean_username) > 20:
        return False, "Username must be between 3 and 20 characters."

    if not USERNAME_REGEX.match(clean_username):
        return False, "Username can only contain letters, numbers, dots, hyphens, and underscores."

    if db is not None:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (clean_username,))
        if cursor.fetchone():
            return False, f"Username '{clean_username}' is already taken."

    return True, clean_username


def validate_password(password):
    """
    Validates administrator password:
    - Required, 6 to 64 characters
    - Must contain at least one letter and one digit
    """
    if password is None or str(password) == "":
        return False, "Password is required."

    pw = str(password)
    if len(pw) < 6 or len(pw) > 64:
        return False, "Password must be between 6 and 64 characters."

    if not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw):
        return False, "Password must include at least one letter and one number."

    return True, pw


def validate_registration(data, db=None):
    """
    Validates administrator registration payload.
    Returns: (is_valid: bool, errors: dict, cleaned_data: dict)
    """
    errors = {}
    cleaned = {}

    ok, res = validate_username(data.get("username"), db=db)
    if ok:
        cleaned["username"] = res
    else:
        errors["username"] = res

    ok, res = validate_name(data.get("full_name"))
    if ok:
        cleaned["full_name"] = res
    else:
        errors["full_name"] = res

    ok, res = validate_email(data.get("email"))
    if ok:
        if db is not None:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (res,))
            if cursor.fetchone():
                errors["email"] = f"Email '{res}' is already registered."
            else:
                cleaned["email"] = res
        else:
            cleaned["email"] = res
    else:
        errors["email"] = res

    ok, res = validate_password(data.get("password"))
    if ok:
        cleaned["password"] = res
        confirm = data.get("confirm_password", "")
        if res != str(confirm):
            errors["confirm_password"] = "Passwords do not match."
    else:
        errors["password"] = res

    return len(errors) == 0, errors, cleaned


def validate_password_change(current_password, new_password, confirm_password, stored_password):
    """
    Validates administrator password update form.
    Returns: (is_valid: bool, errors: dict)
    """
    errors = {}
    if not current_password:
        errors["current_password"] = "Current password is required."
    elif current_password != stored_password:
        errors["current_password"] = "Current password is incorrect."

    ok, res = validate_password(new_password)
    if not ok:
        errors["new_password"] = res
    elif current_password and new_password == current_password:
        errors["new_password"] = "New password must be different from your current password."
    elif str(new_password) != str(confirm_password or ""):
        errors["confirm_password"] = "New passwords do not match."

    return len(errors) == 0, errors
