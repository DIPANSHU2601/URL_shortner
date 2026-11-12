# High-Throughput URL Shortener

A production-grade, high-performance URL shortening service built with **FastAPI**, **PostgreSQL**, **Redis**, and **Docker**. Designed with low latency and scalability in mind.

## Architecture & Design Decisions

1. **Base62 Encoding vs. Random Hashes:**
   - Instead of generating random UUIDs or MD5 hashes (which cause collisions and heavy DB index fragmentation), we use PostgreSQL's auto-incrementing BigInteger ID offset by a fixed integer, encoded into a compact Base62 string (`a-z`, `A-Z`, `0-9`). This guarantees zero collisions and supports up to ~56 billion unique URLs.

2. **Cache-Aside Pattern (Redis):**
   - Read operations (`GET /{short_code}`) first check the Redis cache. On a cache hit, it returns the original URL instantly with a `307 Temporary Redirect`.
   - On a cache miss, it queries PostgreSQL, populates Redis with a TTL of 1 hour, and serves the response.

3. **Asynchronous Click Tracking:**
   - Click metrics are incremented asynchronously using FastAPI `BackgroundTasks` combined with atomic SQL updates (`UPDATE urls SET clicks = clicks + 1`), preventing race conditions and keeping redirect latency under 5ms.

4. **Distributed Rate Limiting:**
   - Implemented using Redis sliding/fixed window counters on the `/shorten` endpoint to prevent API abuse, scraping, and DDoS attacks.

## Tech Stack
- **Framework:** FastAPI (Python 3.11, Async)
- **Database:** PostgreSQL 15 (AsyncPG + SQLAlchemy ORM)
- **Caching & Rate Limiting:** Redis 7
- **Containerization:** Docker & Docker Compose

## Setup & Running Locally

1. Clone the repository:
   ```bash
   git clone [https://github.com/dipanshumoulekhi/url-shortener-fastapi.git](https://github.com/dipanshumoulekhi/url-shortener-fastapi.git)
   cd url-shortener-fastapi
