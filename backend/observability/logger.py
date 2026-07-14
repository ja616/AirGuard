import logging
import json
import uuid
import contextvars
from datetime import datetime

# Context variable for trace tracking
trace_id_var = contextvars.ContextVar("trace_id", default="")
investigation_id_var = contextvars.ContextVar("investigation_id", default="")

def get_trace_id() -> str:
    tid = trace_id_var.get()
    if not tid:
        tid = str(uuid.uuid4())
        trace_id_var.set(tid)
    return tid

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get(),
            "investigation_id": investigation_id_var.get(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name: str = "airguard"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        # Prevent propagation to the root logger to avoid duplicate logs in standard format
        logger.propagate = False
        
    return logger

logger = setup_logger()
