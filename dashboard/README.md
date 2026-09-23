# PropLeads Dashboard

Panel mínimo en Next.js 15 (App Router + TypeScript) que consume la API real
del backend (no la demo client-side del portfolio): carga leads por
`POST /webhook/lead` (REST) y los lista consultando `POST /graphql`.

## Correrlo

Necesita el backend real corriendo (ver `../README.md`):

```bash
# en la raíz del repo
docker compose up --build
```

Y en esta carpeta:

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

Abrí http://localhost:3000. Si el backend no está corriendo, el panel lo
avisa explícitamente en vez de romperse en blanco.
