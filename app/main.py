from fastapi import FastAPI, Request, HTTPException, APIRouter, Depends
import httpx  # For forwarding requests to microservices
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

USER_SERVICE_URL = "http://localhost:8001"
RECIPE_SERVICE_URL = "http://localhost:8002"
router = APIRouter()

async def auth_header_check(request: Request, call_next):
    """
    Middleware to check and validate the Authorization header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return await call_next(request)

@router.get("/users")
@limiter.limit("10/minute")
async def get_users(request: Request):
    """
    Fetch all users from the User Service.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USER_SERVICE_URL}/users")
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"User Service is unreachable: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)

@router.post("/recipes")
@limiter.limit("10/minute")
async def create_recipe(request: Request):
    """
    Forward recipe creation request to the Recipe Service.
    """
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{RECIPE_SERVICE_URL}/recipes", json=body)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Recipe Service is unreachable: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
@router.get("/users/{user_id}")
@limiter.limit("5/minute")
async def get_user(user_id: int, request: Request):
    """
    Fetch user details from the User Service by user_id.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/users/{user_id}",
                headers=request.headers  # Forward headers, including Authorization
            )
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"User Service unreachable: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)

# Include the router
app.include_router(router)
@router.post("/users/register")
@limiter.limit("5/minute")
async def register_user(request: Request):  # Add `request` argument
    """
    Forward user registration request to the User Service.
    """
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{USER_SERVICE_URL}/register", json=body)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"User Service is unreachable: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)

# Add health check route
@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Simple health check endpoint for API Gateway.
    """
    return {"status": "ok"}

app.include_router(router)
