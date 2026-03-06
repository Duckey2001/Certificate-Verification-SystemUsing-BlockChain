from database import SessionLocal
from models import User

db = SessionLocal()
user = db.query(User).filter(User.email == 'mpholekunye6@gmail.com').first()
print(f"User found: {user is not None}")
if user:
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Role: {user.role}")
    print(f"Password hash exists: {user.password_hash is not None}")
else:
    print("User not found")
db.close()
