import os

from netld_example_client import NetLDClient, NetLDError, print_json


job_name = os.environ.get("NETLD_JOB_NAME")
if not job_name:
    raise NetLDError("Set NETLD_JOB_NAME to the exact name of the job to run.")

client = NetLDClient.from_env()
client.login()

page_data = client.search_available_jobs(
    networks=[os.environ.get("NETLD_NETWORK", "Default")],
    page_size=int(os.environ.get("NETLD_JOB_PAGE_SIZE", "100")),
)

matches = [
    job
    for job in (page_data or {}).get("jobData", [])
    if job.get("jobName") == job_name
]

if not matches:
    raise NetLDError(f'No available job named "{job_name}" was found.')
if len(matches) > 1:
    job_ids = ", ".join(str(job.get("jobId")) for job in matches)
    raise NetLDError(f'Multiple jobs named "{job_name}" were found: {job_ids}')

job_id = matches[0]["jobId"]
job_data = client.get_job(job_id)
if job_data is None:
    raise NetLDError(f"Scheduler.getJob returned no data for job ID {job_id}.")

print(f'Selected job "{job_name}" with ID {job_id}:')
print_json(job_data)

if os.environ.get("NETLD_RUN_JOB", "false").lower() != "true":
    print("Dry run only. Set NETLD_RUN_JOB=true to execute this job.")
else:
    execution = client.run_now(job_data)
    print("Execution started:")
    print_json(execution)
