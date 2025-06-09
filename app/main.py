from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.redis_client import init_redis_pool, redis

app = FastAPI(title="Scientific Poster ML Service")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(router, prefix="/api/ml", tags=["ml"])

@app.on_event("startup")
async def on_startup():
    # Инициализируем пул подключений к Redis
    await init_redis_pool()

@app.on_event("shutdown")
async def on_shutdown():
    # Закрываем соединение при остановке
    if redis:
        await redis.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Scientific Poster ML Service"}
