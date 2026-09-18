import json
import urllib.request

base = 'http://127.0.0.1:8000'

machine = {
    'name': 'CNC Lathe X200',
    'machine_type': 'CNC',
    'capacity': 25,
    'processing_time': 40,
    'operating_speed': 1.2,
    'working_hours': 8,
    'downtime_probability': 0.08,
    'mean_repair_time': 180,
    'position_index': 0,
}

req1 = urllib.request.Request(
    f'{base}/machines',
    data=json.dumps(machine).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req1, timeout=20) as resp1:
    print('POST /machines ->', resp1.status)
    print(resp1.read().decode())

req2 = urllib.request.Request(
    f'{base}/simulate',
    data=b'{}',
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req2, timeout=20) as resp2:
    print('POST /simulate ->', resp2.status)
    print(resp2.read().decode())
