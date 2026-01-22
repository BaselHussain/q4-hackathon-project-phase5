"""
Comprehensive API endpoint testing script.

Tests all endpoints of the Task Management API to verify functionality.
"""
import requests
import json
from uuid import uuid4

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USER_ID = str(uuid4())  # Generate a unique test user ID

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(test_name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {test_name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(message):
    print(f"{GREEN}[PASS] {message}{RESET}")

def print_error(message):
    print(f"{RED}[FAIL] {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}[INFO] {message}{RESET}")

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# Test 1: Health Check
print_test("1. Health Check Endpoint")
try:
    response = requests.get(f"{BASE_URL}/health")
    print_response(response)
    if response.status_code == 200:
        print_success("Health check passed")
    else:
        print_error(f"Health check failed with status {response.status_code}")
except Exception as e:
    print_error(f"Health check failed: {str(e)}")

# Test 2: Create Task (POST /api/tasks)
print_test("2. Create New Task")
task_data = {
    "title": "Test Task 1",
    "description": "This is a test task created by the API test script"
}
headers = {"X-User-ID": TEST_USER_ID}

try:
    response = requests.post(f"{BASE_URL}/api/tasks", json=task_data, headers=headers)
    print_response(response)
    if response.status_code == 201:
        task_id = response.json()["id"]
        print_success(f"Task created successfully with ID: {task_id}")
    else:
        print_error(f"Task creation failed with status {response.status_code}")
        task_id = None
except Exception as e:
    print_error(f"Task creation failed: {str(e)}")
    task_id = None

# Test 3: List Tasks (GET /api/tasks)
print_test("3. List All Tasks")
try:
    response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
    print_response(response)
    if response.status_code == 200:
        tasks = response.json()
        print_success(f"Retrieved {len(tasks)} task(s)")
    else:
        print_error(f"List tasks failed with status {response.status_code}")
except Exception as e:
    print_error(f"List tasks failed: {str(e)}")

# Test 4: Get Single Task (GET /api/tasks/{task_id})
if task_id:
    print_test("4. Get Single Task by ID")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks/{task_id}", headers=headers)
        print_response(response)
        if response.status_code == 200:
            print_success("Retrieved task successfully")
        else:
            print_error(f"Get task failed with status {response.status_code}")
    except Exception as e:
        print_error(f"Get task failed: {str(e)}")

# Test 5: Update Task (PUT /api/tasks/{task_id})
if task_id:
    print_test("5. Update Task Details")
    update_data = {
        "title": "Updated Test Task",
        "description": "This task has been updated"
    }
    try:
        response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data, headers=headers)
        print_response(response)
        if response.status_code == 200:
            print_success("Task updated successfully")
        else:
            print_error(f"Update task failed with status {response.status_code}")
    except Exception as e:
        print_error(f"Update task failed: {str(e)}")

# Test 6: Toggle Task Completion (PATCH /api/tasks/{task_id}/complete)
if task_id:
    print_test("6. Toggle Task Completion Status")
    try:
        response = requests.patch(f"{BASE_URL}/api/tasks/{task_id}/complete", headers=headers)
        print_response(response)
        if response.status_code == 200:
            status = response.json()["status"]
            print_success(f"Task status toggled to: {status}")
        else:
            print_error(f"Toggle completion failed with status {response.status_code}")
    except Exception as e:
        print_error(f"Toggle completion failed: {str(e)}")

# Test 7: Toggle Back to Pending
if task_id:
    print_test("7. Toggle Task Back to Pending")
    try:
        response = requests.patch(f"{BASE_URL}/api/tasks/{task_id}/complete", headers=headers)
        print_response(response)
        if response.status_code == 200:
            status = response.json()["status"]
            print_success(f"Task status toggled to: {status}")
        else:
            print_error(f"Toggle completion failed with status {response.status_code}")
    except Exception as e:
        print_error(f"Toggle completion failed: {str(e)}")

# Test 8: Create Another Task
print_test("8. Create Second Task")
task_data_2 = {
    "title": "Test Task 2",
    "description": "Second test task"
}
try:
    response = requests.post(f"{BASE_URL}/api/tasks", json=task_data_2, headers=headers)
    print_response(response)
    if response.status_code == 201:
        task_id_2 = response.json()["id"]
        print_success(f"Second task created with ID: {task_id_2}")
    else:
        print_error(f"Second task creation failed with status {response.status_code}")
        task_id_2 = None
except Exception as e:
    print_error(f"Second task creation failed: {str(e)}")
    task_id_2 = None

# Test 9: List Tasks Again (should show 2 tasks)
print_test("9. List All Tasks (Should Show 2 Tasks)")
try:
    response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
    print_response(response)
    if response.status_code == 200:
        tasks = response.json()
        print_success(f"Retrieved {len(tasks)} task(s)")
        if len(tasks) == 2:
            print_success("Correct number of tasks returned")
        else:
            print_error(f"Expected 2 tasks, got {len(tasks)}")
    else:
        print_error(f"List tasks failed with status {response.status_code}")
except Exception as e:
    print_error(f"List tasks failed: {str(e)}")

# Test 10: Delete First Task (DELETE /api/tasks/{task_id})
if task_id:
    print_test("10. Delete First Task")
    try:
        response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 204:
            print_success("Task deleted successfully")
        else:
            print_error(f"Delete task failed with status {response.status_code}")
    except Exception as e:
        print_error(f"Delete task failed: {str(e)}")

# Test 11: List Tasks After Deletion (should show 1 task)
print_test("11. List Tasks After Deletion (Should Show 1 Task)")
try:
    response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
    print_response(response)
    if response.status_code == 200:
        tasks = response.json()
        print_success(f"Retrieved {len(tasks)} task(s)")
        if len(tasks) == 1:
            print_success("Correct number of tasks after deletion")
        else:
            print_error(f"Expected 1 task, got {len(tasks)}")
    else:
        print_error(f"List tasks failed with status {response.status_code}")
except Exception as e:
    print_error(f"List tasks failed: {str(e)}")

# Test 12: Test Error Handling - Missing X-User-ID Header
print_test("12. Error Handling - Missing X-User-ID Header")
try:
    response = requests.get(f"{BASE_URL}/api/tasks")  # No headers
    print_response(response)
    if response.status_code == 400:
        print_success("Correctly returned 400 for missing header")
    else:
        print_error(f"Expected 400, got {response.status_code}")
except Exception as e:
    print_error(f"Error handling test failed: {str(e)}")

# Test 13: Test Error Handling - Invalid UUID Format
print_test("13. Error Handling - Invalid UUID Format")
invalid_headers = {"X-User-ID": "not-a-uuid"}
try:
    response = requests.get(f"{BASE_URL}/api/tasks", headers=invalid_headers)
    print_response(response)
    if response.status_code == 400:
        print_success("Correctly returned 400 for invalid UUID")
    else:
        print_error(f"Expected 400, got {response.status_code}")
except Exception as e:
    print_error(f"Error handling test failed: {str(e)}")

# Test 14: Test Error Handling - Task Not Found
print_test("14. Error Handling - Task Not Found")
fake_task_id = str(uuid4())
try:
    response = requests.get(f"{BASE_URL}/api/tasks/{fake_task_id}", headers=headers)
    print_response(response)
    if response.status_code == 404:
        print_success("Correctly returned 404 for non-existent task")
    else:
        print_error(f"Expected 404, got {response.status_code}")
except Exception as e:
    print_error(f"Error handling test failed: {str(e)}")

# Summary
print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}TEST SUMMARY{RESET}")
print(f"{BLUE}{'='*60}{RESET}")
print_info(f"Test User ID: {TEST_USER_ID}")
print_success("All endpoint tests completed!")
print_info("Check the output above for any failures")
