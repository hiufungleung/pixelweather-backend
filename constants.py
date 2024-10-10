# Successful Responses
# 200 OK
SUCCESS_LOGIN = "Login Successfully"
SUCCESS_LOGOUT = "Logout Successfully"
SUCCESS_EMAIL_CHANGED = "Email Changed Successfully"
SUCCESS_PASSWORD_CHANGED = "Password Changed Successfully"
SUCCESS_USERNAME_CHANGED = "Username Changed Successfully"


SUCCESS_DATA_RETRIEVED = "Data retrieved Successfully"
SUCCESS_DATA_UPDATED = "Data updated Successfully"
SUCCESS_DATA_DELETED = "Data deleted Successfully"

# 201 Created
SUCCESS_SIGN_UP = "Sign Up Successful"
SUCCESS_DATA_CREATED = "Data created Successfully"
NOTIFICATION_SENT = "Notification Sent"

# 204 No Content
NOT_IN_ALERT_TIME = "Not in user's alert time"
NOT_MEET_THRESHOLD = "No notification would be sent"

# Client Error Responses
# 400 Bad Request
MISSING_SIGNUP_INFO = "Missing email, username or password"
MISSING_LOGIN_INFO = "Missing email or password"
MISSING_OLD_NEW_PASSWORD = "Missing current or new password"
MISSING_PASSWORD = "Missing password"
MISSING_NEW_USERNAME = "Missing new username"
MISSING_TOKEN = "Missing token"
MISSING_EMAIL = "Missing email"

MISSING_DATA = "Missing (part of) required data"

# 401 Unauthorized
INVALID_CREDENTIALS = "Invalid credentials"
INVALID_TOKEN = "Invalid or expired token"

# 403 Forbidden
INCORRECT_PASSWORD = "Incorrect password"

# 404 Not found
NOT_FOUND_RECORDS = "Record is not found"

# 409 Conflict
CONFLICT_EMAIL = "Email is already in use"
CONFLICT_SAVED_LABEL = "The label has been used by user"
CONFLICT_SAVED_SUBURB = "User has already saved this suburb"
CONFLICT_ALERT_SUBURB = "User has set this alert suburb"
CONFLICT_ALERT_TIME = "User has already saved an alert time for this time range"

# 422 Unprocessable Entity
MALFORMED_EMAIL_PASSWORD = "Invalid email or password format"
MALFORMED_EMAIL = "Invalid email format"
MALFORMED_PASSWORD = "Invalid password format"
MALFORMED_USERNAME = "Invalid username format"
REQUIREMENT_EMAIL = "Must be an email format"
REQUIREMENT_PASSWORD = "Password must be at least 8 characters, include an uppercase letter, a number, and a special character"
REQUIREMENT_USERNAME = "Username must contain no more than 31 characters"

MALFORMED_TIME = "Invalid time range: start_time cannot be later than end_time"
NOT_EXIST_FK = (
    "The record with the corresponding PK or FK does not exist, or format is incorrect"
)


# 500 Internal Server Error
INTERNAL_SERVER_ERROR = "An internal server error occurred. Please try again later"

# Varchar length
USERNAME_LENGTH = 31

# Token expire
TOKEN_VALID_DURATION = 60

# post related
POST_EXPIRY_WINDOW = 30 # minutes

NOTIFICATION_ALERT_THRESHOLD = 2