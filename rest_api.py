"""
REST API wrapper for MCP OTP Server compatible with Zendesk
Provides a simple HTTP API that Zendesk can connect to
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from pathlib import Path
from typing import Optional, List
import pyotp
import time

# Initialize FastAPI app
app = FastAPI(
    title="OTP MCP REST API for Zendesk",
    version="1.0.0",
    description="REST API for OTP generation compatible with Zendesk MCP Connections"
)

# Configure CORS for Zendesk
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize token database
token_db = None

class Token(BaseModel):
    name: str
    type: str
    secret: Optional[str] = None

class GenerateOTPRequest(BaseModel):
    token_name: str

class GenerateOTPResponse(BaseModel):
    success: bool
    otp: str
    token_name: str
    token_type: str
    time_remaining: Optional[int] = None

class AddTokenRequest(BaseModel):
    name: str
    secret: str
    type: str = "totp"  # totp or hotp

class ListTokensResponse(BaseModel):
    success: bool
    tokens: List[Token]

def get_token_db():
    """Lazy load token database"""
    global token_db
    if token_db is None:
        from freakotp.token import TokenDb
        db_path = Path(os.environ.get("OTP_MCP_SERVER_DB", "/app/freakotp.db"))
        token_db = TokenDb(db_path)
        logging.info(f"Initialized token database at {db_path}")
    return token_db

@app.on_event("startup")
async def startup_event():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.info("Starting OTP REST API for Zendesk")
    # Initialize database
    get_token_db()

@app.get("/")
async def root():
    return {
        "service": "OTP MCP REST API for Zendesk",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate": "POST /v1/mcp/generate",
            "list": "GET /v1/mcp/tokens",
            "add": "POST /v1/mcp/tokens"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "otp-mcp-rest-api"}

@app.get("/v1/mcp")
async def mcp_info():
    """Info endpoint for Zendesk MCP connection"""
    return {
        "service": "OTP MCP",
        "version": "1.0.0",
        "capabilities": ["generate_otp", "list_tokens", "add_token"],
        "status": "ready"
    }

@app.post("/v1/mcp/generate", response_model=GenerateOTPResponse)
async def generate_otp(request: GenerateOTPRequest):
    """Generate OTP for a given token name"""
    try:
        db = get_token_db()
        token = db.get(request.token_name)

        if not token:
            raise HTTPException(status_code=404, detail=f"Token '{request.token_name}' not found")

        # Generate OTP
        if token.type == "totp":
            totp = pyotp.TOTP(token.secret)
            otp = totp.now()
            time_remaining = 30 - (int(time.time()) % 30)
        elif token.type == "hotp":
            hotp = pyotp.HOTP(token.secret)
            otp = hotp.at(token.counter)
            token.counter += 1
            db.update(token)
            time_remaining = None
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported token type: {token.type}")

        return GenerateOTPResponse(
            success=True,
            otp=otp,
            token_name=request.token_name,
            token_type=token.type,
            time_remaining=time_remaining
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating OTP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/mcp/tokens", response_model=ListTokensResponse)
async def list_tokens():
    """List all available token names"""
    try:
        db = get_token_db()
        tokens = db.list()
        return ListTokensResponse(
            success=True,
            tokens=[Token(name=t.name, type=t.type) for t in tokens]
        )
    except Exception as e:
        logging.error(f"Error listing tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/mcp/tokens")
async def add_token(request: AddTokenRequest):
    """Add a new OTP token"""
    try:
        db = get_token_db()
        from freakotp.token import Token as FreakOTPToken

        token = FreakOTPToken(
            name=request.name,
            secret=request.secret,
            type=request.type,
            counter=0 if request.type == "hotp" else None
        )
        db.add(token)

        return {
            "success": True,
            "message": f"Token '{request.name}' added successfully",
            "token": {
                "name": token.name,
                "type": token.type
            }
        }
    except Exception as e:
        logging.error(f"Error adding token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
