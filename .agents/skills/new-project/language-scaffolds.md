## Contents

- Python scaffolding (uv, library, application, FastAPI)
- Elixir/Phoenix scaffolding (web, API-only)
- Rust scaffolding (binary, library)
- Go scaffolding (module init)
- Node.js/TypeScript scaffolding
- Full-stack project structures (FastAPI + Next.js/Vite, Phoenix + Next.js)
- Frontend proxy configurations (Next.js, Vite)

---

## Python (uv)

Read the uv documentation at <https://docs.astral.sh/uv/concepts/projects/init/> and follow the instructions.

**For a library project:**

```bash
uv init --lib <project-name>
```

**For an application project:**

```bash
uv init <project-name>
```

## Elixir/Phoenix (mix)

Read the Phoenix installation guide at <https://hexdocs.pm/phoenix/installation.html>.

**For a Phoenix web project:**

```bash
mix phx.new <project-name>
```

**For a Phoenix API-only project:**

```bash
mix phx.new <project-name> --no-html --no-assets
```

## Rust (cargo)

Read the Cargo reference at <https://doc.rust-lang.org/cargo/commands/cargo-init.html>.

**For a binary project:**

```bash
cargo init <project-name>
```

**For a library project:**

```bash
cargo init --lib <project-name>
```

## Go (go mod)

Read the Go modules reference at <https://go.dev/ref/mod>.

```bash
mkdir <project-name>
cd <project-name>
go mod init <module-path>
```

Use a module path of the form `github.com/<username>/<project-name>` or a local path if the project is not intended for publication.

## Node.js/TypeScript (npm)

```bash
mkdir <project-name>
cd <project-name>
npm init -y
npm install --save-dev typescript @types/node ts-node
npx tsc --init
```

## Full-Stack: FastAPI + Next.js or Vite

Read the uv FastAPI guide at <https://docs.astral.sh/uv/guides/integration/fastapi/> and initialize the backend with this structure:

```
backend/
├── app/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── items.py
│   │   └── users.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── item_service.py
│   │   └── user_service.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── item_schemas.py
│   │   └── user_schemas.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py
│   └── main.py
├── pyproject.toml
└── uv.lock
```

Backend runs on `http://localhost:8000` by default.

## Full-Stack: Phoenix + Next.js

**Backend (`backend/` subdirectory — Phoenix API-only):**

```bash
cd <project-name>
mix phx.new backend --no-html --no-assets
```

Default Phoenix port is `4000`. Ensure CORS is configured to allow the frontend origin.

## Frontend Proxy Configuration

### Next.js

Read <https://ui.shadcn.com/docs/installation/next> and follow the instructions. Configure proxy for backend API in `next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:<backend-port>/api/:path*',
      },
    ];
  },
};
module.exports = nextConfig;
```

### Vite

Read <https://ui.shadcn.com/docs/installation/vite> and follow the instructions. Configure proxy for backend API in `vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:<backend-port>',
        changeOrigin: true,
      },
    },
  },
})
```
