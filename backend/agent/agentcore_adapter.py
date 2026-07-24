"""
AgentCore Adapter — AirGuard
============================
Bridges the Deterministic Capability Planner with the Amazon Bedrock
AgentCore Harness via the inline function tool execution model.

Pipeline:
    InvestigationRequest
        → Deterministic Planner (capability list + tool names)
        → AgentCore invoke_harness (with inline tool definitions)
            ↔ Inline Tool Loop (client-side execution):
                Harness LLM emits toolUse events
                FastAPI backend executes tools locally
                Results returned to Harness to continue reasoning
        → EvidenceBundleResult
        → Deterministic Investigation Engine
        → OperationalReport

When AGENTCORE_HARNESS_ID is not set, evidence tools run directly via
AgentCoreToolExecutor without an LLM orchestration loop.
"""
import uuid
import os
import json
import boto3
import time
from datetime import datetime, timezone
from typing import Dict, Callable, Optional, Union, List, Any

from backend.agent.harness.memory import InvestigationMemory
from backend.investigation.models import InvestigationRequest, OperationalReport
from backend.domain.investigation import InvestigationState, ArtifactType, EvidenceArtifact
from backend.agent.planner.selector import InvestigationPlanner
from backend.agent.executor import AgentCoreToolExecutor
from backend.investigation.pipeline import DeterministicInvestigationEngine
from backend.evidence.models import EvidenceBundleResult, ToolFailure

try:
    from backend.tools.registry import TOOL_REGISTRY
except ImportError:
    TOOL_REGISTRY = {}


