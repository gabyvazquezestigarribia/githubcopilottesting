from fastapi.testclient import TestClient
import copy
import pytest

from src.app import app, activities

# keep a copy of the original activities so we can reset between tests
original_activities = copy.deepcopy(activities)

@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: restore global state before every test
    activities.clear()
    activities.update(copy.deepcopy(original_activities))

# client is reused across tests
client = TestClient(app)


def test_root_redirect():
    # Arrange: none (client already available)
    # Act (disable auto-following so we can inspect the redirect itself)
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # Arrange
    expected = copy.deepcopy(original_activities)
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_for_activity_success():
    # Arrange
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities[activity]["participants"]


def test_signup_for_activity_already_signed_up():
    # Arrange
    email = original_activities["Chess Club"]["participants"][0]
    activity = "Chess Club"
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_for_invalid_activity():
    # Arrange
    email = "someone@mergington.edu"
    activity = "Nonexistent Club"
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_success():
    # Arrange
    activity = "Programming Class"
    email = original_activities[activity]["participants"][0]
    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in activities[activity]["participants"]


def test_unregister_not_signed_up():
    # Arrange
    activity = "Programming Class"
    email = "ghost@mergington.edu"
    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up"


def test_unregister_invalid_activity():
    # Arrange
    activity = "Fake Club"
    email = "someone@mergington.edu"
    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
