import pytest
import httpx
from fastapi.testclient import TestClient

import firebase_admin
from firebase_admin import credentials, auth # type: ignore
from fastapi import FastAPI
from main import app  # Import your FastAPI app from your application
from datetime import datetime, timezone

client = TestClient(app)

##-----------------------------------------------------------Login test-----------------------------------------------------------##

def test_login():
    # Normally, you'd have the Firebase Authentication Token for a real user
    # For this test, we will assume you have a token from a successful Firebase Authentication

    # Simulating a valid Firebase ID token (You can replace this with a real Firebase ID token for testing)
    mock_token = "valid_firebase_token_here"

    # Simulate Firebase Token verification
    try:
        # Verify the Firebase token (check if it's valid)
        decoded_token = auth.verify_id_token(mock_token)
        uid = decoded_token["uid"]  # You would get the user ID after decoding the token

        # Now, check if the token is properly handled by your FastAPI route
        response = client.post("/login", json={"token": mock_token})

        # Assert the response status code and response data
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "success"

    except auth.InvalidIdTokenError:
        # Handle the case where the token is invalid
        pytest.fail("Firebase token is invalid or expired.")
    
##-----------------------------------------------------------Login test-----------------------------------------------------------##

##-----------------------------------------------------------Homepage test-----------------------------------------------------------##

# Test case for loading patients
def test_patients_load():
    response = client.get("/home-fetch")
    assert response.status_code == 200
    assert "patients" in response.json()  # Assuming MEWS data is included

# Test case for fetching report by patient ID
def test_get_report():
    patient_id = "example_patient_id"
    response = client.get(f"/home-fetch/report/{patient_id}")
    assert response.status_code == 200
    assert "patient_id" in response.json()
    assert "patient_info" in response.json()
    assert "mews_reports" in response.json()

# Test case for adding a patient
def test_add_patient():
    patient_data = {
        "age": "30",  # Age as a string
        "bed_number": "B12",  # Bed number as a string
        "created_at": datetime.now(timezone.utc).isoformat(), # Using timezone-aware datetime
        "fullname": "John Doe",  # Full name as a string
        "gender": "Male",  # Gender as a string
        "hospital_number": "HN123456",  # Hospital number as a string
        "patient_id": "P12345",  # Patient ID as a string
        "ward": "ICU",  # Ward as a string
    }

    response = client.post("/home-fetch/add_patient", json=patient_data)
    
    # Assert the response status code and success status
    assert response.status_code == 200
    assert response.json()["status"] == "success"

# Test case for getting patient data
def test_get_patient_data():
    patient_id = "example_patient_id"
    response = client.get(f"/home-fetch/get_patient/{patient_id}")
    assert response.status_code == 200
    assert "age" in response.json()
    assert "bed_number" in response.json()
    assert "created_at" in response.json()
    assert "fullname" in response.json()
    assert "gender" in response.json()
    assert "hospital_number" in response.json()
    assert "patient_id" in response.json()
    assert "ward" in response.json()

