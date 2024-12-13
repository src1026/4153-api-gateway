from fastapi import APIRouter, Request
from slowapi.util import get_remote_address
from slowapi import Limiter

router = APIRouter()
limiter = Limiter(key_func=lambda request: request.client.host)
RECIPE_SERVICE_URL = "http://localhost:8001"
USER_SERVICE_URL = "http://localhost:8002"

@router.get("/recipes")
@limiter.limit("5/minute")
async def get_recipes(request: Request):
    return {"message": "Here are your recipes"}

@router.get("/users")
@limiter.limit("10/minute")
async def get_users(request: Request):
    return {"message": "Here are your users!"}
