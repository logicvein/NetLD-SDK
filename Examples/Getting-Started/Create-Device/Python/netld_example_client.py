import json
import os
import uuid

import requests
from dotenv import load_dotenv


class NetLDError(RuntimeError):
    pass


def load_environment(path):
    load_dotenv(path, override=True)


class NetLDClient:
    def __init__(self, base_url, api_key, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    @classmethod
    def from_env(cls):
        base_url = os.getenv("NETLD_BASE_URL", "").strip()
        api_key = os.getenv("NETLD_API_KEY", "").strip()
        if not base_url:
            raise NetLDError("Set NETLD_BASE_URL in .env before running this example.")
        if not api_key:
            raise NetLDError("Set NETLD_API_KEY in .env before running this example.")
        return cls(base_url, api_key)

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def login(self):
        try:
            response = self.session.get(
                f"{self.base_url}/rest",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise NetLDError(f"Could not reach {self.base_url}.") from exc
        if response.is_redirect:
            raise NetLDError(f"Login redirected to {response.headers.get('Location', '')}.")
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise NetLDError(f"Login failed with HTTP {response.status_code}.") from exc

    def call(self, method, **parameters):
        payload = {"jsonrpc": "2.0", "method": method, "params": parameters, "id": str(uuid.uuid4())}
        try:
            response = self.session.post(
                f"{self.base_url}/rest",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise NetLDError(f"Could not reach {self.base_url}.") from exc
        if response.is_redirect:
            raise NetLDError(f"API call redirected to {response.headers.get('Location', '')}.")
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise NetLDError(f"API call failed with HTTP {response.status_code}.") from exc
        data = response.json()
        if data.get("error"):
            raise NetLDError(json.dumps(data["error"]))
        return data.get("result")

    def get_device(self, network, ip_address):
        return self.call("Inventory.getDevice", network=network, ipAddress=ip_address)

    def create_device(self, network, ip_address, adapter_id):
        return self.call(
            "Inventory.createDevice", network=network, ipAddress=ip_address, adapterId=adapter_id
        )
