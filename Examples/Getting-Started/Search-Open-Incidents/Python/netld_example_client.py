import json
import os
import uuid

import requests
from dotenv import load_dotenv


class NetLDError(RuntimeError):
    pass


class NetLDClient:
    def __init__(self, base_url, api_key, timeout=10, debug=False):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.debug = debug
        self.session = requests.Session()

    @classmethod
    def from_env(cls):
        load_dotenv()

        base_url = os.environ.get("NETLD_BASE_URL")
        api_key = os.environ.get("NETLD_API_KEY")
        debug = os.environ.get("NETLD_DEBUG") == "1"

        if not base_url:
            raise NetLDError("Set NETLD_BASE_URL in .env before running this example.")
        if not api_key:
            raise NetLDError("Set NETLD_API_KEY before running this example.")

        return cls(base_url, api_key, debug=debug)

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def login(self):
        try:
            response = self.session.get(
                f"{self.base_url}/rest",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise NetLDError(
                f"Could not reach {self.base_url}. Check NETLD_BASE_URL in your .env file."
            ) from error

        if response.is_redirect:
            location = response.headers.get("Location", "")
            raise NetLDError(
                "Login redirected instead of returning a netLD session. "
                f"Redirect target: {location}"
            )

        response.raise_for_status()
        print(f"Login status={response.status_code}")

        if self.debug:
            print(f"Cookies={self.session.cookies.get_dict()}")

    def call(self, method, **params):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": str(uuid.uuid4()),
        }

        if self.debug:
            print("Request JSON:")
            print(json.dumps(payload, indent=2))

        try:
            response = self.session.post(
                f"{self.base_url}/rest",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise NetLDError(
                f"Could not reach {self.base_url}. Check NETLD_BASE_URL in your .env file."
            ) from error

        if response.is_redirect:
            location = response.headers.get("Location", "")
            raise NetLDError(
                "API call redirected instead of returning JSON-RPC data. "
                f"Redirect target: {location}"
            )

        response.raise_for_status()
        if not response.text.strip():
            return None

        data = response.json()

        if data is None:
            return None

        if self.debug:
            print("Response JSON:")
            print(json.dumps(data, indent=2))

        if data.get("error"):
            raise NetLDError(data["error"])

        return data.get("result")

    def search_open_incidents(
        self,
        network,
        offset=0,
        page_size=100,
        sort_column="modified",
        descending=False,
    ):
        return self.call(
            "Incidents.searchIncidents",
            pageData={
                "offset": offset,
                "total": 0,
                "pageSize": page_size,
                "incidents": [],
            },
            queries=[
                "status=OPEN,WORKING",
                f"networks={network}",
            ],
            sortColumn=sort_column,
            descending=descending,
        )


def print_incidents(page_data):
    if page_data is None:
        print("No incident data returned. Incidents.searchIncidents is available only on ThirdEye.")
        return

    print(json.dumps(page_data, indent=2))
