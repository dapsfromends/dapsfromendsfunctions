import azure.functions as func
import logging
import json
import uuid
import os
from datetime import datetime
from azure.data.tables import TableServiceClient, TableClient, UpdateMode
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Azure Table Storage configuration
connection_string = os.environ.get("AzureWebJobsStorage")
table_name = "tasks"

# Helper function to get table client
def get_table_client():
    try:
        table_service = TableServiceClient.from_connection_string(connection_string)
        try:
            # Try to create table if it doesn't exist
            table_service.create_table(table_name)
            logging.info(f"Table {table_name} created successfully.")
        except ResourceExistsError:
            logging.info(f"Table {table_name} already exists.")
        
        # Get table client
        return table_service.get_table_client(table_name)
    except Exception as e:
        logging.error(f"Error connecting to table storage: {str(e)}")
        raise

# Helper function to convert entity to task dict
def entity_to_task(entity):
    task = {
        "id": entity["RowKey"],
        "title": entity["title"],
        "description": entity.get("description", ""),
        "status": entity["status"],
        "created_at": entity["created_at"],
        "completed_at": entity.get("completed_at", None)
    }
    return task

# Keep your original function unchanged
@app.route(route="oladapofunction2")
def oladapofunction2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "My name is Dapo ",
             status_code=200
        )

