# Production line digital Twin and bottleneck Intelligence

A working prototype of your project:
**User input → 3D Digital Twin update → Simulation update → Bottleneck recalculation → AI recommendation.**

## What's implemented

| Layer | Tech | What it does |
|---|---|---|
| 3D Digital Twin | React + Three.js (`@react-three/fiber`) | Renders each machine as a 3D block, sized/animated from its real parameters (capacity → size, processing time → height, operating speed → rotation speed). Swap this for Unity later without touching the backend. |
| UI | React (Vite) | Form to add machines, live line list, run-simulation / predict buttons, results dashboard (recharts). |
| Backend API | FastAPI | CRUD for machines, `/simulate`, `/predict`. |
| Simulation | SimPy | Discrete-event model: parts flow through machines in sequence; each machine has capacity, processing time, random breakdown probability, repair time. Computes throughput, utilization, wait time, downtime, and flags the bottleneck (highest-utilization machine). |
| AI layer | scikit-learn (`IsolationForest`) | Scores each machine's anomaly/failure risk from its simulated behavior. Rule-based recommendations engine also included in `simulation.py`. |
| Storage | MongoDB (via `motor`), with automatic in-memory fallback | Works immediately with zero setup; point `MONGO_URI` at a real Mongo instance when ready. |

This is the same architecture you described — Unity/Blender is represented here by the Three.js twin so you have something you can run today; the FastAPI/SimPy/MongoDB/scikit-learn layers are unchanged if you later swap in Unity for higher-fidelity visuals (Unity would just call the same REST API).

## Folder structure

```
digital-twin-project/
├── backend/
│   ├── main.py            FastAPI app & routes
│   ├── models.py          Pydantic schemas (Machine, SimulationResult, etc.)
│   ├── simulation.py      SimPy discrete-event simulation engine
│   ├── ml_predict.py      IsolationForest-based risk scoring
│   ├── database.py        MongoDB (motor) with in-memory fallback
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    │       ├── MachineForm.jsx   (input parameters form)
    │       ├── MachineList.jsx
    │       ├── TwinScene.jsx     (the 3D digital twin)
    │       └── Dashboard.jsx     (charts + recommendations)
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## How to run in VS Code

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to see and test the live Swagger API.

By default it runs with in-memory storage (no setup needed). To use real MongoDB, create a `.env` file in `backend/` with:
```
MONGO_URI=mongodb://localhost:27017
```

### 2. Frontend (React)
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. Add a machine, click **Run Simulation**, then **Predict Risk (AI)**.

### VS Code tips
- Install the **Python** and **ES7+ React/Redux/JS snippets** extensions.
- Use two integrated terminals side-by-side (one for backend, one for frontend) via the split-terminal button.
- The backend auto-reloads on save (`--reload`); the frontend hot-reloads automatically (Vite).

## Extending this toward your full proposal

- **Unity 3D / Blender:** replace `TwinScene.jsx` with a Unity WebGL build; have it poll the same `/machines` and `/simulate` endpoints (or receive them via a small WebSocket bridge) instead of Three.js.
- **MQTT / OPC UA live data:** add a `sensor_ingest.py` service that subscribes to machine topics and calls `save_machine()` / a new `/telemetry` endpoint so the twin reflects real machine state instead of only simulated state.
- **Better AI recommendations:** once you have real historical run data, replace the rule-based `_generate_recommendations()` in `simulation.py` with a trained model (e.g., a regression/classification model in `ml_predict.py`) that learns which interventions actually raised throughput.
- **Persistent simulation history:** store each `SimulationResult` in MongoDB (a `simulation_runs` collection) so you can chart trends over time, not just the latest run.
