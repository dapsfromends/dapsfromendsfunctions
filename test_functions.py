import json
import azure.functions as func
import pytest
from function_app import app, tasks

# Clear tasks before each test
@pytest.fixture(autouse=True)
def clear_tasks():
    tasks.clear()
    yield

def test_create_task():
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='POST',
        url='/api/tasks',
        headers={'Content-Type': 'application/json'},
        body=json.dumps({"title": "Test Task", "description": "Testing"}).encode()
    )
    
    # Call our function
    resp = app.get_routes()[1].get_user_function()(req)
    
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
    app.get_routes()[1].get_user_function()(create_req)
    
    # Now get all tasks
    req = func.HttpRequest(
        method='GET',
        url='/api/tasks',
        body=None
    )
    
    # Call our function
    resp = app.get_routes()[2].get_user_function()(req)
    
    # Check response
    assert resp.status_code == 200
    response_body = json.loads(resp.get_body())
    assert len(response_body) == 1
    assert response_body[0]["title"] == "Test Task"