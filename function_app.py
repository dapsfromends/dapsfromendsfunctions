import azure.functions as func
import logging
import json
import uuid
from datetime import datetime

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# In-memory database for tasks (in a real project, you'd use Azure Table Storage or Cosmos DB)
tasks = []

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
        new_task = {
            "id": str(uuid.uuid4()),
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        # Log task creation
        logging.info(f'Created new task with ID: {new_task["id"]}, Title: "{new_task["title"]}"')
        
        # Add to our "database"
        tasks.append(new_task)
        
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
    
    # Get status filter if provided
    status = req.params.get('status')
    logging.info(f'Filtering tasks by status: {status if status else "none"}')
    
    if status:
        filtered_tasks = [task for task in tasks if task['status'] == status]
        logging.info(f'Retrieved {len(filtered_tasks)} tasks with status "{status}"')
        return func.HttpResponse(
            json.dumps(filtered_tasks),
            mimetype="application/json"
        )
    else:
        logging.info(f'Retrieved all {len(tasks)} tasks')
        return func.HttpResponse(
            json.dumps(tasks),
            mimetype="application/json"
        )

# Get task by ID
@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Get Task by ID function processed a request.')
    
    # Get task ID from route
    task_id = req.route_params.get('id')
    logging.info(f'Looking for task with ID: {task_id}')
    
    # Find task with matching ID
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if task:
        logging.info(f'Found task: "{task["title"]}"')
        return func.HttpResponse(
            json.dumps(task),
            mimetype="application/json"
        )
    else:
        logging.warning(f'Task with ID {task_id} not found')
        return func.HttpResponse(
            "Task not found",
            status_code=404
        )

# Update task
@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Update Task function processed a request.')
    
    # Get task ID from route
    task_id = req.route_params.get('id')
    logging.info(f'Updating task with ID: {task_id}')
    
    try:
        # Get request body
        req_body = req.get_json()
        logging.info(f'Update request body: {req_body}')
        
        # Find task with matching ID
        task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
        
        if task_index is None:
            logging.warning(f'Task with ID {task_id} not found for update')
            return func.HttpResponse(
                "Task not found",
                status_code=404
            )
        
        # Update task fields but preserve ID and creation date
        current_task = tasks[task_index]
        updated_task = {
            "id": current_task["id"],
            "title": req_body.get("title", current_task["title"]),
            "description": req_body.get("description", current_task["description"]),
            "status": req_body.get("status", current_task["status"]),
            "created_at": current_task["created_at"],
            "completed_at": current_task["completed_at"]
        }
        
        # Replace task in list
        tasks[task_index] = updated_task
        logging.info(f'Task updated successfully: "{updated_task["title"]}"')
        
        return func.HttpResponse(
            json.dumps(updated_task),
            mimetype="application/json"
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
    
    # Get task ID from route
    task_id = req.route_params.get('id')
    logging.info(f'Attempting to delete task with ID: {task_id}')
    
    # Find task with matching ID
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
    
    if task_index is None:
        logging.warning(f'Task with ID {task_id} not found for deletion')
        return func.HttpResponse(
            "Task not found",
            status_code=404
        )
    
    # Remove task from list
    deleted_task = tasks.pop(task_index)
    logging.info(f'Task deleted successfully: "{deleted_task["title"]}"')
    
    return func.HttpResponse(
        json.dumps({"message": "Task deleted successfully", "task": deleted_task}),
        mimetype="application/json"
    )

# Mark task as complete
@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Complete Task function processed a request.')
    
    # Get task ID from route
    task_id = req.route_params.get('id')
    logging.info(f'Marking task with ID {task_id} as complete')
    
    # Find task with matching ID
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
    
    if task_index is None:
        logging.warning(f'Task with ID {task_id} not found for completion')
        return func.HttpResponse(
            "Task not found",
            status_code=404
        )
    
    # Update task status and completion time
    tasks[task_index]["status"] = "completed"
    tasks[task_index]["completed_at"] = datetime.now().isoformat()
    logging.info(f'Task marked as complete: "{tasks[task_index]["title"]}"')
    
    return func.HttpResponse(
        json.dumps(tasks[task_index]),
        mimetype="application/json"
    )

# Analytics: Task completion statistics
@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Task Completion Statistics function processed a request.')
    
    # Count tasks by status
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task["status"] == "completed")
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

# Analytics: Productivity metrics by time period
@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Productivity Metric function processed a request.')
    
    # Get optional date parameter (for future filtering)
    period = req.params.get('period', 'all')
    logging.info(f'Generating productivity metrics for period: {period}')
    
    # Calculate tasks created and completed
    tasks_created = len(tasks)
    tasks_completed = sum(1 for task in tasks if task["status"] == "completed")
    
    # Calculate average completion time (for completed tasks)
    completion_times = []
    for task in tasks:
        if task["status"] == "completed" and task["completed_at"]:
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