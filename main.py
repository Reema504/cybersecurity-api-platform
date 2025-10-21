# ===============================================
# 1. Imports
# ===============================================
import subprocess
import time
from collections import defaultdict
import logging # --- Logging: Import the logging library ---

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import datetime

# ===============================================
# --- Logging: Basic logger configuration ---
# ===============================================
# Configure logging level (INFO and above) and format (timestamp, name, level, message)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Get a logger instance for this module
logger = logging.getLogger(__name__)

# ===============================================
# 2. Database Setup
# ===============================================
DATABASE_URL = "postgresql://postgres:postgres@db/cyber_platform_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PingResult(Base):
    __tablename__ = "ping_results"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class NmapResult(Base):
    __tablename__ = "nmap_results"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===============================================
# 3. Create FastAPI Application
# ===============================================
app = FastAPI(
    title="Cybersecurity Tools Management Platform",
    description="An API to manage and run cybersecurity tools.",
    version="0.0.1",
)

# ===============================================
# 4. Simple DoS Protection Middleware
# ===============================================
request_counts = defaultdict(list)
TIME_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 20

@app.middleware("http")
async def dos_protection_middleware(request: Request, call_next):
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    current_time = time.time()

    request_counts[client_ip] = [
        timestamp for timestamp in request_counts[client_ip]
        if current_time - timestamp < TIME_WINDOW_SECONDS
    ]
    request_counts[client_ip].append(current_time)

    # --- Logging: Log request count per IP (Debug level) ---
    logger.debug(f"Client IP: {client_ip}, Request Count: {len(request_counts[client_ip])}") # Using debug to make it less verbose

    if len(request_counts[client_ip]) > MAX_REQUESTS_PER_WINDOW:
        # --- Logging: Log potential DoS attempt ---
        logger.warning(f"DoS protection triggered for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"message": "Too many requests. Possible DoS attack detected. Please wait."}
        )

    response = await call_next(request)
    return response

# ===============================================
# 5. API Endpoints
# ===============================================
@app.get("/")
def read_root():
    logger.info("Root endpoint accessed") # --- Logging: Log access to root endpoint ---
    return {"message": "Welcome! Use /ping/{hostname} or /scan/nmap/{hostname}"}

@app.get("/ping/{hostname}")
def run_ping(hostname: str, db: Session = Depends(get_db)):
    logger.info(f"Received ping request for hostname: {hostname}") # --- Logging: Log start of Ping request ---
    command = ["ping", "-c", "4", hostname]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=20)
        db_ping_result = PingResult(hostname=hostname, output=result.stdout)
        db.add(db_ping_result)
        db.commit()
        logger.info(f"Ping successful for {hostname}, result saved.") # --- Logging: Log successful Ping ---
        return {"hostname": hostname, "output": result.stdout}
    except subprocess.CalledProcessError as e:
        db_ping_result = PingResult(hostname=hostname, error=e.stderr)
        db.add(db_ping_result)
        db.commit()
        logger.error(f"Ping failed for {hostname}. Error: {e.stderr}") # --- Logging: Log failed Ping ---
        return {"hostname": hostname, "error": e.stderr}
    except Exception as e: # --- Logging: Catch any other potential errors ---
        logger.exception(f"An unexpected error occurred during ping for {hostname}: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error during ping."})


@app.get("/history/ping")
def get_ping_history(db: Session = Depends(get_db)):
    logger.info("Accessed ping history endpoint") # --- Logging: Log history request ---
    try:
        results = db.query(PingResult).order_by(PingResult.id.desc()).all()
        return results
    except Exception as e: # --- Logging: Catch any potential errors ---
        logger.exception(f"An unexpected error occurred while fetching ping history: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error fetching ping history."})


@app.get("/scan/nmap/{hostname}")
def run_nmap_scan(hostname: str, db: Session = Depends(get_db)):
    logger.info(f"Received nmap scan request for hostname: {hostname}") # --- Logging: Log start of Nmap request ---
    command = ["nmap", "-F", hostname]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=120)
        db_nmap_result = NmapResult(hostname=hostname, output=result.stdout)
        db.add(db_nmap_result)
        db.commit()
        logger.info(f"Nmap scan successful for {hostname}, result saved.") # --- Logging: Log successful Nmap ---
        return {"hostname": hostname, "output": result.stdout}
    except subprocess.CalledProcessError as e:
        db_nmap_result = NmapResult(hostname=hostname, error=e.stderr)
        db.add(db_nmap_result)
        db.commit()
        logger.error(f"Nmap scan failed for {hostname}. Error: {e.stderr}") # --- Logging: Log failed Nmap ---
        return {"hostname": hostname, "error": e.stderr}
    except Exception as e: # --- Logging: Catch any other potential errors ---
        logger.exception(f"An unexpected error occurred during nmap scan for {hostname}: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error during nmap scan."})


@app.get("/history/nmap")
def get_nmap_history(db: Session = Depends(get_db)):
    logger.info("Accessed nmap history endpoint") # --- Logging: Log history request ---
    try:
        results = db.query(NmapResult).order_by(NmapResult.id.desc()).all()
        return results
    except Exception as e: # --- Logging: Catch any potential errors ---
        logger.exception(f"An unexpected error occurred while fetching nmap history: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error fetching nmap history."})

