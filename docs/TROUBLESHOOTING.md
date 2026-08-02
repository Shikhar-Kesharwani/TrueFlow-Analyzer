# Troubleshooting Guide

### Python Engine crashes with "ModuleNotFoundError"
- Ensure you have installed the requirements using `pip install -r requirements.txt`.

### Dashboard displays "Connecting to Engine..." endlessly
1. Check if the Node.js API is running on port `3001`.
2. Open the browser dev tools (F12) -> Console. If there are CORS errors, ensure `ALLOWED_ORIGINS` in your `.env` includes your frontend URL (e.g., `http://localhost:5173`).
3. Ensure you are running the `live_dpi_engine.py` script. The dashboard only connects to the API; the API receives data from the Engine.

### Nginx returns 502 Bad Gateway (Docker Compose)
- The Node API container might have crashed. Check logs via `docker logs trueflow_api`.

### Model 1 Vercel Deployment displays blank screen
- Ensure your `VITE_API_URL` environment variable is set in the Vercel dashboard and points to your Render backend URL. Ensure you redeploy after setting it.
