from fastapi import FastAPI
from app.api.v1 import auth

app = FastAPI(title="FastAPI SSO Service")

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "FastAPI SSO is running"}
