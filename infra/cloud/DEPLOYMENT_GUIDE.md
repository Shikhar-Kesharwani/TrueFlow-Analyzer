# Cloud-Native Hybrid Deployment (Vercel + Render)

## Step 1: Backend Deployment (Render)
1. Sign up for Render (render.com).
2. Connect your GitHub repository.
3. Render will automatically detect the `render.yaml` blueprint.
4. Click **Apply Blueprint**.
5. It will provision the Node.js API service based on the Dockerfile.
6. Copy the resulting URL (e.g., `https://trueflow-analyzer-api.onrender.com`).

## Step 2: Frontend Deployment (Vercel)
1. Sign up for Vercel (vercel.com).
2. Click **Add New** > **Project** and select your repository.
3. Framework Preset: **Vite**.
4. Root Directory: `dashboard`.
5. In Environment Variables, add:
   - `VITE_API_URL` = `[Your Render URL from Step 1]`
6. Click **Deploy**.

## Step 3: Local Engine Connectivity
1. On your local machine, open your `.env` or set an environment variable:
   - `API_URL=[Your Render URL from Step 1]/telemetry`
2. Run the engine: `python live_dpi_engine.py --mode live`
3. The Vercel dashboard will instantly reflect your local traffic!
