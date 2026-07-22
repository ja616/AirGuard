from backend.investigation.models import InvestigationRequest, ClassifiedIncident, NormalizedEvidenceBundle
from backend.taxonomy.registry import INCIDENT_REGISTRY

MIN_CONFIDENCE_THRESHOLD = 0.2

def run(request: InvestigationRequest, bundle: NormalizedEvidenceBundle) -> ClassifiedIncident:
    scores = []
    
    for inc_id, definition in INCIDENT_REGISTRY.items():
        score = 0.0
        max_possible = sum(definition.classification_signals.values())
        
        if max_possible > 0:
            for signal_key, weight in definition.classification_signals.items():
                if bundle.signals.get(signal_key):
                    score += weight
                    
            confidence = score / max_possible
            if confidence >= MIN_CONFIDENCE_THRESHOLD:
                # Store tuple of (confidence, score, definition)
                scores.append((confidence, score, definition))
                
    # Sort descending by confidence, then by total score
    scores.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    if not scores:
        # Fallback to Task Failure
        return ClassifiedIncident(
            request=request, 
            definition=INCIDENT_REGISTRY["INC-EXEC-002"],
            classification_confidence=0.1
        )
        
    primary_conf, primary_score, primary_def = scores[0]
    
    secondary_def = None
    secondary_conf = 0.0
    supporting = []
    rejected = []
    
    if len(scores) > 1:
        sec_conf, sec_score, sec_def = scores[1]
        if sec_conf >= 0.3:
            secondary_def = sec_def
            secondary_conf = sec_conf
        
    for i in range(2, len(scores)):
        supporting.append(scores[i][2].name)
        
    # Anyone who scored 0 or wasn't even evaluated
    for inc_id, definition in INCIDENT_REGISTRY.items():
        if inc_id != primary_def.id and (not secondary_def or inc_id != secondary_def.id):
            if definition.name not in supporting:
                rejected.append(definition.id)
                
    return ClassifiedIncident(
        request=request,
        definition=primary_def,
        classification_confidence=primary_conf,
        secondary_definition=secondary_def,
        secondary_confidence=secondary_conf,
        supporting_factors=supporting,
        rejected_classes=rejected
    )
