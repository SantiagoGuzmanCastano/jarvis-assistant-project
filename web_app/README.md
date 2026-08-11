# Jarvis Web

Cliente activo de Jarvis, construido con React, TypeScript, Vite y TanStack Query. `../flutter_app` se conserva para una futura fase móvil, pero no es el cliente actual.

## Desarrollo local

El backend FastAPI permite `http://localhost:3000` y el callback OAuth regresa a ese origen. Por eso el cliente debe usar ese puerto durante el desarrollo.

```powershell
Copy-Item .env.example .env
npm install
npm run dev -- --port 3000
```

## Arquitectura

- `src/core/api.ts`: cliente Axios central; agrega el bearer token, intenta una rotación tras un `401` y repite la solicitud original.
- `src/core/session-store.ts`: conserva el par JWT en `localStorage`.
- `src/core/services.ts`: contratos HTTP con FastAPI.
- `src/features/`: pantallas y flujos de producto.

La aplicación cubre autenticación, onboarding, conversaciones, chat, ajustes y conexión/desconexión de Google. La misma autorización habilita las tools conversacionales de Gmail y Google Calendar; Calendar no tiene una pantalla propia en el MVP.

Si la cuenta fue conectada antes de añadir los scopes de Calendar, debe desconectarse y conectarse nuevamente para concederlos.

## Verificación

```powershell
npm run lint
npm run build
```
