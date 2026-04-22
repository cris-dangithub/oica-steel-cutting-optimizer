# AGENTS.md

## Project

OICA (Optimizador Inteligente de Cortes de Acero) - Python/Flask backend that uses genetic algorithms to solve the 1D cutting stock problem for steel bars. Part of a Docker Compose stack with PostgreSQL, Redis, Celery, and a Next.js frontend.

## Architecture

- **`server.py`** - Production entrypoint. Flask + Socket.IO (gevent) server with async processing via Celery. This is what Docker runs.
- **`main.py`** - Legacy/standalone entrypoint. Synchronous Flask server with the GA running inline. Contains its own `/upload` endpoint, AG profile configs (`CONFIGURACIONES_AG`), and a PDF generator. Still functional but not used in Docker.
- **`celery_worker.py`** - Celery task definition. Reads Excel uploads, validates, runs the GA, generates artifacts (Excel/PDF/PNG), saves results to PostgreSQL. Progress reported via Redis Pub/Sub.
- **`genetic_algorithm/`** - Core GA package: `engine.py` (orchestrator), `chromosome.py`, `fitness.py`, `population.py`, `selection.py`, `crossover.py`, `mutation.py`, `input_adapter.py`, `output_formatter.py`, `metrics.py`, `optimal_analyzer.py`, `chromosome_utils.py`.
- **`models/`** - SQLAlchemy models: `UploadedFile` (1:N) `ProcessingResult`. PostgreSQL backend.
- **`utils/artifact_generator.py`** - Generates Excel, PDF (WeasyPrint), and PNG (matplotlib) output files.
- **`barras_estandar.json`** - Standard bar lengths config (6m, 9m, 12m per diameter).

## Running

The app runs via Docker Compose from the parent repo (`oica-docker-compose/`):

```bash
# From oica-docker-compose/
docker compose up --build
```

Services: `db` (PostgreSQL:15), `redis` (Redis:7), `backend` (Flask on :5000), `celery_worker`, `frontend` (Next.js on :80).

Backend source is volume-mounted at `/usr/src/app` inside containers.

### Running standalone (without Docker)

Requires PostgreSQL and Redis running locally. Environment variables:
- `DATABASE_URL` (default: `postgresql://oica_user:oica_password@db:5432/oica_db`)
- `REDIS_URL` (default: `redis://localhost:6379/0`)
- `UPLOAD_PATH` (default: `/usr/src/app/data/filestore`)

```bash
pip install -r requirements.txt
python server.py          # production server
python main.py            # legacy standalone (no Celery needed)
```

## Tests

Tests use `unittest` (no pytest). Run from the backend directory:

```bash
python -m unittest discover tests/          # all tests
python -m unittest tests.test_engine        # single module
python -m unittest tests.test_fitness
python -m unittest tests.test_operators
python -m unittest tests.test_integration
```

There is also a root-level `test_optimal_analysis.py` (run with `python -m unittest test_optimal_analysis`).

Tests only cover the `genetic_algorithm/` package. No tests for Flask endpoints, Celery tasks, or artifact generation. Tests do NOT require database or Redis.

## Key conventions

- **Language**: Codebase, comments, variable names, and configs are in Spanish. Use Spanish for new code to stay consistent.
- **GA config profiles**: Three profiles (`rapido`, `balanceado`, `profundo`/`intensivo`) control population size and generations. `main.py` calls it `intensivo`, `celery_worker.py` calls it `profundo` - be aware of this inconsistency.
- **`LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`**: Defined in two places with different values - `0.0` in `main.py`, `0.5` in `genetic_algorithm/__init__.py`. The GA package uses `0.5`.
- **Two upload flows exist**: `server.py` (async via Celery) and `main.py` (sync inline). They transform input data differently - `server.py` flattens all bar types into one list; `main.py` processes per `numero_barra` and `grupo_ejecucion` hierarchically.
- **Input format**: Excel files with columns: `N° Orden`, `Elemento`, `N° de Barra`, `Longitud total (m)`, `Cantidad`, `Masa total (kg)`.
- **GA internal data format**: `barras_disponibles` is a list of dicts `{'longitud': float, 'tipo': 'estandar'|'desperdicio'}`. Use `input_adapter.longitudes_a_barras_dict()` or `adaptar_entrada_completa()` to convert.
- **Chromosomes**: A `Cromosoma` has a list of `Patron` objects. Each `Patron` represents one bar being cut into pieces.

## Gotchas

- **WeasyPrint** requires system-level C libraries (cairo, pango, gdk-pixbuf). These are installed in the Alpine Dockerfiles. Running locally on a machine without these will crash artifact generation.
- **matplotlib backend** must be `Agg` (non-interactive). Already set in `main.py` but not in `celery_worker.py` - matplotlib may fail in headless environments if not set.
- **Pipfile** is out of sync with `requirements.txt` - it lacks `psycopg2-binary`, `SQLAlchemy`, `Flask-SQLAlchemy`, `celery`, `redis`, `flask-socketio`, `python-socketio`, `gevent`, `gevent-websocket`. Use `requirements.txt` as the source of truth.
- **No linter, formatter, or type checker** is configured. No CI pipeline exists.
- **`data/filestore/`** is the artifact storage directory, created at runtime. It's volume-mounted in Docker.
