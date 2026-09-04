# SIH26165: AI-Powered Safety Intelligence & Early Warning System

## Overview
This repository contains the project foundation for **SIH26165: AI-Powered Safety Intelligence & Early Warning System**.

This foundational layer provides:
- **Backend**: Modular Python FastAPI application with Pydantic v2 settings, standard exception handlers, and SQLAlchemy database session management.
- **Frontend**: Clean, minimalist React (Vite) application shell styled with Tailwind CSS, React Router, and a unified health monitor.
- **Database**: PostgreSQL configuration and initialization scripts with connection pooling and health checks.
- **Tests**: Automated Pytest suite verifying the health and diagnostic endpoints.

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/             # API routes & endpoint definitions
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py
│   │   │       └── api.py
│   │   ├── auth/            # Authentication & authorization logic (upcoming)
│   │   ├── core/            # Config, settings, and exception handlers
│   │   │   ├── config.py
│   │   │   └── exceptions.py
│   │   ├── database/        # Database session and connection utilities
│   │   │   └── session.py
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   │   └── health.py
│   │   ├── services/        # Business logic services
│   │   └── main.py          # FastAPI application entrypoint
│   ├── .env.example         # Environment template
│   ├── .env                 # Local environment config
│   ├── Dockerfile           # Backend container definition
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (Header, Sidebar)
│   │   ├── context/         # Application state & health context
│   │   ├── hooks/           # Custom React hooks (useHealthCheck)
│   │   ├── layouts/         # Layout shells (AppShell)
│   │   ├── pages/           # Page views (DashboardPlaceholder)
│   │   ├── services/        # API client & services (api.js)
│   │   ├── utils/           # Helper constants
│   │   ├── App.jsx          # Main application & routing
│   │   ├── index.css        # Tailwind styling & base styles
│   │   └── main.jsx         # React root mounting
│   ├── .env.example         # Frontend environment template
│   ├── .env                 # Frontend environment config
│   ├── Dockerfile           # Frontend container definition
│   ├── package.json         # Node dependencies
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   └── vite.config.js       # Vite configuration with API proxy
├── database/
│   └── init.sql             # PostgreSQL initialization scripts
├── tests/
│   ├── conftest.py          # Pytest fixtures and TestClient
│   └── test_health.py       # Health endpoint test suite
├── docker-compose.yml       # Multi-container local deployment
└── README.md
```

---

## Getting Started

### Prerequisites
- **Python** 3.10+
- **Node.js** 18+ and **npm**
- **PostgreSQL** 14+ (or Docker)

---

### Backend Setup (Local)

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env` (preconfigured for local development).
   ```bash
   cp .env.example .env
   ```

5. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

### Frontend Setup (Local)

1. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env`.
   ```bash
   cp .env.example .env
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - **Frontend UI**: [http://localhost:5173](http://localhost:5173)

---

### Running with Docker Compose

To start PostgreSQL, the FastAPI backend, and the React frontend simultaneously:

```bash
docker-compose up --build
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## Running Tests

Execute the automated backend test suite:

```bash
pytest -v tests/
```

Test coverage includes:
- `GET /api/health` status response verification (`{"status": "ok"}`)
- `GET /api/v1/health` and `GET /api/v1/health/details` diagnostic checks
- Global error handler formatting (404 / 422 / 500)
