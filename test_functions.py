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