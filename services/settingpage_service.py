from fastapi import FastAPI, HTTPException, APIRouter
from firebase_db import get_firestore_db
from model import Users

app = FastAPI()
router = APIRouter()

@router.get("/account_load/{user_id}")
def account_load(user_id: str): # ✅ 
    db = get_firestore_db()
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="Users not found")
    
    return {"id": user_doc.id, **user_doc.to_dict()}

@router.get("/users_load/{admin_id}")
def users_load(admin_id: str): # ✅
    db = get_firestore_db()

    # ตรวจสอบสิทธิ์จาก role ใน collection users
    admin_ref = db.collection("users").document(admin_id).get()
    admin_data = admin_ref.to_dict()

    if not admin_data or admin_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # โหลดข้อมูล users ทั้งหมด
    users_ref = db.collection("users").stream()
    users_list = [{"id": user.id, **user.to_dict()} for user in users_ref if user.id != admin_id]

    if not users_list:
        raise HTTPException(status_code=404, detail="No users found")

    return {"data": users_list}

@router.post("/add_user")
async def add_user(user: Users): # ✅
    try:
        db = get_firestore_db()
        users_ref = db.collection("users")
        
        # ใช้ model_dump() แทน to_dict()
        user_data = user.model_dump()
        new_user_ref = users_ref.add(user_data)
        
        return {"message": "User added successfully", "user_id": new_user_ref[1].id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add user: {str(e)}")

@router.get("/get_user_data/{user_id}") 
async def get_user_data(user_id: str):  # ✅
    db = get_firestore_db()
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="Users not found")
    
    return {"id": user_doc.id, **user_doc.to_dict()}

@router.post("/save_user/{user_id}")
async def save_user(user_id: str, user: Users): # ✅
    db = get_firestore_db()
    user_ref = db.collection("users").document(user_id)
    
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    # ใช้ model_dump() แทน dict()
    user_ref.update(user.model_dump())
    return {"message": "User updated successfully"}

@router.delete("/del_user/{user_id}")
async def del_user(user_id: str): # ✅
    db = get_firestore_db()
    user_ref = db.collection("users").document(user_id)
    
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_ref.delete()
    return {"message": "User deleted successfully"}