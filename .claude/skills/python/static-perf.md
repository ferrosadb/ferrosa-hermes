# Python — Static Performance Patterns

Companion to `/performance-tuning static`. Catalogs Python-specific patterns
that **commonly** cause performance issues. Use only after `/dsm-analysis`.

> **DISCLAIMER — STATIC INFERENCE, NOT MEASUREMENT.** Findings here are
> hypotheses inferred from code patterns. Before acting, baseline the system
> under representative load and measure prospective improvements against
> actual system performance. Prefer clearly written code over micro-benchmark
> cleverness; CPython optimizes many idioms (and the GIL means many
> "optimizations" don't help anyway).

## Hot-path heuristics

- `@app.get`/`@app.post`/`@router.*` (FastAPI), `def get/post(self)`
  (Django/DRF), `@app.route` (Flask).
- Celery `@task`, RQ jobs, FastAPI `BackgroundTasks` callees.
- `asyncio.run`/`uvloop` event-loop callees.
- Top-quartile DSM fan-in modules.

## Lock & GIL contention

| Pattern | Signal | Why | Idiomatic alternative |
|---------|--------|-----|----------------------|
| Long pure-Python compute under threading | `threading.Thread` running heavy work | GIL serializes; threads don't help CPU-bound | `multiprocessing`, `concurrent.futures.ProcessPoolExecutor`, or rewrite hot kernel in NumPy/numba/cython |
| `threading.Lock` held across I/O or DB call | `with lock: ... db.execute ...` | Critical section grows with network latency | Hold the lock only over the in-memory mutation |
| `asyncio.Lock` held across `await` to slow service | `async with lock: ... await client.get(...)` | All tasks waiting on this lock serialize | Fetch first, then briefly lock for state update |
| Per-request `multiprocessing.Manager()`/proxy | grep `Manager().` in handlers | Proxies cost a syscall round-trip per access | Pre-shared queue / shared memory |
| Module-level mutable state mutated from threads | global `dict` / `list` w/o lock | Tearing, lost updates | Explicit lock or thread-safe structure |

## Algorithmic complexity

| Pattern | Signal | Inferred Big-O | Fix |
|---------|--------|----------------|-----|
| `for x in xs: for y in xs:` | nested loops over input | O(n²) | Build a `dict`/`set` index once |
| `if x in some_list` inside loop | `in` on a `list` | O(n·m) | `set` or `frozenset` |
| `s = s + chunk` over n chunks | string `+=` in loop | O(n²) memory copy | `''.join(parts)` |
| `list.insert(0, x)` / `list.pop(0)` in loop | grep `\.insert\(0`, `\.pop\(0` | O(n) per call | `collections.deque` |
| `sorted(xs)[:k]` for top-k | sort then slice | O(n log n) | `heapq.nsmallest(k, xs)` → O(n log k) |
| `re.compile(pat)` inside loop / handler | per-request regex compile | parse + alloc per call | Module-level `_PAT = re.compile(...)` |
| Recursive without `@functools.cache` | overlapping subproblems | exponential | `@functools.lru_cache` / DP |
| Pandas `df.iterrows()` over large frames | grep `iterrows()` | O(n) Python-level dispatch per row, ~100× slower | Vectorize with NumPy ops, or `df.apply` (still slow but better), or `df.to_records` |
| Pandas `df.append()` in loop | grep `\.append\(` on DataFrame | O(n²), copies whole frame | Build `list[dict]` then `pd.DataFrame(list)` once |
| Pandas chained indexers `df[a][b] = …` | SettingWithCopyWarning | hidden copy, O(n) extra | `df.loc[a, b] = …` |
| ORM N+1 (Django/SQLAlchemy) | `for obj in qs: obj.related.x` without `select_related`/`joinedload` | n round-trips | `select_related`, `prefetch_related`, `joinedload` |

## Allocation / GC pressure

| Pattern | Better |
|---------|--------|
| `dict(**a, **b)` in tight loop creating many merged dicts | `{**a, **b}` is the same; the cost is the merge itself — restructure to avoid |
| `[x for x in xs if ...]` only to iterate once | generator `(x for x in xs if ...)` |
| Building large list to compute `sum(...)`/`any(...)` | pass the generator directly |
| `copy.deepcopy` of large dict per request | re-design to avoid; or use immutable `attrs(frozen=True)` / `pydantic` model and share |
| `json.dumps` of large object per request | Pre-serialize when possible; consider `orjson` only if measured to matter |

## Async / IO

| Pattern | Why | Fix |
|---------|-----|-----|
| `requests.get(...)` inside `async def` | Blocks the event loop — every other task stalls | `httpx.AsyncClient` / `aiohttp` |
| `time.sleep(s)` inside `async def` | Same | `await asyncio.sleep(s)` |
| Sync DB driver (`psycopg2`, sync `pymongo`) inside `async def` | Same | `asyncpg`, `motor`, or run in `asyncio.to_thread` |
| File I/O without buffering or `with` block in loop | Syscall per byte/line, possible leak | Open once outside the loop; use `with`; iterate the file (which is buffered) |
| `await` inside a tight CPU loop with no `asyncio.sleep(0)` | One coroutine hogs the event loop | Either move CPU work to a thread/process, or yield occasionally |
| Per-request `httpx.AsyncClient()` | TCP/TLS handshake per request | Build one client at app startup, reuse |
| Per-request DB engine creation | Same | Use a pool: `create_async_engine(...)` once, depended-on |

## Data structure misuse

- `list` used as a set (`.append` + `if x not in lst`) → `set`.
- `list` used as a queue (`.pop(0)`) → `collections.deque`.
- `dict` keyed on a tuple containing a large mutable converted to tuple each
  access → cache the key.
- Using `pandas` for tiny data structures — overhead dwarfs the work; use
  plain dicts/lists.

## Tools to seed candidates

- `ruff check --select PERF,B,C4,SIM` (PERF rules catch many of the above).
- `pylint --enable=R0915,W0631,too-many-nested-blocks`.
- `perflint` (focused on PERF anti-patterns).
- `pandas-stubs` + `mypy --strict` for pandas misuse.
- `py-spy` — runtime profiler (use **after** baselining).

## What NOT to flag

- List comprehensions vs `for` loops — comprehension is faster *and* clearer.
- `len(x) == 0` vs `not x` — same speed, both clear.
- Tuple-vs-list for small literals — irrelevant.
- One-time setup/import cost.
- f-strings — fastest format option; idiomatic.

## Recommended fix style

Prefer changes that **simplify** code:

1. Replace `for/append` with a comprehension — clearer, often faster.
2. Replace nested loop + `in list` with a precomputed `set` — clearer intent.
3. Hoist `re.compile` to module scope — declares the regex as a constant.
4. Vectorize pandas where the loop becomes a one-liner. Do not vectorize when
   the result is unreadable; readability beats a 2× win on a non-bottleneck.