# Test slow response function for alert testing
@app.route(route="test-slow-response")
def test_slow_response(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Testing slow response for alert monitoring.')
    
    # Simulate a long-running process (5-second delay)
    import time
    time.sleep(5)
    
    return func.HttpResponse(
        "This response was intentionally delayed to test alerts",
        status_code=200
    )

# Add new function: Create a new task
@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Create Task function processed a request.')
    
    try:
        # Get request body
        req_body = req.get_json()
        
        # Add enhanced logging
        logging.info(f'Request body: {req_body}')
        
        # Check if required fields are present
        if not req_body or 'title' not in req_body:
            logging.warning('Missing required field: title')
            return func.HttpResponse(
                "Please pass a title in the request body",
                status_code=400
            )
            
        # Create new task with unique ID
        task_id = str(uuid.uuid4())
        
        task_entity = {
            "PartitionKey": "tasks",  # Use a single partition for simplicity
            "RowKey": task_id,
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        # Log task creation
        logging.info(f'Created new task with ID: {task_id}, Title: "{task_entity["title"]}"')
        
        # Add to Table Storage
        table_client = get_table_client()
        table_client.create_entity(task_entity)
        
        # Convert back to our task format for response
        new_task = entity_to_task(task_entity)
        
        return func.HttpResponse(
            json.dumps(new_task),
            mimetype="application/json",
            status_code=201
        )
        
    except ValueError as e:
        logging.error(f'Invalid request body: {str(e)}')
        return func.HttpResponse(
            "Invalid request body",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Error creating task: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )

# Get all tasks
@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Get Tasks function processed a request.')
    
    try:
        # Get status filter if provided
        status = req.params.get('status')
        logging.info(f'Filtering tasks by status: {status if status else "none"}')
        
        # Get table client
        table_client = get_table_client()
        
        # Query for tasks
        if status:
            query_filter = f"PartitionKey eq 'tasks' and status eq '{status}'"
        else:
            query_filter = "PartitionKey eq 'tasks'"
        
        entities = table_client.query_entities(query_filter)
        tasks = [entity_to_task(entity) for entity in entities]
        
        logging.info(f'Retrieved {len(tasks)} tasks')
        return func.HttpResponse(
            json.dumps(tasks),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error retrieving tasks: {str(e)}")
        return func.HttpResponse(
            f"Error retrieving tasks: {str(e)}",
            status_code=500
        )

# Get task by ID
@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Get Task by ID function processed a request.')
    
    try:
        # Get task ID from route
        task_id = req.route_params.get('id')
        logging.info(f'Looking for task with ID: {task_id}')
        
        # Get table client
        table_client = get_table_client()
        
        try:
            # Get entity from table
            entity = table_client.get_entity('tasks', task_id)
            task = entity_to_task(entity)
            
            logging.info(f'Found task: "{task["title"]}"')
            return func.HttpResponse(
                json.dumps(task),
                mimetype="application/json"
            )
        except ResourceNotFoundError:
            logging.warning(f'Task with ID {task_id} not found')
            return func.HttpResponse(
                "Task not found",
                status_code=404
            )
    except Exception as e:
        logging.error(f"Error retrieving task: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )

# Update task
@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Update Task function processed a request.')
    
    try:
        # Get task ID from route
        task_id = req.route_params.get('id')
        logging.info(f'Updating task with ID: {task_id}')
        
        # Get request body
        req_body = req.get_json()
        logging.info(f'Update request body: {req_body}')
        
        # Get table client
        table_client = get_table_client()
        
        try:
            # Get existing entity
            entity = table_client.get_entity('tasks', task_id)
            
            # Update fields
            if 'title' in req_body:
                entity['title'] = req_body['title']
            if 'description' in req_body:
                entity['description'] = req_body['description']
            if 'status' in req_body:
                entity['status'] = req_body['status']
                
            # Update entity in table
            table_client.update_entity(entity, mode=UpdateMode.REPLACE)
            
            # Convert to task format for response
            task = entity_to_task(entity)
            
            logging.info(f'Task updated successfully: "{task["title"]}"')
            return func.HttpResponse(
                json.dumps(task),
                mimetype="application/json"
            )
        except ResourceNotFoundError:
            logging.warning(f'Task with ID {task_id} not found for update')
            return func.HttpResponse(
                "Task not found",
                status_code=404
            )
    except ValueError:
        logging.error('Invalid request body for update')
        return func.HttpResponse(
            "Invalid request body",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Error updating task: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )

# Delete task
@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Delete Task function processed a request.')
    
    try:
        # Get task ID from route
        task_id = req.route_params.get('id')
        logging.info(f'Attempting to delete task with ID: {task_id}')
        
        # Get table client
        table_client = get_table_client()
        
        try:
            # Get entity before deletion for response
            entity = table_client.get_entity('tasks', task_id)
            deleted_task = entity_to_task(entity)
            
            # Delete entity
            table_client.delete_entity('tasks', task_id)
            
            logging.info(f'Task deleted successfully: "{deleted_task["title"]}"')
            return func.HttpResponse(
                json.dumps({"message": "Task deleted successfully", "task": deleted_task}),
                mimetype="application/json"
            )
        except ResourceNotFoundError:
            logging.warning(f'Task with ID {task_id} not found for deletion')
            return func.HttpResponse(
                "Task not found",
                status_code=404
            )
    except Exception as e:
        logging.error(f"Error deleting task: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )

# Mark task as complete
@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Complete Task function processed a request.')
    
    try:
        # Get task ID from route
        task_id = req.route_params.get('id')
        logging.info(f'Marking task with ID {task_id} as complete')
        
        # Get table client
        table_client = get_table_client()
        
        try:
            # Get existing entity
            entity = table_client.get_entity('tasks', task_id)
            
            # Update status and completion time
            entity['status'] = 'completed'
            entity['completed_at'] = datetime.now().isoformat()
            
            # Update entity in table
            table_client.update_entity(entity, mode=UpdateMode.REPLACE)
            
            # Convert to task format for response
            task = entity_to_task(entity)
            
            logging.info(f'Task marked as complete: "{task["title"]}"')
            return func.HttpResponse(
                json.dumps(task),
                mimetype="application/json"
            )
        except ResourceNotFoundError:
            logging.warning(f'Task with ID {task_id} not found for completion')
            return func.HttpResponse(
                "Task not found",
                status_code=404
            )
    except Exception as e:
        logging.error(f"Error completing task: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )

# Analytics: Task completion statistics
@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Task Completion Statistics function processed a request.')
    
    try:
        # Get table client
        table_client = get_table_client()
        
        # Query for all tasks
        all_tasks = list(table_client.query_entities("PartitionKey eq 'tasks'"))
        total_tasks = len(all_tasks)
        completed_tasks = sum(1 for task in all_tasks if task["status"] == "completed")
        pending_tasks = total_tasks - completed_tasks
        
        # Calculate completion percentage
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Create statistics object
        stats = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_percentage": round(completion_percentage, 2)
        }
        
        logging.info(f'Analytics - Total: {total_tasks}, Completed: {completed_tasks}, Pending: {pending_tasks}, Completion: {round(completion_percentage, 2)}%')
        
        return func.HttpResponse(
            json.dumps(stats),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error retrieving analytics: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )

# Analytics: Productivity metrics by time period
@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Productivity Metrics function processed a request.')
    
    try:
        # Get optional date parameter (for future filtering)
        period = req.params.get('period', 'all')
        logging.info(f'Generating productivity metrics for period: {period}')
        
        # Get table client
        table_client = get_table_client()
        
        # Query for all tasks
        all_tasks = list(table_client.query_entities("PartitionKey eq 'tasks'"))
        tasks_created = len(all_tasks)
        tasks_completed = sum(1 for task in all_tasks if task["status"] == "completed")
        
        # Calculate average completion time (for completed tasks)
        completion_times = []
        for task in all_tasks:
            if task["status"] == "completed" and "completed_at" in task:
                created = datetime.fromisoformat(task["created_at"])
                completed = datetime.fromisoformat(task["completed_at"])
                completion_time_hours = (completed - created).total_seconds() / 3600
                completion_times.append(completion_time_hours)
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Create metrics object
        metrics = {
            "period": period,
            "tasks_created": tasks_created,
            "tasks_completed": tasks_completed,
            "completion_rate": round((tasks_completed / tasks_created * 100) if tasks_created > 0 else 0, 2),
            "average_completion_time_hours": round(avg_completion_time, 2)
        }
        
        logging.info(f'Productivity metrics calculated - Tasks created: {tasks_created}, Tasks completed: {tasks_completed}, Avg completion time: {round(avg_completion_time, 2)} hours')
        
        return func.HttpResponse(
            json.dumps(metrics),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error retrieving productivity metrics: {str(e)}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )