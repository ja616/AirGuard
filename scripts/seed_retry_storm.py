import requests
import time

AIRFLOW_API = "http://localhost:8080/api/v1"
AUTH = ("admin", "admin")
DAG_ID = "data_pipeline_etl"

print(f"Triggering {DAG_ID} to simulate a retry storm...")

for i in range(5):
    print(f"Triggering run {i+1}...")
    resp = requests.post(
        f"{AIRFLOW_API}/dags/{DAG_ID}/dagRuns",
        auth=AUTH,
        json={"conf": {}}
    )
    if resp.status_code in [200, 201]:
        print(f"Run {i+1} queued successfully.")
    else:
        print(f"Failed to queue run: {resp.status_code} {resp.text}")
        
    time.sleep(1)
    
print("All 5 runs triggered. Wait about 30 seconds for Airflow to process them and create the retry storm, then run the investigation!")
