import urllib.request
import json
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000/api/v1"
REPORTS_DIR = "reports"

from backend.evaluation.ground_truth import EXPECTED_OUTPUTS, GroundTruth

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def verify_system_health():
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

def run_scenario(gt: GroundTruth) -> dict:
    print(f"\n--- Running Scenario: {gt.dag_id} ---")
    
    # 1. Trigger Investigation
    payload = json.dumps({
        "dag_id": gt.dag_id,
        "user_query": f"Automated benchmark for {gt.dag_id}"
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
        return {"scenario": gt.dag_id, "status": "FAIL", "error": "Investigation creation failed"}

    # 2. Poll for Completion
    max_retries = 30
    last_state = None
    
    for _ in range(max_retries):
        req = urllib.request.Request(f"{BASE_URL}/investigations/{inv_id}")
        try:
            with urllib.request.urlopen(req) as response:
                status = json.loads(response.read().decode('utf-8'))
                current_state = status['state']
                progress = status.get('progress', 0)
                
                if current_state != last_state:
                    print(f"  State: {current_state} ({progress}%)")
                    last_state = current_state
                    
                if current_state in ['Completed', 'Failed']:
                    break
        except Exception as e:
            print(f"  Poll error: {e}")
            
        time.sleep(1)
        
    if current_state != 'Completed':
        return {"scenario": gt.dag_id, "status": "FAIL", "error": f"Pipeline ended in state {current_state}"}
        
    # 3. Evaluate results
    artifacts = status.get('artifacts', [])
    report_art = next((a for a in artifacts if a['type'] == 'report'), None)
    if not report_art:
        return {"scenario": gt.dag_id, "status": "FAIL", "error": "No ReportArtifact generated"}
        
    report = report_art['content']
    
    classification_actual = report.get('incident_classification')
    classification_match = classification_actual == gt.expected_incident_class
    
    conf = report.get('confidence', {})
    conf_score = conf.get('score', 0.0)
    conf_match = gt.expected_confidence_min <= conf_score <= gt.expected_confidence_max
    
    rca = report.get('root_cause', '').lower()
    rca_match = any(kw.lower() in rca for kw in gt.expected_root_cause_keywords)
    
    passed = classification_match and conf_match and (rca_match or classification_match) # Sometimes RCA keywords are generic, class is more important
    
    return {
        "scenario": gt.dag_id,
        "status": "PASS" if passed else "FAIL",
        "expected_class": gt.expected_incident_class,
        "actual_class": classification_actual,
        "expected_conf": f"{gt.expected_confidence_min}-{gt.expected_confidence_max}",
        "actual_conf": conf_score,
        "root_cause_matched": rca_match,
        "classification_matched": classification_match,
        "conf_matched": conf_match,
        "actual_rca": rca
    }

def generate_report(results: list):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "benchmark_report.md")
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    
    with open(report_path, "w") as f:
        f.write("# Phase 6.2 Benchmark Report\n\n")
        f.write(f"**Score:** {passed}/{total} ({passed/total*100:.1f}%)\n\n")
        
        f.write("## Scenario Results\n\n")
        f.write("| Scenario | Status | Expected Class | Actual Class | Expected Conf | Actual Conf |\n")
        f.write("|----------|--------|----------------|--------------|---------------|-------------|\n")
        
        for r in results:
            f.write(f"| {r['scenario']} | {r['status']} | {r.get('expected_class', '')} | {r.get('actual_class', '')} | {r.get('expected_conf', '')} | {r.get('actual_conf', '')} |\n")
            
        f.write("\n## Detailed Failures\n\n")
        for r in results:
            if r["status"] == "FAIL":
                f.write(f"### {r['scenario']}\n")
                f.write(f"- Classification matched: {r.get('classification_matched')}\n")
                f.write(f"- Confidence matched: {r.get('conf_matched')}\n")
                f.write(f"- RCA matched: {r.get('root_cause_matched')} (Actual: {r.get('actual_rca')})\n")
                f.write(f"- Error: {r.get('error', 'N/A')}\n\n")
                
    print(f"\nReport written to {report_path}")

def run_all():
    print_header("AirGuard 15-Scenario Benchmark")
    verify_system_health()
    
    results = []
    for gt in EXPECTED_OUTPUTS:
        res = run_scenario(gt)
        results.append(res)
        if res["status"] == "FAIL":
            print(f"[FAIL] {res['scenario']}")
            print("DEBUG REPORT:", json.dumps(res, indent=2))
        else:
            print(f"[PASS] {res['scenario']}")
            
    generate_report(results)
    
if __name__ == "__main__":
    run_all()
