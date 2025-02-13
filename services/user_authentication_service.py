from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from model import Users

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate JWT Token
def create_access_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Decode JWT Token
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        return None

# Dependency for Protected Routes
def get_current_user(token: str):
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email

# Register User
@app.post("/register")
async def register(user: Users):
    if user.email in user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user[user.email] = {"email": user.email}

    return {"message": "User registered successfully"}

# Login User
@app.post("/login", response_model=Token)
async def login(user: Users):
    db_user = user.get(user.email)
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}

# Protected Route (Requires Authentication)
@app.get("/protected")
async def protected_route(email: str = Depends(get_current_user)):
    return {"message": "Welcome!", "email": email}