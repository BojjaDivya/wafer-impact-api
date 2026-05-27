# DESIGN.md – Key Design Decisions

## 1. Recursive resolver with memoization (`calculator.py`)

The BrightWay2 format creates a directed acyclic graph (DAG) of activities.
`ImpactCalculator._resolve()` walks this graph depth-first, caching results in
`self._memo` so shared sub-activities (e.g. `Electricity, GLO mix` used by
multiple recipes) are computed only once. Cycle detection uses an immutable
`visiting` set passed per recursion branch — cheaper than a stack and
correct even if the graph is called re-entrant.

## 2. Layered lookup: base + partner overlay (`main.py`)

Company A's activities are loaded once at startup into a module-level dict.
For partner requests, a shallow copy (`dict(company_a_data)`) is made and
partner activities are overlaid. The base dict is never mutated, so concurrent
requests cannot corrupt each other. Conflict detection (Part 2 constraint) is
enforced at upload time.

## 3. Partner data isolation (`partner.py` + SQLite)

Partner recipes are stored in a separate SQLite table keyed by `(partner_id,
activity_name)`. This enforces the separation requirement architecturally —
Company A's in-memory store is never written to by a partner upload.
SQLite survives process restarts without requiring a full database server.

## 4. Framework choice: FastAPI

FastAPI gives automatic OpenAPI docs (`/docs`), async file uploads, typed
path/query parameters, and Pydantic validation for free. The overhead is
negligible for this workload.

## TODOs (given more time)

- Authentication / API keys so only authorised partners can upload.
- Per-partner namespacing to prevent partner A seeing partner B's activity names.
- Async DB access (SQLAlchemy async) for concurrent upload load.
- Integration tests using `httpx.AsyncClient` + `TestClient`.
- Docker / docker-compose for one-command setup.
