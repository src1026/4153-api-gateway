from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

async def auth_header_check(request: Request, call_next):
    if request.url.path in ["/", "/docs", "/openapi.json", "/favicon.ico"]:
        return await call_next(request)

    if "Authorization" not in request.headers:
        return JSONResponse(
            {"error": "Authorization header missing"}, status_code=401
        )

    return await call_next(request)
