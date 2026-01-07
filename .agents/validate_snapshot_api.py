import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skybridge.platform.bootstrap.app import get_app
from skybridge.platform.config import config as config_module
from skybridge.platform.delivery import routes as routes_module

os.environ["SKYBRIDGE_API_KEYS"] = "test-key:test-client"
os.environ["SKYBRIDGE_METHOD_POLICY"] = "test-client:health,fileops.read,snapshot.capture,snapshot.compare"
os.environ["ALLOW_LOCALHOST"] = "false"
os.environ["SKYBRIDGE_RATE_LIMIT_PER_MINUTE"] = "0"
config_module._security_config = None

client = TestClient(get_app().app)
routes_module._ticket_store.clear()

resp = client.get("/ticket", params={"method": "snapshot.capture"}, headers={"X-API-Key": "test-key"})
print("/ticket snapshot.capture", resp.status_code, resp.json())
ticket_id = resp.json()["ticket"]["id"]

payload = {
    "ticket_id": ticket_id,
    "detail": {
        "context": "snapshot",
        "action": "capture",
        "subject": "fileops",
        "payload": {"target": ".", "depth": 2},
    },
}
resp = client.post("/envelope", json=payload, headers={"X-API-Key": "test-key"})
print("/envelope snapshot.capture", resp.status_code)
print(resp.json())

snapshot_id = resp.json().get("result", {}).get("snapshot_id")

resp = client.get("/ticket", params={"method": "snapshot.compare"}, headers={"X-API-Key": "test-key"})
print("/ticket snapshot.compare", resp.status_code, resp.json())
ticket_id = resp.json()["ticket"]["id"]

payload = {
    "ticket_id": ticket_id,
    "detail": {
        "context": "snapshot",
        "action": "compare",
        "subject": "fileops",
        "payload": {"old_snapshot_id": snapshot_id, "new_snapshot_id": snapshot_id, "format": "json"},
    },
}
resp = client.post("/envelope", json=payload, headers={"X-API-Key": "test-key"})
print("/envelope snapshot.compare", resp.status_code)
print(resp.json())
