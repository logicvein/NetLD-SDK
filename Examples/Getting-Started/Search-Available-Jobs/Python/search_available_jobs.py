import os

from netld_example_client import NetLDClient, print_available_jobs


client = NetLDClient.from_env()
client.login()

page_data = client.search_available_jobs(
    networks=[os.environ.get("NETLD_NETWORK", "Default")],
    offset=int(os.environ.get("NETLD_JOB_OFFSET", "0")),
    page_size=int(os.environ.get("NETLD_JOB_PAGE_SIZE", "100")),
    sort_column=os.environ.get("NETLD_JOB_SORT_COLUMN", ""),
    descending=os.environ.get("NETLD_JOB_DESCENDING", "false").lower() == "true",
)

print_available_jobs(page_data)
