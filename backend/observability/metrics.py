import time
from collections import defaultdict
from typing import Dict, Any
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

# Global in-memory metrics registry for Prometheus formatting
metrics_registry = {
    "counters": defaultdict(int),
    "histograms": defaultdict(list)
}

def increment_counter(name: str, labels: Dict[str, str] = None, value: int = 1):
    label_str = ",".join(f'{k}="{v}"' for k, v in (labels or {}).items())
    key = f"{name}{{{label_str}}}" if label_str else name
    metrics_registry["counters"][key] += value

def observe_histogram(name: str, value: float, labels: Dict[str, str] = None):
    label_str = ",".join(f'{k}="{v}"' for k, v in (labels or {}).items())
    key = f"{name}{{{label_str}}}" if label_str else name
    metrics_registry["histograms"][key].append(value)
    # Keep last 1000 items to avoid memory leak locally
    if len(metrics_registry["histograms"][key]) > 1000:
        metrics_registry["histograms"][key] = metrics_registry["histograms"][key][-1000:]

router = APIRouter(tags=["observability"])

@router.get("/metrics", response_class=PlainTextResponse)
def get_metrics():
    lines = []
    
    # Format counters
    for key, val in metrics_registry["counters"].items():
        base_name = key.split("{")[0]
        lines.append(f"# TYPE {base_name} counter")
        lines.append(f"{key} {val}")
        
    # Format histograms (simplistic sum/count approach for Prometheus compatibility)
    for key, values in metrics_registry["histograms"].items():
        base_name = key.split("{")[0]
        lines.append(f"# TYPE {base_name} histogram")
        count = len(values)
        total = sum(values)
        # Handle label injection for _sum and _count
        if "{" in key:
            name, labels = key.split("{", 1)
            lines.append(f"{name}_sum{{{labels} {total}")
            lines.append(f"{name}_count{{{labels} {count}")
        else:
            lines.append(f"{key}_sum {total}")
            lines.append(f"{key}_count {count}")
        
    return "\n".join(lines) + "\n"
