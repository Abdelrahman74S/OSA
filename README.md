# 🚀 Online Auction System

A scalable and high-performance online auction platform built with **Django**, designed to handle real-time bidding, high concurrency, and optimized database operations.

---

## 🛠️ Technologies Used

| Layer | Technology |
|---|---|
| **Backend** | Python, Django, Django REST Framework (DRF) |
| **Async Tasks** | Celery + Redis (broker & result backend) |
| **Real-Time** | Django Channels & Daphne (WebSockets) |
| **Authentication** | JWT via `djangorestframework-simplejwt` |
| **Caching & Infra** | Redis, Docker, Docker Compose |
| **API Docs** | Swagger / OpenAPI via `drf-spectacular` |

---

## ⚙️ Core Features

### 🔒 Transactional Bidding Engine
- Secure bidding system using row-level locking (`select_for_update`)
- Prevents race conditions in high-concurrency environments
- Ensures financial data consistency and integrity

### ⏱️ Automated Auction Lifecycle
- Background jobs powered by **Celery Beat**
- Automatically detects expired auctions, closes listings, and assigns winners
- No manual intervention required

### ⚡ Advanced Query Optimization
- Eliminated N+1 query problems
- Optimized database performance using `select_related`, `prefetch_related`, `Subquery`, and `OuterRef`
- Ensures fast and scalable API responses

### 🧩 Dynamic Auction Management
- Sellers can create and manage listings with:
  - Starting price & reserve price
  - Bid increments
  - Hierarchical category organization

### 🖼️ Robust Media Handling
- Multiple images per listing
- Automatic primary image designation and organization

### ⭐ Watchlist & User Engagement
- Personalized watchlist for tracking auctions of interest
- Filterable and sortable tracked items

---

## 🧠 Key Highlights

- Built for **scalability and performance** from the ground up
- **Real-time updates** via WebSockets
- Designed for **high-concurrency** environments
- Clean, maintainable architecture following Django best practices

---

## 📦 Setup & Run

> Make sure you have **Docker** and **Docker Compose** installed.

```bash
git clone <repo-url>
cd project

docker-compose up --build
```

---

## 📄 API Documentation

Interactive Swagger UI is available at:

```
http://localhost:8000/api/schema/swagger-ui/
```
