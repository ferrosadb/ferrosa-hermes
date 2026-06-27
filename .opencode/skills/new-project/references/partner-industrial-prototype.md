# Partner Industrial Prototype Pattern

Session-derived reference for B2B industrial demos where the user wants a private repo plus a working slice before a full plan.

## Trigger

Use this reference when the request includes most of:

- Private partner/customer demo.
- Industrial, compliance, safety, manufacturing, oil/gas, chemical, power, or regulated-process domain.
- Explicit stack and repo location.
- External service boundaries such as FerrosaDB/CQL/RRDB, MinIO/S3, or local container services.
- A request for a blueprint plus wording like "working slices are better" or "fast prototype".

## Recommended Build Shape

1. Create the private repo under the requested owner/org and preserve local git hygiene.
2. Scaffold the stated framework without asking generic language/framework questions.
3. Add container/dev orchestration early so service boundaries are real:
   - app container
   - object storage container/bucket setup
   - database or placeholder target container/adapter
4. Build one visible workflow:
   - configure an industrial recipe/process
   - generate deterministic query/rule output
   - show human-in-loop approval or audit state
5. Keep external integrations behind thin adapters and flags so the slice remains runnable when live infra is unavailable.
6. Write blueprint/spec docs from what exists, not a speculative back-to-front plan.
7. Verify with native tests, container build, and a curl/browser smoke test.
8. End with one grill-me question plus a recommended answer.

## InterLock AI Example

A good first slice for the InterLock AI class of prototype:

- Phoenix/LiveView UI for configuring upstream/downstream industrial processing recipes.
- FerrosaDB CQL/RRDB-oriented query draft for sensor/anomaly data.
- Datalog-style rule draft for human-in-loop safety decisions, with ferrosa-memory called out as a likely future rules engine.
- MinIO/S3 adapter for persisted artifacts/evidence bundles.
- Blueprint docs under `specs/` capturing vertical, deployment, buyer, role, certification, threat model, FMEA, and test plan.

## Pitfalls

- Do not turn the request into a pure planning engagement.
- Do not ask which language/framework to use when the user already specified it.
- Do not hide service boundaries behind in-memory-only code; use adapters and containers even if demo data is generated.
- Do not claim integration is done unless a live service path was exercised. Label adapter-only work precisely.
