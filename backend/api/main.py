from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from .routers import auth, agents, employees, tasks, reports
from ..agents.agent_manager import get_agent_manager
from ..database.connection import init_db
from ..database.init_db import initialize_database
from ..rag.retriever import RAGRetriever
from ..rag.document_loader import DocumentLoader
from ..config.settings import settings
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
agent_manager = None
rag_retriever = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    global agent_manager, rag_retriever
    
    logger.info("Starting AI Operations Agent API...")
    
    # Initialize database
    logger.info("Initializing database...")
    initialize_database()
    
    # Initialize RAG system
    logger.info("Initializing RAG system...")
    rag_retriever = RAGRetriever()
    try:
        await rag_retriever.initialize()
        logger.info("RAG system initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize RAG system: {e}")
        logger.info("API will continue to run, but RAG functionality will be disabled")
        rag_retriever = None
    
    # Load documents into RAG (optional - skip if OpenAI quota exceeded)
    if rag_retriever is not None:
        logger.info("Loading company documents...")
        doc_loader = DocumentLoader(rag_retriever)
        try:
            await doc_loader.load_all_documents()
            logger.info("Company documents loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load company documents during startup: {e}")
            logger.info("API will continue to run, but RAG functionality may be limited")
    else:
        logger.info("Skipping document loading - RAG system not available")
    
    # Initialize agent manager
    logger.info("Initializing agent manager...")
    agent_manager = get_agent_manager()
    await agent_manager.initialize()
    
    logger.info("API startup complete!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    if agent_manager:
        await agent_manager.cleanup()
    if rag_retriever:
        await rag_retriever.cleanup()
    logger.info("API shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-powered operations assistant for SMEs",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Operations Agent API",
        "version": "1.0.0",
        "status": "operational"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_active": agent_manager is not None,
        "rag_active": rag_retriever is not None,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# API documentation
@app.get("/api")
async def api_documentation():
    return {
        "endpoints": {
            "auth": {
                "register": "POST /api/auth/register",
                "login": "POST /api/auth/token",
                "me": "GET /api/auth/me",
                "refresh": "POST /api/auth/refresh"
            },
            "agents": {
                "execute": "POST /api/agents/execute",
                "info": "GET /api/agents/info",
                "history": "GET /api/agents/actions/history",
                "action_detail": "GET /api/agents/actions/{action_id}",
                "override": "POST /api/agents/actions/{action_id}/override"
            },
            "employees": {
                "list": "GET /api/employees",
                "get": "GET /api/employees/{employee_id}",
                "update": "PUT /api/employees/{employee_id}",
                "attendance": "GET /api/employees/{employee_id}/attendance"
            },
            "tasks": {
                "list": "GET /api/tasks",
                "create": "POST /api/tasks",
                "get": "GET /api/tasks/{task_id}",
                "update": "PUT /api/tasks/{task_id}",
                "assign": "POST /api/tasks/{task_id}/assign"
            },
            "reports": {
                "generate": "POST /api/reports/generate",
                "list": "GET /api/reports",
                "get": "GET /api/reports/{report_id}"
            }
        }
    }