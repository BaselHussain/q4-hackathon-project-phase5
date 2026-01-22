"""
Test script for POST /api/tasks endpoint (Phase 4 - User Story 2)
"""
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"
TEST_USER_ID = str(uuid4())

def test_create_task_with_description():
    """Test creating a task with title and description"""
    print("\n=== Test 1: Create task with title and description ===")

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        },
        json={
            "title": "Complete project documentation",
            "description": "Write comprehensive API documentation for all endpoints"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    assert data["title"] == "Complete project documentation"
    assert data["description"] == "Write comprehensive API documentation for all endpoints"
    assert data["status"] == "pending", f"Expected status='pending', got {data['status']}"
    assert data["user_id"] == TEST_USER_ID
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    print("✓ Test 1 passed!")
    return data["id"]


def test_create_task_without_description():
    """Test creating a task with only title (no description)"""
    print("\n=== Test 2: Create task without description ===")

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        },
        json={
            "title": "Review pull requests"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Review pull requests"
    assert data["description"] is None
    assert data["status"] == "pending"

    print("✓ Test 2 passed!")
    return data["id"]


def test_verify_tasks_in_list(task_ids):
    """Test that created tasks appear in GET /api/tasks"""
    print("\n=== Test 3: Verify tasks appear in GET /api/tasks ===")

    response = requests.get(
        f"{BASE_URL}/api/tasks",
        headers={"X-User-ID": TEST_USER_ID}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Number of tasks: {len(response.json())}")

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 2, f"Expected at least 2 tasks, got {len(tasks)}"

    task_ids_in_response = [task["id"] for task in tasks]
    for task_id in task_ids:
        assert task_id in task_ids_in_response, f"Task {task_id} not found in response"

    print("✓ Test 3 passed!")


def test_validation_empty_title():
    """Test validation error for empty title"""
    print("\n=== Test 4: Validation error - empty title ===")

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        },
        json={
            "title": "",
            "description": "This should fail"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    print("✓ Test 4 passed!")


def test_validation_title_too_long():
    """Test validation error for title exceeding 200 characters"""
    print("\n=== Test 5: Validation error - title too long ===")

    long_title = "A" * 201  # 201 characters

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        },
        json={
            "title": long_title,
            "description": "This should fail"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    print("✓ Test 5 passed!")


def test_validation_description_too_long():
    """Test validation error for description exceeding 2000 characters"""
    print("\n=== Test 6: Validation error - description too long ===")

    long_description = "A" * 2001  # 2001 characters

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        },
        json={
            "title": "Valid title",
            "description": long_description
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    print("✓ Test 6 passed!")


def test_missing_user_id_header():
    """Test error when X-User-ID header is missing"""
    print("\n=== Test 7: Error - missing X-User-ID header ===")

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={"Content-Type": "application/json"},
        json={
            "title": "This should fail",
            "description": "No user ID provided"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    data = response.json()
    assert data["detail"]["type"] == "invalid-user-id"

    print("✓ Test 7 passed!")


def test_user_auto_creation():
    """Test that user is automatically created on first task"""
    print("\n=== Test 8: User auto-creation ===")

    new_user_id = str(uuid4())

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={
            "Content-Type": "application/json",
            "X-User-ID": new_user_id
        },
        json={
            "title": "First task for new user",
            "description": "This should auto-create the user"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == new_user_id

    print("✓ Test 8 passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing POST /api/tasks endpoint (Phase 4 - User Story 2)")
    print("=" * 60)

    try:
        # Test creating tasks
        task_id_1 = test_create_task_with_description()
        task_id_2 = test_create_task_without_description()

        # Verify tasks appear in list
        test_verify_tasks_in_list([task_id_1, task_id_2])

        # Test validation errors
        test_validation_empty_title()
        test_validation_title_too_long()
        test_validation_description_too_long()

        # Test missing header
        test_missing_user_id_header()

        # Test user auto-creation
        test_user_auto_creation()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPhase 4 (User Story 2) - Create New Task is COMPLETE!")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server at http://localhost:8000")
        print("Make sure the FastAPI server is running.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
