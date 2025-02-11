from fastapi import FastAPI, HTTPException, Depends
from firebase_db import get_firestore_db
from model import Users

app = FastAPI()

@app.get("/account/{uid}")
async def account_load(uid: str):
    """โหลดข้อมูลของผู้ใช้ตาม UID"""
    db = get_firestore_db()
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": user_doc.id, **user_doc.to_dict()}

@app.get("/users/{admin_id}")
async def users_load(admin_id: str):
    """โหลดข้อมูลผู้ใช้ และยืนยันว่า admin_id มีสิทธิ์เข้าถึง"""
    db = get_firestore_db()

    # ตรวจสอบว่า admin_id เป็น admin จริงหรือไม่
    admin_ref = db.collection("admins").document(admin_id).get()
    if not admin_ref.exists or admin_ref.to_dict().get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # โหลดข้อมูล user ทั้งหมดที่ได้รับการอนุมัติแล้ว
    users_ref = db.collection("users").where("status", "==", "approved").stream()
    users = [{"id": user.id, **user.to_dict()} for user in users_ref]

    if not users:
        raise HTTPException(status_code=404, detail="No approved users found")

    return {"data": users}

@app.post("/user")
async def add_user(user: Users):
    """เพิ่มข้อมูลผู้ใช้ใหม่"""
    db = get_firestore_db()
    users_ref = db.collection("users")

    new_user_ref = users_ref.add(user.to_dict())
    return {"message": "User added successfully", "user_id": new_user_ref[1].id}

@app.get("/user/{user_id}")
async def get_user_data(user_id: str):
    """ดึงข้อมูลผู้ใช้ตาม user_id"""
    db = get_firestore_db()
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": user_doc.id, **user_doc.to_dict()}

@app.put("/user/{user_id}")
async def save_user(user_id: str, user: Users):
    """อัปเดตข้อมูลของ user"""
    db = get_firestore_db()
    user_ref = db.collection("users").document(user_id)

    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_ref.update(user.dict())
    return {"message": "User updated successfully"}

@app.delete("/user/{user_id}")
async def del_user(user_id: str):
    """ลบข้อมูลผู้ใช้ตาม user_id"""
    db = get_firestore_db()
    user_ref = db.collection("users").document(user_id)

    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_ref.delete()
    return {"message": "User deleted successfully"}