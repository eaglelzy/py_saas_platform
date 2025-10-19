from fastapi import APIRouter


router = APIRouter()

@router.get("/users/test")
def users_api():
    return {"message": "Users router is working!"}