class AgentCoreAdapter:
    """
    Adapter for Amazon Bedrock AgentCore Harness.

    Orchestrates investigations using the inline function model:
    - The AirGuard Deterministic Planner provides the capability list.
    - The AgentCore Harness LLM selects and sequences tool calls from that list.
    - This backend executes each tool call client-side (inline) and returns results.
    - The Deterministic Engine performs all reasoning on the collected evidence.
    """

    def __init__(self):
        self.active_sessions: Dict[str, InvestigationMemory] = {}
        self.planner = InvestigationPlanner()
        self.tool_executor = AgentCoreToolExecutor()
        self.pipeline = DeterministicInvestigationEngine()

    # ─────────────────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────────────────

    def create_session(self, initial_query: str) -> str:
        session_id = str(uuid.uuid4())
        memory = InvestigationMemory(
            session_id=session_id,
            original_query=initial_query
        )
        memory.add_message("user", initial_query)
        self.active_sessions[session_id] = memory
        return session_id

    def get_memory(self, session_id: str) -> InvestigationMemory:
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found or has expired.")
        return self.active_sessions[session_id]

    def end_session(self, session_id: str) -> None:
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def _build_prompt(self, request) -> str:
        """
        Build a structured, fact-rich LLM prompt from IncidentContext when available,
        falling back to the derived reported_symptom for legacy requests.
        """
        ctx = getattr(request, "incident_context", None)

        if ctx is None:
            # Legacy path — plain text
            return (
                f"You are an evidence collection agent for a workflow investigation. "
                f"The workflow under investigation is '{request.dag_id}'. "
                f"The reported symptom is: '{request.reported_symptom or 'unspecified'}'. "
                f"Your task is to call the available evidence tools to gather diagnostic data. "
                f"Call each relevant tool once. Do NOT perform root cause analysis or speculate. "
                f"Return only tool calls."
            )

        # Structured path — build from IncidentContext fields
        lines = [
            "You are an evidence collection agent for a workflow investigation.",
            "",
            f"  Workflow:          {ctx.workflow_id}",
            f"  Environment:       {ctx.environment}",
            f"  Severity:          {ctx.severity.value.upper()}",
            f"  Investigation goal: {ctx.investigation_goal.value}",
            f"  Triggered by:      {ctx.trigger_source.value}",
            f"  At:                {ctx.execution_timestamp.isoformat()}",
        ]
        if ctx.workflow_execution_id:
            lines.append(f"  Execution ID:      {ctx.workflow_execution_id}")
        if ctx.failed_node_id:
            retry_info = f", attempt {ctx.retry_number}" if ctx.retry_number else ""
            lines.append(
                f"  Failed node:       '{ctx.failed_node_id}' "
                f"(state: {ctx.execution_state or 'failed'}{retry_info})"
            )
        if ctx.orchestrator_error_type:
            lines.append(f"  Error type:        {ctx.orchestrator_error_type}")
        if ctx.additional_context.get("exception"):
            lines.append(f"  Exception:         {ctx.additional_context['exception'][:200]}")

        lines += [
            "",
            "Instructions:",
            "  - Call the available evidence tools to collect diagnostic data.",
            "  - Focus your tool selection on the failing node and its execution window.",
            "  - Call each relevant tool exactly once.",
            "  - Do NOT perform root cause analysis or speculate about causes.",
            "  - Collect facts only. Return only tool calls.",
        ]
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Main Investigation Entry Point
    # ─────────────────────────────────────────────────────────────────────────

    def run_investigation(
        self,
        request: InvestigationRequest,
        state_callback: Optional[Callable[[InvestigationState, int, Optional[Union[ArtifactType, List[ArtifactType]]]], None]] = None
    ) -> OperationalReport:

        if state_callback:
            state_callback(InvestigationState.STARTING, 5, None)

        # ── Step 1: Deterministic Planning ──────────────────────────────────
        plan = self.planner.build_plan(request)
        print(f"[Planner] Profile: {plan.skill} | Tools: {plan.estimated_tools}")

        # ── Step 2: Agentic Evidence Collection ─────────────────────────────
        if state_callback:
            state_callback(InvestigationState.COLLECTING_EVIDENCE, 20, None)

        harness_id = os.environ.get("AGENTCORE_HARNESS_ID")

        if harness_id:
            print(f"[AgentCore] Harness configured. Starting inline tool loop...")
            try:
                evidence_result = self._run_inline_tool_loop(harness_id, plan.estimated_tools, request)
            except Exception as e:
                print(f"[AgentCore] Harness failed ({type(e).__name__}: {e}). Falling back to direct tool execution.")
                evidence_result = self.tool_executor.run(plan.estimated_tools, request)
        else:
            print("[AgentCore] No AGENTCORE_HARNESS_ID. Running tools directly.")
            evidence_result = self.tool_executor.run(plan.estimated_tools, request)

        # ── Step 3: Emit Evidence Artifact ──────────────────────────────────
        if state_callback:
            ev_art = EvidenceArtifact(
                id=str(uuid.uuid4()),
                collected=[e.model_dump() for e in evidence_result.evidence]
            )
            state_callback(InvestigationState.COLLECTING_EVIDENCE, 25, [ev_art])

        # ── Step 4: Deterministic Pipeline ──────────────────────────────────
        if state_callback:
            state_callback(InvestigationState.NORMALIZING_EVIDENCE, 35, None)

        report = self.pipeline.execute_with_evidence(request, plan, evidence_result, state_callback)
        return report

    # ─────────────────────────────────────────────────────────────────────────
    # AgentCore Inline Function Tool Loop
    # ─────────────────────────────────────────────────────────────────────────

    def _build_inline_tool_definitions(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """
        Build tool schemas for AgentCore inline function registration.
        Only tools that exist in TOOL_REGISTRY are exposed to the LLM.
        The planner determines which tools are in scope — the LLM picks which to call.

        Tool descriptions live in tools/schemas.py (single source of truth).
        Adding a new tool: edit tools/registry.py + tools/schemas.py — not here.
        """
        from backend.tools.schemas import TOOL_DESCRIPTIONS

        definitions = []
        for name in tool_names:
            if name in TOOL_REGISTRY:
                definitions.append({
                    "type": "inline_function",
                    "name": name,
                    "config": {
                        "inlineFunction": {
                            "description": TOOL_DESCRIPTIONS.get(
                                name, f"Collect {name.replace('_', ' ')} evidence."
                            ),
                            "inputSchema": {
                                "json": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        }
                    }
                })
        return definitions

    def _parse_harness_stream(self, event_stream) -> tuple:
        """
        Parse the invoke_harness streaming response.

        Returns:
            assistant_content (List[dict]): Content blocks for the assistant turn.
            tool_calls (List[dict]): Each tool call as {id, name, input}.
        """
        assistant_content = []
        tool_calls = []
        current_tool_use = None
        current_tool_input_json = ""

        try:
            for event in event_stream:
                print(f"[AgentCore Stream Event] {event}")
                # ── Text chunk ──
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})
                    if "text" in delta:
                        if not assistant_content or "text" not in assistant_content[-1]:
                            assistant_content.append({"type": "text", "text": delta["text"]})
                        else:
                            assistant_content[-1]["text"] += delta["text"]
                    elif "toolUse" in delta:
                        current_tool_input_json += delta["toolUse"].get("input", "")

                # ── Tool use block started ──
                elif "contentBlockStart" in event:
                    start = event["contentBlockStart"].get("start", {})
                    if "toolUse" in start:
                        current_tool_use = {
                            "type": "tool_use",
                            "toolUseId": start["toolUse"]["toolUseId"],
                            "name": start["toolUse"]["name"],
                            "input": {}
                        }
                        current_tool_input_json = ""

                # ── Tool use block ended ──
                elif "contentBlockStop" in event:
                    if current_tool_use is not None:
                        try:
                            parsed_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
                        except json.JSONDecodeError:
                            parsed_input = {}
                        current_tool_use["input"] = parsed_input
                        assistant_content.append(current_tool_use)
                        tool_calls.append({
                            "id": current_tool_use["toolUseId"],
                            "name": current_tool_use["name"],
                            "input": parsed_input
                        })
                        current_tool_use = None

                # ── Stream end ──
                elif "messageStop" in event:
                    break

        except Exception as e:
            print(f"[AgentCore] Stream parsing error: {e}")
            raise e

        return assistant_content, tool_calls

    def _run_inline_tool_loop(
        self,
        harness_id: str,
        tool_names: List[str],
        request: InvestigationRequest
    ) -> EvidenceBundleResult:
        """
        Execute the AgentCore inline function tool loop.

        The Harness LLM selects which tools to call. This backend executes
        them client-side (inline) and feeds results back. Loop continues
        until the LLM signals completion.
        """
        from backend.integrations.aws.client_factory import get_boto3_client
        client = get_boto3_client("bedrock-agentcore")

        tool_definitions = self._build_inline_tool_definitions(tool_names)

        prompt = self._build_prompt(request)


        messages = [{"role": "user", "content": [{"text": prompt}]}]
        collected_evidence = []
        collected_failures = []
        max_iterations = 5  # safety bound

        for iteration in range(max_iterations):
            print(f"[AgentCore] Tool loop iteration {iteration + 1}/{max_iterations}")

            response = client.invoke_harness(
                harnessArn=harness_id,
                runtimeSessionId=request.investigation_id,
                model={"bedrockModelConfig": {"modelId": "us.amazon.nova-pro-v1:0"}},
                messages=messages,
                tools=tool_definitions
            )

            assistant_content, tool_calls = self._parse_harness_stream(response["stream"])

            if not tool_calls:
                print(f"[AgentCore] No tool calls in iteration {iteration + 1}. Loop complete.")
                break

            print(f"[AgentCore] LLM requested {len(tool_calls)} tool(s): {[tc['name'] for tc in tool_calls]}")

            # Execute each tool inline (client-side)
            tool_results = []
            for tc in tool_calls:
                tool_name = tc["name"]
                try:
                    evidence = self.tool_executor.execute_single(tool_name, request)
                    if evidence:
                        collected_evidence.append(evidence)
                        result_text = json.dumps(evidence.normalized_payload, default=str)
                        print(f"[AgentCore] ✓ {tool_name} executed successfully")
                    else:
                        result_text = "Tool returned no data."
                except Exception as e:
                    err = str(e)
                    print(f"[AgentCore] ✗ {tool_name} failed: {err}")
                    collected_failures.append(ToolFailure(
                        tool=tool_name,
                        reason=err,
                        timestamp=datetime.now(timezone.utc)
                    ))
                    result_text = f"Error: {err}"

                tool_results.append({
                    "toolResult": {
                        "toolUseId": tc["id"],
                        "content": [{"text": result_text}]
                    }
                })

            # Continue the conversation with tool results
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        print(f"[AgentCore] Loop complete. Collected {len(collected_evidence)} evidence items, "
              f"{len(collected_failures)} failures.")

        return EvidenceBundleResult(
            evidence=collected_evidence,
            failures=collected_failures,
            collection_duration_ms=0
        )
