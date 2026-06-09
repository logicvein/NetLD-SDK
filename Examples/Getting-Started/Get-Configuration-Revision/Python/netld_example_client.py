import json
import os
import uuid
import base64
import binascii

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
        data = response.json()

        if self.debug:
            print("Response JSON:")
            print(json.dumps(data, indent=2))

        if data.get("error"):
            raise NetLDError(data["error"])

        return data.get("result")

    def get_configuration_history(
        self,
        networks,
        scheme,
        data,
        offset=0,
        page_size=100,
        sort_column="session",
        descending=True,
    ):
        if isinstance(networks, str):
            networks = [networks]

        return self.call(
            "Configuration.retrieveConfigHistory",
            pageData={
                "offset": offset,
                "pageSize": page_size,
                "total": 0,
                "configHistoryItems": [],
            },
            networks=list(networks),
            scheme=scheme,
            data=data,
            sortColumn=sort_column,
            descending=descending,
        )

    def retrieve_revision(self, network, ip_address, config_path, timestamp):
        return self.call(
            "Configuration.retrieveRevision",
            network=network,
            ipAddress=ip_address,
            configPath=config_path,
            timestamp=timestamp,
        )


def decode_revision_content(revision):
    content = revision.get("content")
    if not content:
        return None

    try:
        decoded = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as error:
        raise NetLDError("Revision content is not valid Base64.") from error

    if not (revision.get("mimeType") or "").startswith("text/"):
        return None

    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError as error:
        raise NetLDError("Text revision content is not valid UTF-8.") from error
