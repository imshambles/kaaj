"""
API Integration Tests for the Lender Matching Platform
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.main import app


client = TestClient(app)


# ============== Lender API Tests ==============

class TestLenderAPI:
    
    def test_list_lenders(self):
        """GET /api/lenders should return list of lenders"""
        response = client.get("/api/lenders")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_rule_types(self):
        """GET /api/lenders/rule-types should return list of rule types"""
        response = client.get("/api/lenders/rule-types")
        
        assert response.status_code == 200
        rule_types = response.json()
        assert isinstance(rule_types, list)
        assert "fico_min" in rule_types
        assert "excluded_states" in rule_types
        assert "no_bankruptcies" in rule_types
        assert len(rule_types) >= 20  # We have 27+ rule types
    
    def test_get_nonexistent_lender(self):
        """GET /api/lenders/{id} with invalid UUID should return 404"""
        fake_id = str(uuid4())
        response = client.get(f"/api/lenders/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ============== Application API Tests ==============

class TestApplicationAPI:
    
    def test_create_application_validation(self):
        """POST /api/applications with invalid data should return 422"""
        invalid_data = {
            "borrower": {},  # Missing required fields
            "application": {}
        }
        
        response = client.post("/api/applications", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_nonexistent_application(self):
        """GET /api/applications/{id} with invalid ID should return 404"""
        fake_id = str(uuid4())
        response = client.get(f"/api/applications/{fake_id}")
        
        assert response.status_code == 404


# ============== Health Check Tests ==============

class TestHealthCheck:
    
    def test_root_endpoint(self):
        """Root endpoint should return API info"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data or "name" in data


# ============== Rule Types Coverage Tests ==============

class TestRuleTypesCoverage:
    
    def test_all_evaluators_have_names(self):
        """All registered evaluators should have valid names"""
        response = client.get("/api/lenders/rule-types")
        rule_types = response.json()
        
        for rule_type in rule_types:
            assert isinstance(rule_type, str)
            assert len(rule_type) > 0
            assert "_" in rule_type or len(rule_type) > 3  # Naming convention
    
    def test_expected_rule_categories_covered(self):
        """All major rule categories should be covered"""
        response = client.get("/api/lenders/rule-types")
        rule_types = response.json()
        
        # Credit score rules
        assert any("fico" in r for r in rule_types)
        assert any("paynet" in r for r in rule_types)
        
        # Business rules
        assert any("tib" in r for r in rule_types)  # time in business
        
        # Exclusion rules
        assert any("excluded" in r for r in rule_types)
        
        # Derogatory credit rules
        assert any("bankruptcy" in r for r in rule_types)
        assert any("judgments" in r or "foreclosure" in r for r in rule_types)
        
        # Transaction type rules
        assert any("private_party" in r or "refinance" in r for r in rule_types)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
