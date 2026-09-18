"""
Data models for machines and simulation configuration.
These describe exactly the parameters a user enters on the frontend
to dynamically generate a machine's Digital Twin.
"""
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class MachineIn(BaseModel):
    """What the user types in on the 'Add Machine' form."""
    name: str = Field(..., description="Machine name/model, e.g. 'CNC Lathe X200'")
    machine_type: str = Field(..., description="e.g. CNC, Press, Conveyor, Robot Arm")
    capacity: float = Field(..., gt=0, description="Units it can process per cycle")
    processing_time: float = Field(..., gt=0, description="Seconds to process 1 unit")
    operating_speed: float = Field(1.0, gt=0, description="Speed multiplier (1.0 = normal)")
    working_hours: float = Field(8.0, gt=0, description="Hours available per shift")
    downtime_probability: float = Field(0.05, ge=0, le=1, description="Chance of random failure per cycle")
    mean_repair_time: float = Field(300, ge=0, description="Seconds to recover from failure")
    position_index: Optional[int] = Field(None, description="Order in the production line (0 = first)")
    model_url: Optional[str] = Field(None, description="Optional URL to a .glb or .gltf machine model")


class Machine(MachineIn):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Simple derived "twin size" so the 3D model scales with real specs
    @property
    def twin_scale(self):
        return {
            "width": 1 + (self.capacity / 50),
            "height": 1 + (self.processing_time / 20),
            "speed_factor": self.operating_speed,
        }


class SimulationConfig(BaseModel):
    sim_time_seconds: float = Field(3600, description="How long to simulate, in seconds")
    arrival_interval: float = Field(10, description="Seconds between new parts entering the line")


class MachineResult(BaseModel):
    id: str
    name: str
    units_processed: int
    utilization_pct: float
    avg_wait_time: float
    downtime_events: int
    total_downtime_seconds: float
    is_bottleneck: bool


class SimulationResult(BaseModel):
    throughput_per_hour: float
    total_units_completed: int
    machine_results: list[MachineResult]
    bottleneck_machine: Optional[str]
    recommendations: list[str]
