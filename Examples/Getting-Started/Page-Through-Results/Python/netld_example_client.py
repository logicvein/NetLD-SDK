import json
import os
import uuid

import requests
from dotenv import load_dotenv


class NetLDError(RuntimeError):
    pass


class NetLDClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10, debug: bool = False):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.debug = debug
        self.session = requests.Session()

    @classmethod
    def from_env(cls) -> "NetLDClient":
        load_dotenv()
        base_url = os.environ.get("NETLD_BASE_URL", "").strip()
        api_key = os.environ.get("NETLD_API_KEY", "").strip()
        if not base_url:
            raise NetLDError("Set NETLD_BASE_URL in .env before running this example.")
        if not api_key:
            raise NetLDError("Set NETLD_API_KEY in .env before running this example.")
        return cls(base_url, api_key, debug=os.environ.get("NETLD_DEBUG") == "1")

    def login(self) -> None:
        response = self._request("GET")
        print(f"Login status={response.status_code}")

    def _request(self, method: str, **kwargs):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        headers.update(kwargs.pop("headers", {}))
        try:
            response = self.session.request(
                method,
                f"{self.base_url}/rest",
                headers=headers,
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
                **kwargs,
            )
        except requests.RequestException as error:
            raise NetLDError(f"Could not reach {self.base_url}.") from error

        if 300 <= response.status_code < 400:
            raise NetLDError(
                f"Request redirected to {response.headers.get('Location', '')}."
            )
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            raise NetLDError(f"Request failed with HTTP {response.status_code}.") from error
        return response

    def call(self, method: str, parameters: dict):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": parameters,
            "id": str(uuid.uuid4()),
        }
        if self.debug:
            print("Request JSON:")
            print(json.dumps(payload, indent=2))
        response = self._request(
            "POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        try:
            data = response.json()
        except ValueError as error:
            raise NetLDError(f"{method} returned invalid JSON.") from error
        if self.debug:
            print("Response JSON:")
            print(json.dumps(data, indent=2))
        if data.get("error"):
            raise NetLDError(json.dumps(data["error"]))
        return data.get("result")

    def get_configuration_change_log_page(
        self, network: str, ip_address: str, offset: int, page_size: int
    ) -> dict:
        result = self.call(
            "Configuration.retrieveSnapshotChangeLog",
            {
                "network": network,
                "ipAddress": ip_address,
                "pageData": {"offset": offset, "pageSize": page_size},
            },
        )
        if not isinstance(result, dict) or not isinstance(result.get("changeLogs"), list):
            raise NetLDError(
                "Configuration.retrieveSnapshotChangeLog returned an invalid page."
            )
        return result
