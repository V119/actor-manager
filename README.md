# Glacier AI Actor

Glacier AI Actor is a comprehensive platform designed for managing AI actor personas and visual styles. It provides a full-stack solution for actors to upload their portraits, manage visual styles, handle legal protocols, and discover other AI actors in a global square.

## Tech Stack

- **Frontend**: [Vue 3](https://vuejs.org/) + [Vite](https://vitejs.dev/) + [Tailwind CSS](https://tailwindcss.com/)
- **Backend**: [Python 3.12](https://www.python.org/) + [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) + [Peewee ORM](http://docs.peewee-orm.com/) (with `peewee_async`)
- **Storage**: [MinIO](https://min.io/) (for image and video assets)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)

## Architecture

The backend follows **Domain-Driven Design (DDD)** principles, organized into four layers:

1.  **Domain**: Core business logic, entities, and repository interfaces.
2.  **Application**: Use cases and application-specific services.
3.  **Infrastructure**: Implementation of repositories, database models, and external service clients (MinIO).
4.  **Interface**: API routes, request/response schemas, and the main application entry point.

## Directory Structure

```
.
├── backend/
│   ├── domain/         # Domain entities and interfaces
│   ├── application/    # Application services
│   ├── infrastructure/ # DB models, repositories, and config
│   ├── interface/      # FastAPI routes and schemas
│   ├── tests/          # Unit and integration tests
│   ├── migrations/     # Alembic migration files
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── views/      # Core page components
    │   ├── router/     # Vue Router configuration
    │   └── App.vue     # Main application layout
    └── package.json
```

## Getting Started

### Backend Setup

1.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
2.  Configure environment variables (optional, defaults are provided in `backend/infrastructure/config.py`):
    - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
    - `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`
3.  Run migrations:
    ```bash
    # Run from the backend directory for alembic
    cd backend && alembic upgrade head && cd ..
    ```
4.  Start the API server (from project root to support absolute imports):
    ```bash
    PYTHONPATH=. uvicorn backend.interface.api.main:app --reload
    ```

### Frontend Setup

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```

## Testing

Run backend tests using `pytest`:
```bash
export PYTHONPATH=$PYTHONPATH:.
pytest backend/tests/
```
