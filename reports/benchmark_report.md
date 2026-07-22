# Phase 6.2 Benchmark Report

**Score:** 15/15 (100.0%)

## Scenario Results

| Scenario | Status | Expected Class | Actual Class | Expected Conf | Actual Conf |
|----------|--------|----------------|--------------|---------------|-------------|
| retry_storm_dag | PASS | INC-EXEC-001 | INC-EXEC-001 | 0.45-1.0 | 0.5 |
| dependency_failure_dag | PASS | INC-DEP-001 | INC-DEP-001 | 0.45-1.0 | 0.55 |
| unexpected_dag_explosion_dag | PASS | INC-EXEC-002 | INC-EXEC-002 | 0.45-1.0 | 0.55 |
| lambda_failure_dag | PASS | INC-CLD-001 | INC-CLD-001 | 0.6-1.0 | 0.9 |
| long_running_task_dag | PASS | INC-EXEC-003 | INC-EXEC-003 | 0.45-1.0 | 0.55 |
| scheduler_failure_dag | PASS | INC-SCHED-001 | INC-SCHED-001 | 0.45-1.0 | 0.55 |
| schedule_misconfig_dag | PASS | INC-SCHED-002 | INC-SCHED-002 | 0.45-1.0 | 0.55 |
| manual_trigger_storm_dag | PASS | INC-OPS-001 | INC-OPS-001 | 0.45-1.0 | 0.55 |
| backfill_storm_dag | PASS | INC-SCHED-003 | INC-SCHED-003 | 0.45-1.0 | 0.55 |
| resource_contention_dag | PASS | INC-EXEC-004 | INC-EXEC-004 | 0.45-1.0 | 0.6 |
| silent_data_failure_dag | PASS | INC-DATA-001 | INC-DATA-001 | 0.45-1.0 | 0.55 |
| partial_recovery_dag | PASS | INC-REC-001 | INC-REC-001 | 0.45-1.0 | 0.55 |
| sagemaker_cost_spike_dag | PASS | INC-COST-001 | INC-COST-001 | 0.45-1.0 | 0.9 |
| excessive_parallelism_dag | PASS | INC-OPS-002 | INC-OPS-002 | 0.45-1.0 | 0.5 |
| dag_pause_resume_dag | PASS | INC-OPS-003 | INC-OPS-003 | 0.45-1.0 | 0.55 |

## Detailed Failures

