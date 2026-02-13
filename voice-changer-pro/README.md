<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Voice Changer Pro (Frontend)

React + Vite UI for the FastAPI voice changer backend.

## Run Locally

**Prerequisites:**  Node.js

1. Install dependencies:
   `npm install`
2. Backend URL:
   - **Dev (recommended):** leave `VITE_API_BASE_URL` empty in `.env.local` and run the FastAPI backend on `http://127.0.0.1:8000`. Vite will proxy `/voice-changer`, `/outputs`, and `/healthz`.
   - **Prod:** set `VITE_API_BASE_URL` to your backend base URL (e.g. Render):
     `VITE_API_BASE_URL=https://your-backend.onrender.com`

3. (Optional) Main-site Voice Library URL:
    - By default, the UI uses the same base as `VITE_API_BASE_URL` (or the dev proxy) for voice-library endpoints.
    - To pull voices from the main site instead (e.g. `https://noiz.ai`), set:

       `VITE_VOICE_LIBRARY_BASE_URL=https://noiz.ai`

    Notes:
    - For cross-origin requests, custom headers can trigger CORS preflight. By default, when `VITE_VOICE_LIBRARY_BASE_URL` is set, the app will **not** send `X-User-Id`.
    - If you control CORS and want `is_favorited` to work via `X-User-Id`, enable it explicitly:
       `VITE_VOICE_LIBRARY_SEND_USER_ID=true`
    - If the main site relies on cookie session and allows credentials via CORS, you can set:
       `VITE_VOICE_LIBRARY_CREDENTIALS=include`
4. Run the app:
   `npm run dev`

## Deploy (Vercel + Render)

### Vercel (frontend)

- Create a new Vercel project pointing at this directory (set **Root Directory** to `voice-changer-pro`).
- Set environment variable `VITE_API_BASE_URL` to your backend URL (Render), e.g. `https://your-backend.onrender.com`.

### Render (backend)

- Ensure the FastAPI service has CORS configured to allow your Vercel domain.
- Set `ALLOWED_ORIGINS` on the backend, e.g.:
  `ALLOWED_ORIGINS=https://your-frontend.vercel.app`

Notes:
- If you use multiple preview domains, separate with commas.
- The backend serves generated audio from `/outputs/*`.
