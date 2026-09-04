# Production Deployment

This project deploys as two separate Vercel projects from the same GitHub repository: a React/Vite frontend rooted at `frontend/` and a FastAPI backend rooted at `backend/`, plus a managed PostgreSQL database. The existing routes, UI, API endpoints, authentication, imports, and exports are unchanged.

## 1. GitHub Setup

1. Push the repository to GitHub without committing `.env` files, database files, `node_modules`, or `dist`.
2. Confirm the repository contains `backend/.env.example` and `frontend/.env.example`, but not real credentials.
3. Use the repository root as the source repository for both Vercel projects.

## 2. PostgreSQL Setup

Create a PostgreSQL database using a managed provider. Copy the connection string that is reachable from Vercel.

Configure either:

- `DATABASE_URL=postgresql://username:password/host/database` (recommended), or
- all `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` variables.

The backend normalizes `postgres://` and `postgresql://` URLs for SQLAlchemy. Fresh PostgreSQL databases receive the SQLAlchemy model schema at backend startup. The root `database/init.sql` only enables PostgreSQL extensions and is optional for managed providers.

## 3. Vercel Backend Setup

Create a Vercel project for the backend with:

- Repository: your GitHub repository
- Root directory: `backend`
- Framework preset: Other
- Build command: leave the Vercel default unless Vercel requires a custom build command
- Output directory: leave empty

Vercel detects `backend/api/index.py` as the Python serverless entry point. That file imports the existing `app.main:app`; it does not duplicate the FastAPI application or change its routes. Do not use a root-level multi-service `vercel.json`.

## 4. Required Vercel Backend Environment Variables

Set these in the backend Vercel project, not in source control:

```text
ENVIRONMENT=production
DEBUG=False
JWT_SECRET_KEY=<unique random secret of at least 32 characters>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=<managed PostgreSQL connection string>
USE_SQLITE_DEV_FALLBACK=False
SEED_DEMO_DATA=False
BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app
FRONTEND_URL=https://your-frontend.vercel.app
```

Optional variables include `PROJECT_NAME`, `VERSION`, `API_V1_STR`, `MAX_UPLOAD_SIZE_MB`, `ALLOWED_IMPORT_EXTENSIONS`, `ENABLE_OCR`, and `TESSERACT_CMD`. Do not place database credentials or JWT secrets in frontend variables.

After deployment, verify:

- `https://<backend-project>.vercel.app/health`
- `https://<backend-project>.vercel.app/api/health`
- `https://<backend-project>.vercel.app/docs`

The detailed health endpoint reports PostgreSQL connectivity at `/api/v1/health/details`.

## 5. Vercel Frontend Setup

Create a second Vercel project from the same GitHub repository with:

- Root directory: `frontend`
- Framework preset: Vite
- Build command: `npm run build`
- Publish directory: `dist`

Set these frontend Vercel environment variables:

```text
VITE_API_BASE_URL=https://<backend-project>.vercel.app
VITE_APP_TITLE=Safety Intelligence & Early Warning System
```

Do not add `/api` to this value. The frontend appends the API paths itself. `VITE_APP_TITLE` is optional.

The file `frontend/vercel.json` contains the SPA rewrite required for React Router. `frontend/public/_redirects` remains for hosts that support Netlify-style redirects, but Vercel uses `frontend/vercel.json`.

This keeps direct refreshes of React Router paths such as `/reports`, `/analytics`, and `/bulk-import` working on Vercel.

## 6. CORS Configuration

Set `BACKEND_CORS_ORIGINS` to the exact frontend Vercel origin, including `https://` and excluding a trailing slash. Comma-separated origins are supported:

```text
BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app
```

For local development, use `http://localhost:5173` (and optionally `http://127.0.0.1:5173`). Production does not add localhost origins automatically and never enables `*`.

If a custom frontend domain is used, update both `BACKEND_CORS_ORIGINS` and `FRONTEND_URL` in the backend Vercel project.

## 7. Local Development

Backend:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Local frontend requests use `VITE_API_BASE_URL=http://localhost:8000`. The local `.env.example` permits the SQLite development fallback when PostgreSQL is unavailable; production must use PostgreSQL and set `USE_SQLITE_DEV_FALLBACK=False`.

## 8. File Uploads and Exports

Bulk imports are read and parsed from the request body. CSV, Excel, and PDF uploads are not stored as permanent files. Export endpoints generate CSV, Excel, and PDF response bytes on demand. This avoids relying on Render’s ephemeral filesystem. PostgreSQL stores the import metadata and imported records.

The current import progress processing uses an in-process background thread. For a single Vercel function instance it works as currently implemented, but work can be interrupted when the function is recycled or scaled out. A durable job queue would be a future reliability improvement and is not required for this deployment configuration.

## 9. Testing Before Release

From the repository root:

```powershell
cd frontend
npm run build
cd ..
pytest -v tests/
```

To verify the backend runtime locally:

```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then request `/health` and stop the server with `Ctrl+C`.

For a deployed smoke test, open the frontend Vercel URL, log in, refresh a nested route, submit a report, open the admin import page, upload a supported file, and download an export. Browser developer tools should show requests going to the backend Vercel URL rather than localhost.

## 10. Common Deployment Errors

### CORS error in the browser

Use the exact frontend Vercel origin in the backend Vercel project's `BACKEND_CORS_ORIGINS`. Remove a trailing slash and redeploy the backend after changing environment variables.

### React route returns 404 after refresh

Confirm the Vercel frontend root directory is `frontend`, the framework is Vite, the build output is `dist`, and `frontend/vercel.json` is present.

### Backend fails while importing settings

Set a production JWT secret with at least 32 characters, provide `DATABASE_URL` or PostgreSQL connection variables, and set `USE_SQLITE_DEV_FALLBACK=False`.

### Database connection failure

Use the managed provider's Vercel-reachable connection string, check that the database accepts Vercel connections, and confirm the URL includes the correct username, password, host, port, and database name.

### Frontend still calls localhost

Set the frontend Vercel project's `VITE_API_BASE_URL`, trigger a new frontend build, and check the generated browser requests. Vite variables are embedded at build time, so changing the variable requires a rebuild.

### Upload or export fails

Check Vercel function logs and request size limits. The backend default upload limit is 25 MB; set `MAX_UPLOAD_SIZE_MB` if the deployment needs a different limit. Generated exports are response downloads and do not persist on disk.
