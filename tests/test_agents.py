import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.connection import get_db
from backend.database.models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestAgents:
    def test_clock_agent(self):
        """Test clock in/out functionality"""
        # Create test user
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        
        # Login
        response = client.post("/api/auth/token", data={
            "username": "testuser",
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Test clock in
        response = client.post(
            "/api/agents/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "agent_type": "clock",
                "action": "process_natural_language",
                "parameters": {"query": "Clock me in"},
                "context": {}
            }
        )
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert "clocked in" in response.json()["output"].lower()
    
    def test_task_agent(self):
        """Test task creation and management"""
        # Login (using existing user from previous test)
        response = client.post("/api/auth/token", data={
            "username": "testuser",
            "password": "TestPass123!"
        })
        token = response.json()["access_token"]
        
        # Create task
        response = client.post(
            "/api/agents/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "agent_type": "task",
                "action": "process_natural_language",
                "parameters": {"query": "Create a task to update the website homepage"},
                "context": {}
            }
        )
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert "task created" in response.json()["output"].lower()

@pytest.mark.asyncio
async def test_rag_system():
    """Test RAG document retrieval"""
    from backend.rag.retriever import RAGRetriever
    
    retriever = RAGRetriever()
    await retriever.initialize()
    
    # Test document retrieval
    docs = await retriever.get_relevant_documents(
        "What is the clock-in policy?",
        filter={"category": "hr"}
    )
    
    assert len(docs) > 0
    assert "clock" in docs[0].lower()