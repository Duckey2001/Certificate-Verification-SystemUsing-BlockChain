from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Hash the password
hashed_password = hash_password("password123")
print(hashed_password)

# Insert the user with the hashed password
INSERT INTO users (email, password, full_name, created_at)
VALUES (
    'issuer@example.com',
    '$2b$12$examplehashedpasswordhere', -- Replace with the hashed password
    'Issuer Name',
    NOW()
);