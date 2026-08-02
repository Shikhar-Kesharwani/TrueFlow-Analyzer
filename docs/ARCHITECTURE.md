# Architecture Documentation

This document explains the Dual Architecture deployment of **TrueFlow-Analyzer**.

## Model 1 — Cloud-Native (Hybrid approach)

```mermaid
graph TB
    subgraph MODEL1["Model 1 — Cloud-Native Hybrid"]
        A1[User Browser] --> B1[Vercel\n React Frontend]
        B1 --> C1[Render Web Service\n Node Express API]
        D1[Local Machine\n Python live_dpi_engine.py] -->|POST /telemetry| C1
    end
```
*Note: Due to the 2.5GB ML model size, the Python engine cannot run on free serverless hosting and must run locally.*

## Model 2 — Docker Compose (Self-Hosted)

```mermaid
graph TB
    subgraph MODEL2["Model 2 — Docker Compose (Local/VPS)"]
        A2[User Browser] --> B2[Nginx Container\n Port 80]
        B2 --> C2[React UI Container\n Port 5173]
        B2 --> D2[Express API Container\n Port 3001]
        E2[Local Machine\n Python live_dpi_engine.py] -->|POST /telemetry| D2
    end
```
