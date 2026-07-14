import urllib.request
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def verify():
    print_header("AirGuard Pipeline Verification")
    
    # 1. Check Health
    print("Checking system health...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req) as response:
            health = json.loads(response.read().decode('utf-8'))
            print(f"Overall Status: {health['status']}")
            if health['status'] == 'Unavailable':
                print("System unavailable. Aborting.")
                sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

    # 2. Trigger Investigation
    print("\nTriggering Investigation...")
    payload = json.dumps({
        "dag_id": "lambda_failure_dag",
        "user_query": "Automated verification"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/investigations/", 
        data=payload, 
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer test'}, 
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            inv = json.loads(response.read().decode('utf-8'))
            inv_id = inv['id']
            print(f"Investigation created: {inv_id}")
    except Exception as e:
        print(f"Failed to create investigation: {e}")
        sys.exit(1)

    # 3. Poll for Completion
    print("\nPolling progress...")
    max_retries = 30
    last_state = None
    
    for _ in range(max_retries):
        req = urllib.request.Request(f"{BASE_URL}/investigations/{inv_id}")
        with urllib.request.urlopen(req) as response:
            status = json.loads(response.read().decode('utf-8'))
            current_state = status['state']
            progress = status.get('progress', 0)
            
            if current_state != last_state:
                print(f"State: {current_state} ({progress}%)")
                last_state = current_state
                
            if current_state in ['Completed', 'Failed']:
                break
                
        time.sleep(1)
        
    print_header("Results")
    if current_state == 'Completed':
        print("[SUCCESS] Pipeline succeeded!")
        print(f"Duration: {status['metadata'].get('duration_seconds', 0)} seconds")
        print(f"Artifacts generated: {len(status.get('artifacts', []))}")
        for art in status.get('artifacts', []):
            print(f" - {art['type']}")
    else:
        print(f"[FAIL] Pipeline failed with state: {current_state}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
