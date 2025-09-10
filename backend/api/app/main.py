from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/api/healthz")
def healthz():
    return {"ok": True}


@app.middleware("http")
async def admin_only(request: Request, call_next):
    if request.url.path.startswith("/admin-api/"):
        if request.headers.get("x-admin") != "true":
            return JSONResponse(status_code=403, content={"detail": "admin only"})
    return await call_next(request)


@app.get("/admin-api/healthz")
def admin_health():
    return {"admin": True}
