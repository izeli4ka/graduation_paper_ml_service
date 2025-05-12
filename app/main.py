import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="Scientific Poster ML Service")

# Настройка CORS
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8080,http://localhost:8000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(router, prefix="/api/ml", tags=["ml"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Scientific Poster ML Service"}
