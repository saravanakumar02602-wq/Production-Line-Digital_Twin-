"""
FastAPI backend for the Dynamic 3D Digital Twin & AI-Based Production
Intelligence System.

Run with:
    uvicorn main:app --reload --port 8000

Endpoints:
    POST   /machines            add a machine -> regenerates the twin+line
    GET    /machines            list current machines (current line state)
    DELETE /machines/{id}       remove a machine -> regenerates the twin+line
    PUT    /machines/{id}       update a machine's parameters
    POST   /simulate            run the SimPy simulation on current machines
    POST   /predict             run AI risk/anomaly scoring on last sim result
    DELETE /machines            clear the whole line (start blank)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import Machine, MachineIn, SimulationConfig, SimulationResult
from database import save_machine, delete_machine, get_all_machines, clear_all
from simulation import run_simulation
from ml_predict import predict_risk

app = FastAPI(title="Digital Twin Production Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep the last simulation result in memory so /predict can use it
_last_simulation_result: SimulationResult | None = None


@app.get("/")
async def root():
    return {"status": "ok", "service": "digital-twin-backend"}


@app.post("/machines", response_model=Machine)
async def add_machine(machine_in: MachineIn):
    """User enters a machine name + parameters -> a new twin is created."""
    machine = Machine(**machine_in.model_dump())
    await save_machine(machine.model_dump())
    return machine


@app.get("/machines", response_model=list[Machine])
async def list_machines():
    docs = await get_all_machines()
    return [Machine(**d) for d in docs]


@app.put("/machines/{machine_id}", response_model=Machine)
async def update_machine(machine_id: str, machine_in: MachineIn):
    """Changing parameters here re-syncs the twin + simulation automatically
    the next time /simulate is called -- no manual rebuild needed."""
    updated = Machine(id=machine_id, **machine_in.model_dump())
    await save_machine(updated.model_dump())
    return updated


@app.delete("/machines/{machine_id}")
async def remove_machine(machine_id: str):
    await delete_machine(machine_id)
    return {"deleted": machine_id}


@app.delete("/machines")
async def reset_line():
    await clear_all()
    return {"status": "cleared"}


@app.post("/simulate", response_model=SimulationResult)
async def simulate(config: SimulationConfig = SimulationConfig()):
    global _last_simulation_result
    docs = await get_all_machines()
    machines = [Machine(**d) for d in docs]
    if not machines:
        raise HTTPException(status_code=400, detail="No machines in the line yet. Add a machine first.")
    result = run_simulation(machines, config)
    _last_simulation_result = result
    return result


@app.post("/predict")
async def predict():
    """AI layer: score each machine's failure/anomaly risk based on the
    most recent simulation run."""
    if _last_simulation_result is None:
        raise HTTPException(status_code=400, detail="Run /simulate first.")
    machine_dicts = [m.model_dump() for m in _last_simulation_result.machine_results]
    scored = predict_risk(machine_dicts)
    return {"risk_analysis": scored}
