import json
import azure.functions as func
import pytest
from function_app import app

# Mock the Azure Table Storage for testing
@pytest.fixture(autouse=True)
def mock_table_storage(monkeypatch):
    # Create a mock table client with in-memory storage
    mock_tasks = []
    
    class MockTableClient:
        def create_entity(self, entity):
            mock_tasks.append(entity)
            return entity
            
        def query_entities(self, filter_string):
            if "status eq" in filter_string:
                status = filter_string.split("'")[1]
                return [entity for entity in mock_tasks if entity.get("status") == status]
            return mock_tasks
            
        def get_entity(self, partition_key, row_key):
            for entity in mock_tasks:
                if entity.get("RowKey") == row_key:
                    return entity
            raise Exception("Entity not found")
            
        def update_entity(self, entity, mode=None):
            for i, task in enumerate(mock_tasks):
                if task.get("RowKey") == entity.get("RowKey"):
                    mock_tasks[i] = entity
                    return
                    
        def delete_entity(self, partition_key, row_key):
            for i, task in enumerate(mock_tasks):
                if task.get("RowKey") == row_key:
                    mock_tasks.pop(i)
                    return
    
    # Replace the get_table_client function
    def mock_get_table_client():
        return MockTableClient()
        
    # Apply the mock
    monkeypatch.setattr("function_app.get_table_client", mock_get_table_client)
    
    # Clear mock tasks before each test
    mock_tasks.clear()

def test_create_task():
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='POST',
        url='/api/tasks',
        headers={'Content-Type': 'application/json'},
        body=json.dumps({"title": "Test Task", "description": "Testing"}).encode()
    )
    
    # Import the function directly
    from function_app import create_task
    
    # Call our function directly
    resp = create_task(req)
    
    # Check response
    assert resp.status_code == 201
    response_body = json.loads(resp.get_body())
    assert response_body["title"] == "Test Task"
    assert response_body["description"] == "Testing"
    assert response_body["status"] == "pending"

def test_get_tasks():
    # First create a task
    create_req = func.HttpRequest(
        method='POST',
        url='/api/tasks',
        headers={'Content-Type': 'application/json'},
        body=json.dumps({"title": "Test Task"}).encode()
    )
    
    # Import the functions directly
    from function_app import create_task, get_tasks
    
    # Create a task first
    create_task(create_req)
    
    # Now get all tasks
    get_req = func.HttpRequest(
        method='GET',
        url='/api/tasks',
        body=None
    )
    
    # Call our function
    resp = get_tasks(get_req)
    
    # Check response
    assert resp.status_code == 200
    response_body = json.loads(resp.get_body())
    assert len(response_body) == 1
    assert response_body[0]["title"] == "Test Task"