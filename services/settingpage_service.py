from fastapi import FastAPI, HTTPException, APIRouter
from firebase_db import get_firestore_db
from model import Users

app = FastAPI()
router = APIRouter()

@app.get("/load_account/{uid}")
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
    
    # ตรวจสอบสิทธิ์จาก role ใน collection users แทน
    admin_ref = db.collection("users").document(admin_id).get()
    if not admin_ref.exists or admin_ref.to_dict().get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # โหลดข้อมูล users ทั้งหมด
    users_ref = db.collection("users").stream()
    users = [{"id": user.id, **user.to_dict()} for user in users_ref]
    
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    
    return {"data": users}

@app.post("/user")
async def add_user(user: Users):
    """เพิ่มข้อมูลผู้ใช้ใหม่"""
    try:
        db = get_firestore_db()
        users_ref = db.collection("users")
        
        # ใช้ model_dump() แทน to_dict()
        user_data = user.model_dump()
        new_user_ref = users_ref.add(user_data)
        
        return {"message": "User added successfully", "user_id": new_user_ref[1].id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add user: {str(e)}")

@app.get("/user/{user_id}")
async def get_user_data(user_id: str):  # ลบ async เพราะไม่จำเป็น
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
    
    # ใช้ model_dump() แทน dict()
    user_ref.update(user.model_dump())
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