# /app/services/external/fake_user_service.py
# This file simulates a user database for authentication purposes.
# In a real application, this would be replaced by a proper database service.

from app.models.user import User

# A fake database of users
fake_users_db = {
    "testuser": {
        "id": "user123",
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "testpassword", # In a real app, this would be a hash
        "disabled": False,
    },
    "inactiveuser": {
        "id": "user456",
        "username": "inactiveuser",
        "full_name": "Inactive User",
        "email": "inactive@example.com",
        "password": "inactivepassword",
        "disabled": True,
    },
}

def get_user(db: dict, username: str) -> dict | None:
    if username in db:
        return db[username]
    return None
