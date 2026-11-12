# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import engine, Base, get_db, AsyncSessionLocal
from app.models import URLItem
from app.schemas import URLCreate, URLResponse
from app.utils import encode_base62
from app.redis_client import get_cached_url, set_cached_url, rate_limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="High-Throughput URL Shortener", lifespan=lifespan)

async def increment_click_count(short_code: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(URLItem)
            .where(URLItem.short_code == short_code)
            .values(clicks=URLItem.clicks + 1)
        )
        await session.commit()

@app.post("/shorten", response_model=URLResponse, dependencies=[Depends(rate_limiter)])
async def create_short_url(payload: URLCreate, request: Request, db: AsyncSession = Depends(get_db)):
    new_url = URLItem(original_url=str(payload.url))
    db.add(new_url)
    await db.flush()  # DB generates auto-increment ID without full commit

    # Offset by 100000 so short_code starts with a clean multi-char string
    short_code = encode_base62(new_url.id + 100000)
    new_url.short_code = short_code
    await db.commit()

    await set_cached_url(short_code, new_url.original_url)
    base_url = str(request.base_url).rstrip("/")
    return URLResponse(
        short_code=short_code,
        short_url=f"{base_url}/{short_code}",
        original_url=new_url.original_url
    )

@app.get("/{short_code}")
async def redirect_to_original(
    short_code: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # 1. Check Redis Cache first
    cached_url = await get_cached_url(short_code)
    if cached_url:
        background_tasks.add_task(increment_click_count, short_code)
        return RedirectResponse(url=cached_url, status_code=307)

    # 2. Cache Miss -> Query PostgreSQL
    result = await db.execute(select(URLItem).where(URLItem.short_code == short_code))
    url_item = result.scalar_one_or_none()
    if not url_item:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # 3. Populate Cache & Increment clicks asynchronously
    await set_cached_url(short_code, url_item.original_url)
    background_tasks.add_task(increment_click_count, short_code)
    return RedirectResponse(url=url_item.original_url, status_code=307)

@app.get("/stats/{short_code}")
async def get_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(URLItem).where(URLItem.short_code == short_code))
    url_item = result.scalar_one_or_none()
    if not url_item:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return {
        "short_code": url_item.short_code,
        "original_url": url_item.original_url,
        "clicks": url_item.clicks,
        "created_at": url_item.created_at
    }
