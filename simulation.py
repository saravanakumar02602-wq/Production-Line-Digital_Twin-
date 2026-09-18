"""
Discrete-event simulation of the production line using SimPy.

Every machine in the line is modeled as a SimPy Resource with:
  - a processing time (scaled by operating_speed)
  - a random chance of breakdown each cycle (downtime_probability)
  - a repair time when it breaks (mean_repair_time)

Parts arrive at fixed intervals and flow through machines in the
order given by `position_index`. This whole model is rebuilt fresh
every time the user changes a machine or the line, which is what
gives us the "dynamic" digital twin behaviour.
"""
import random
import simpy
from models import Machine, SimulationConfig, SimulationResult, MachineResult


class MachineState:
    def __init__(self, machine: Machine):
        self.machine = machine
        self.units_processed = 0
        self.total_wait_time = 0.0
        self.busy_time = 0.0
        self.downtime_events = 0
        self.total_downtime_seconds = 0.0


def _machine_process(env, resource, state: Machine, mstate: MachineState, part_id):
    arrival = env.now
    with resource.request() as req:
        yield req
        wait = env.now - arrival
        mstate.total_wait_time += wait

        # Random breakdown check before processing this part
        if random.random() < state.downtime_probability:
            mstate.downtime_events += 1
            repair = max(0, random.expovariate(1 / state.mean_repair_time)) if state.mean_repair_time > 0 else 0
            mstate.total_downtime_seconds += repair
            yield env.timeout(repair)

        proc_time = state.processing_time / max(state.operating_speed, 0.01)
        start = env.now
        yield env.timeout(proc_time)
        mstate.busy_time += (env.now - start)
        mstate.units_processed += 1


def _part_generator(env, resources, machines, states, config: SimulationConfig, completed_counter):
    part_id = 0
    while True:
        yield env.timeout(config.arrival_interval)
        part_id += 1
        env.process(_run_part_through_line(env, resources, machines, states, part_id, completed_counter))


def _run_part_through_line(env, resources, machines, states, part_id, completed_counter):
    for res, machine, mstate in zip(resources, machines, states):
        yield env.process(_machine_process(env, res, machine, mstate, part_id))
    completed_counter["count"] += 1


def run_simulation(machines: list[Machine], config: SimulationConfig) -> SimulationResult:
    if not machines:
        return SimulationResult(
            throughput_per_hour=0,
            total_units_completed=0,
            machine_results=[],
            bottleneck_machine=None,
            recommendations=["Add at least one machine to run a simulation."],
        )

    # Order machines by position_index (fallback: the order given)
    ordered = sorted(
        enumerate(machines),
        key=lambda pair: pair[1].position_index if pair[1].position_index is not None else pair[0],
    )
    ordered_machines = [m for _, m in ordered]

    env = simpy.Environment()
    resources = [simpy.Resource(env, capacity=max(1, int(m.capacity // 10) or 1)) for m in ordered_machines]
    states = [MachineState(m) for m in ordered_machines]
    completed_counter = {"count": 0}

    env.process(_part_generator(env, resources, ordered_machines, states, config, completed_counter))
    env.run(until=config.sim_time_seconds)

    machine_results = []
    utilizations = {}
    for mstate in states:
        m = mstate.machine
        utilization_pct = (mstate.busy_time / config.sim_time_seconds) * 100 if config.sim_time_seconds else 0
        avg_wait = (mstate.total_wait_time / mstate.units_processed) if mstate.units_processed else 0
        utilizations[m.name] = utilization_pct
        machine_results.append(
            MachineResult(
                id=m.id,
                name=m.name,
                units_processed=mstate.units_processed,
                utilization_pct=round(utilization_pct, 2),
                avg_wait_time=round(avg_wait, 2),
                downtime_events=mstate.downtime_events,
                total_downtime_seconds=round(mstate.total_downtime_seconds, 2),
                is_bottleneck=False,
            )
        )

    # Bottleneck = highest utilization machine (classic theory-of-constraints heuristic)
    bottleneck_name = max(utilizations, key=utilizations.get) if utilizations else None
    for mr in machine_results:
        if mr.name == bottleneck_name:
            mr.is_bottleneck = True

    throughput_per_hour = (completed_counter["count"] / config.sim_time_seconds) * 3600 if config.sim_time_seconds else 0

    recommendations = _generate_recommendations(machine_results, bottleneck_name)

    return SimulationResult(
        throughput_per_hour=round(throughput_per_hour, 2),
        total_units_completed=completed_counter["count"],
        machine_results=machine_results,
        bottleneck_machine=bottleneck_name,
        recommendations=recommendations,
    )


def _generate_recommendations(machine_results, bottleneck_name):
    """Simple rule-based recommendation layer (works even before the
    scikit-learn model is trained on real historical data)."""
    recs = []
    for mr in machine_results:
        if mr.is_bottleneck:
            recs.append(
                f"'{mr.name}' is the bottleneck at {mr.utilization_pct}% utilization — "
                f"consider increasing its capacity, adding a parallel unit, or reducing its processing time."
            )
        if mr.downtime_events > 3:
            recs.append(
                f"'{mr.name}' had {mr.downtime_events} downtime events — "
                f"consider preventive maintenance or lowering its downtime probability."
            )
        if mr.utilization_pct < 20:
            recs.append(
                f"'{mr.name}' is under-utilized ({mr.utilization_pct}%) — "
                f"consider removing it, reassigning it, or feeding it from an earlier bottleneck fix."
            )
    if not recs:
        recs.append("Line is balanced. No immediate changes recommended.")
    return recs
