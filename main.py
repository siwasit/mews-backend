from fastapi import FastAPI, HTTPException, Header, Depends
# from firebase_auth import verify_firebase_token  # Firebase authentication
# from firebase_db import db, add_data, get_data, get_all_data, update_data, delete_data
from firebase_db import get_firestore_db
from services import exportpage_service, homepage_service, notificationpage_service, settingpage_service, user_authentication_service
import uuid
from fastapi.responses import StreamingResponse
import json
import asyncio

app = FastAPI()

app.include_router(homepage_service.router, prefix="/home-fetch", tags=["home"])
app.include_router(user_authentication_service.router, prefix="/authenticate", tags=["authenticate"])
app.include_router(notificationpage_service.router, prefix="/noti-fetch", tags=["notification"])
app.include_router(exportpage_service.router, prefix="/expt-fetch", tags=["export"])
app.include_router(settingpage_service.router, prefix="/sett-fetch", tags=["setting"])

async def listen_to_patients():
    db = get_firestore_db()
    """ Listens for Firestore document changes in the 'patients' collection and yields updates as server-sent events """
    patients_collection = db.collection('patients')
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    def on_snapshot(col_snapshot, changes, read_time):
        """ Firestore callback function triggered on data change """
        for change in changes:
            if change.type.name == "ADDED":
                data = {"event": "added", "id": change.document.id, "data": change.document.to_dict()}
            elif change.type.name == "MODIFIED":
                data = {"event": "modified", "id": change.document.id, "data": change.document.to_dict()}
            elif change.type.name == "REMOVED":
                data = {"event": "removed", "id": change.document.id}
            else:
                continue
            
            # Convert dictionary to JSON and put it into the async queue
            loop.call_soon_threadsafe(queue.put_nowait, json.dumps(data))

    # Attach the listener
    query_watch = patients_collection.on_snapshot(on_snapshot)

    try:
        while True:
            event_data = await queue.get()
            yield f"data: {event_data}\n\n"
            await asyncio.sleep(0.1)  # Prevent CPU overload
    finally:
        query_watch.unsubscribe()

# 🔥 Firestore Listener for Real-Time Updates for Users
async def listen_to_users():
    db = get_firestore_db()
    """ Listens for Firestore document changes in the 'users' collection and yields updates as server-sent events """
    users_collection = db.collection('users')
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    def on_snapshot(col_snapshot, changes, read_time):
        """ Firestore callback function triggered on data change """
        for change in changes:
            if change.type.name == "ADDED":
                data = {"event": "added", "id": change.document.id, "data": change.document.to_dict()}
            elif change.type.name == "MODIFIED":
                data = {"event": "modified", "id": change.document.id, "data": change.document.to_dict()}
            elif change.type.name == "REMOVED":
                data = {"event": "removed", "id": change.document.id}
            else:
                continue
            
            # Convert dictionary to JSON and put it into the async queue
            loop.call_soon_threadsafe(queue.put_nowait, json.dumps(data))

    # Attach the listener
    query_watch = users_collection.on_snapshot(on_snapshot)

    try:
        while True:
            event_data = await queue.get()
            yield f"data: {event_data}\n\n"
            await asyncio.sleep(0.1)  # Prevent CPU overload
    finally:
        query_watch.unsubscribe()

@app.get("/stream_patients")
async def get_patient_stream():
    """SSE endpoint for real-time patient updates."""
    return StreamingResponse(listen_to_patients(), media_type="text/event-stream")

@app.get("/stream_users")
async def get_user_stream():
    """SSE endpoint for real-time user updates."""
    return StreamingResponse(listen_to_users(), media_type="text/event-stream")
