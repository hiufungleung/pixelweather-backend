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
TOKEN_VALID_DURATION = 60   # days

# post related
POST_EXPIRY_WINDOW = 30             # minutes
POST_ALERT_EXPIRY_WINDOW = 5        # minutes

NOTIFICATION_ALERT_THRESHOLD = 2

WEATHER_ONE_TO_N = {
    40: [40, 41],
    43: [42, 43, 44],
    21: [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
    5: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    45: [45],
    46: [46],
    47: [47],
    48: [48],
    49: [49]
}

WEATHER_N_TO_ONE = {
    1: 5,
    2: 5,
    3: 5,
    4: 5,
    5: 5,
    6: 5,
    7: 5,
    8: 5,
    9: 5,
    10: 5,
    14: 21,
    15: 21,
    16: 21,
    17: 21,
    18: 21,
    19: 21,
    20: 21,
    21: 21,
    22: 21,
    23: 21,
    24: 21,
    25: 21,
    26: 21,
    27: 21,
    28: 21,
    29: 21,
    40: 40,
    41: 40,
    42: 43,
    43: 43,
    44: 43,
    45: 45,
    46: 46,
    47: 47,
    48: 48,
    49: 49
}