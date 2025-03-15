import json
import azure.functions as func
import pytest
import os
import sys
import time
from datetime import datetime

# Import directly from function_app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import function_app

# Ensure we have a storage connection string
@pytest.fixture(scope="session", autouse=True)
def check_environment():
    # Check if the storage connection string is available
    assert "AzureWebJobsStorage" in os.environ, "No storage connection string found in environment variables"
    
    # Create table if it doesn't exist
    table_client = function_app.get_table_client()
    # Wait a moment to ensure table is created
    time.sleep(1)

# Clean up before and after tests
@pytest.fixture(autouse=True)
def clean_table():
    # Before test: Clean up any existing tasks
    table_client = function_app.get_table_client()
    try:
        entities = table_client.query_entities("PartitionKey eq 'tasks'")
        for entity in entities:
            table_client.delete_entity('tasks', entity['RowKey'])
    except Exception as e:
        print(f"Error cleaning table: {str(e)}")
    
    # Run the test
    yield
    
    # After test: Clean up again
    try:
        entities = table_client.query_entities("PartitionKey eq 'tasks'")
        for entity in entities:
            table_client.delete_entity('tasks', entity['RowKey'])
    except Exception as e:
        print(f"Error cleaning table: {str(e)}")

def test_create_task():
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='POST',
        url='/api/tasks',
        headers={'Content-Type': 'application/json'},
        body=json.dumps({"title": "Test Task", "description": "Testing"}).encode()
    )
    
    # Call our function directly
    resp = function_app.create_task(req)
    
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
    
    # Create a task first
    function_app.create_task(create_req)
    
    # Now get all tasks
    get_req = func.HttpRequest(
        method='GET',
        url='/api/tasks',
        body=None
    )
    
    # Call our function
    resp = function_app.get_tasks(get_req)
    
    # Check response
    assert resp.status_code == 200
    response_body = json.loads(resp.get_body())
    assert len(response_body) == 1
    assert response_body[0]["title"] == "Test Task"