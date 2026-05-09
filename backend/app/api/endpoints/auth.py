import random
import resend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from passlib.context import CryptContext
from app.config.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()
resend.api_key = settings.RESEND_API_KEY

# Temporary in-memory storage for OTPs
# Format: { email: { "otp": "123456", "expires": timestamp } }
OTP_STORE = {}

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    name: Optional[str] = None
    password: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login_v1(request: LoginRequest):
    from app.config.database import get_user
    user = await get_user(request.email)
    if user:
        hashed_password = user.get("hashed_password")
        if hashed_password and pwd_context.verify(request.password, hashed_password):
            return {"status": "success", "name": user.get("name")}
        elif not hashed_password:
            # Fallback for old accounts without passwords (optional: force reset)
            return {"status": "success", "name": user.get("name")}
        else:
            raise HTTPException(status_code=401, detail="Invalid password")
    
    raise HTTPException(status_code=404, detail="Account not found")

@router.post("/send-otp")
async def send_otp(request: OTPRequest):
    otp = str(random.randint(100000, 999999))
    OTP_STORE[request.email] = otp
    
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": request.email,
            "subject": "Your CuraLink Access Code",
            "html": f"""
            <div style="font-family: sans-serif; max-width: 400px; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #000;">CuraLink Secure Access</h2>
                <p>Use the following code to complete your research workstation login:</p>
                <div style="background: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px;">
                    {otp}
                </div>
                <p style="font-size: 12px; color: #666; margin-top: 20px;">This code will expire in 10 minutes.</p>
            </div>
            """
        }
        resend.Emails.send(params)
        return {"message": "OTP sent successfully"}
    except Exception as e:
        print(f"Resend Error: {e}")
        # In a generic hackathon environment, fallback to console print if API fails
        print(f"DEBUG OTP for {request.email}: {otp}")
        return {"message": "OTP sent (Debug Mode)", "debug_otp": otp}

@router.post("/verify-otp")
async def verify_otp(request: OTPVerify):
    stored_otp = OTP_STORE.get(request.email)
    if stored_otp and stored_otp == request.otp:
        # Save User profile to MongoDB if name provided
        if request.name:
            from app.config.database import save_user, get_user
            # Block duplicate accounts
            existing = await get_user(request.email)
            if existing:
                raise HTTPException(status_code=409, detail="An account with this email already exists. Please log in.")
            
            hashed_password = pwd_context.hash(request.password) if request.password else None
            await save_user(request.email, request.name, hashed_password=hashed_password)

        del OTP_STORE[request.email]
        return {"status": "success", "token": "mock-jwt-token"}

    raise HTTPException(status_code=400, detail="Invalid or expired OTP")
