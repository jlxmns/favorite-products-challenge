import enum


class User400Errors(str, enum.Enum):
    UserNotFound = "No user was found with the provided ID."


class UserCreate400Errors(str, enum.Enum):
    EmailInUse = "The provided email is already in use."


class UserUpdate400Errors(str, enum.Enum):
    UserNotFound = "No user was found with the provided ID."
    EmailInUse = "The provided email is already in use."


user_errors = {
    400: User400Errors
}

user_create_errors = {
    400: UserCreate400Errors
}

user_update_errors = {
    400: UserUpdate400Errors
}