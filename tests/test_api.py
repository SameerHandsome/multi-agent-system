"""
Test suite for Multi-Agent System API
"""

import pytest
from fastapi.testclient import TestClient
from app import app
import json

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Multi-Agent System API"
        assert data["status"] == "running"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestQueryEndpoints:
    """Test query submission endpoints"""
    
    def test_submit_query_async(self):
        """Test async query submission"""
        payload = {
            "query": "Test query",
            "max_retries": 1
        }
        response = client.post("/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
    
    def test_submit_query_validation(self):
        """Test query validation"""
        # Empty query should fail
        payload = {"query": ""}
        response = client.post("/query", json=payload)
        assert response.status_code == 422
    
    def test_get_job_status_not_found(self):
        """Test getting status of non-existent job"""
        response = client.get("/status/nonexistent-job-id")
        assert response.status_code == 404
    
    def test_get_job_status_valid(self):
        """Test getting status of valid job"""
        # First submit a job
        payload = {"query": "Test query"}
        submit_response = client.post("/query", json=payload)
        job_id = submit_response.json()["job_id"]
        
        # Then check its status
        response = client.get(f"/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
    
    def test_list_jobs(self):
        """Test listing all jobs"""
        response = client.get("/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "jobs" in data
    
    def test_delete_job(self):
        """Test deleting a job"""
        # Submit a job
        payload = {"query": "Test query"}
        submit_response = client.post("/query", json=payload)
        job_id = submit_response.json()["job_id"]
        
        # Delete it
        response = client.delete(f"/job/{job_id}")
        assert response.status_code == 200
        
        # Verify it's gone
        status_response = client.get(f"/status/{job_id}")
        assert status_response.status_code == 404


class TestInputValidation:
    """Test input validation"""
    
    def test_max_retries_validation(self):
        """Test max_retries bounds"""
        # Too high
        payload = {"query": "Test", "max_retries": 10}
        response = client.post("/query", json=payload)
        assert response.status_code == 422
        
        # Negative
        payload = {"query": "Test", "max_retries": -1}
        response = client.post("/query", json=payload)
        assert response.status_code == 422
        
        # Valid
        payload = {"query": "Test", "max_retries": 2}
        response = client.post("/query", json=payload)
        assert response.status_code == 200


class TestCORS:
    """Test CORS headers"""
    
    def test_cors_headers(self):
        """Test that CORS headers are present"""
        response = client.get("/")
        assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_async_processing():
    """Test that async processing works"""
    # This would require mocking the agent system
    # or running actual agents (slower)
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])