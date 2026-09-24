from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}