# Test case for saving patient data
def test_update_patient_data_case_01():
    patient_id = "example_patient_id"
    patient_data = {
        "age": "30",  # Age as a string
        "bed_number": "B12",  # Bed number as a string
        "fullname": "John Doe",  # Full name as a string
        "gender": "Male",  # Gender as a string
        "hospital_number": "HN123456",  # Hospital number as a string
        "patient_id": "P12345",  # Patient ID as a string
        "ward": "ICU",  # Ward as a string
    }
    response = client.put(f"/home-fetch/update_patient/{patient_id}", json=patient_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

# Test case for getting links by user
def test_get_links_by_user():
    uid = "example_user_id"
    response = client.get(f"/home-fetch/get-links-by-user/{uid}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "data" in response.json()  # Assuming MEWS data is included

# Test case for taking a patient in
def test_take_in():
    response = client.post(f"/home-fetch/take_in")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

# Test case for taking a patient out
def test_take_out():
    link_id = "example_link_id"
    response = client.post(f"/home-fetch/delete-link/{link_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

# Test case for getting inspection notes by MEWS ID
def test_get_note():
    patient_id = "example_patient_id"
    response = client.get(f"/home-fetch/get-note/{patient_id}")
    assert response.status_code == 200
    assert "data" in response.json()

##-----------------------------------------------------------Homepage test-----------------------------------------------------------##

##-----------------------------------------------------------Notification test-----------------------------------------------------------##

def test_load_take_in():
    uid = "test_uid" 
    response = client.get(f"/noti-fetch/{uid}")
    assert response.status_code == 200
    assert "load_in" in response.json()

def test_time_set():
    payload = {"time": "2025-02-10T12:00:00"}  # Example time payload
    response = client.post("/noti-fetch/set-time", json=payload)
    assert response.status_code == 200
    assert response.json().get("message") == "Time set successfully"


def test_add_mews():
    payload = {
        "patient_id": "test_patient_id",
        "uid": "test_uid",
        "mews": {
            "consciousness": 0,
            "heart_rate": "10",
            "temperature": "20",
            "blood_pressure": "30/50",
            "spo2": "40",
            "respiratory_rate": "50",
            "urine": "60",
        }  
    }
    
    response = client.post("/noti-fetch/add-mews", json=payload)
    assert response.status_code == 200
    assert response.json().get("message") == "MEWS added successfully"

def test_add_notes():
    payload = {
        "uid": "test_uid",
        "mews_id": "test_mews_id",
        "note": "Test_note"
    }
    response = client.post("/noti-fetch/add-note", json=payload)
    assert response.status_code == 200
    assert response.json().get("message") == "Note added successfully"
    
##-----------------------------------------------------------Notification test-----------------------------------------------------------##

##-----------------------------------------------------------Export test-----------------------------------------------------------##

def test_patients_load():
    response = client.get("/expt-fetch")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Ensure response is a list of patients
    assert len(response.json()) > 0  # Check that at least one patient is loaded

def test_filter():
    payload = {
        "fullname": "test_name",
        "gender": "male",
        "hospital_number" : "test_hn",
        "bed_number" : "test_bed_number",
        "ward" : "test_ward",
        "age" : "10"
    }
    response = client.post("/expt-fetch/filter", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Ensure response is a list of filtered patients

def test_get_report_exel():
    response = client.get("/expt-fetch/get-excel")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Content-Disposition" in response.headers  # Ensure it is an attachment for download

##-----------------------------------------------------------Export test-----------------------------------------------------------##

##-----------------------------------------------------------Setting test-----------------------------------------------------------##

def test_account_load():
    response = client.get("/sett-fetch/account-load")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)  # Ensure response is a dictionary
    assert "user_data" in response.json()  # Verify the response contains account data

def test_users_load():
    uid = "test_admin_uid"  # Replace with an actual test admin UID
    response = client.get(f"/sett-fetch/users-load/{uid}")
    response_json = response.json()

    assert response.status_code == 200
    assert isinstance(response_json, list)  # Ensure response is a list of users
    assert len(response_json) > 0  # Check that at least one user is loaded
    
    # Verify if the user is an admin
    assert response_json.get("is_admin") is True, "Requester is not an admin"

def test_add_user():
    uid = "test_uid"
    payload = {
        "nurse_id": "test_nurse_id",
        "name": "John",
        "lastname": "doe",
        "role": "admin", 
    }
    response = client.post(f"/sett-fetch/add-user/{uid}", json=payload)
    assert response.status_code == 200
    assert response.json().get("message") == "User created successfully"

def test_get_user_data():
    uid = "test_uid"
    response = client.get(f"/sett-fetch/user-data/{uid}")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)  # Ensure response is a dictionary
    assert response.json().get("uid") == uid  # Verify the correct user is returned
    assert "user_data" in response.json()  # Assuming MEWS data is included
    assert response.json().get("is_admin") is True, "Requester is not an admin"

def test_update_user():
    uid = "test_uid"
    payload = {
        "nurse_id": "test_nurse_id",
        "name": "John1",
        "lastname": "doe1",
        "role": "admin", 
    }
    response = client.put(f"/sett-fetch/save-user/{uid}", json=payload)
    assert response.status_code == 200
    assert response.json().get("message") == "User data updated successfully"

def test_del_user():
    admin_id="test_admin_id"
    uid = "test_uid"
    response = client.delete(f"/sett-fetch/delete-user/{uid}/{admin_id}")
    assert response.status_code == 200
    assert response.json().get("message") == "User deleted successfully"

def test_log_out():
    payload = {"uid": "test_uid"}
    response = client.post("/sett-fetch/logout", json=payload)
    assert response.status_code == 200
    assert response.json().get("message") == "User logged out successfully"

##-----------------------------------------------------------Setting test-----------------------------------------------------------##