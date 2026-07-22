"""
AgentCore Tool Execution Layer — AirGuard
==========================================
Defines ToolExecutorProtocol and AgentCoreToolExecutor.

AgentCoreToolExecutor is the direct local execution path:
  - Used when AGENTCORE_HARNESS_ID is not set (local dev).
  - Used inside the AgentCore inline tool loop to execute individual tool calls.

Future extensibility:
  When an MCP Gateway or Lambda is deployed, implement MCPGatewayToolExecutor
  satisfying ToolExecutorProtocol. Swap in AgentCoreAdapter.__init__ via env-var.
  No other code changes required.
"""
import concurrent.futures
from typing import List, Protocol, runtime_checkable
from datetime import datetime, timezone
import time
from backend.investigation.models import InvestigationRequest
from backend.evidence.models import EvidenceBundleResult, Evidence, ToolFailure

try:
    from backend.tools.registry import TOOL_REGISTRY
except ImportError:
    TOOL_REGISTRY = {}


@runtime_checkable
class ToolExecutorProtocol(Protocol):
    """
    Interface all tool executors must satisfy.
    Any class implementing this can be used as the tool execution layer
    in AgentCoreAdapter without modifying the adapter.
    """
    def run(self, tools: List[str], request: InvestigationRequest) -> EvidenceBundleResult:
        ...


class AgentCoreToolExecutor:
    """
    Executes AirGuard evidence tools registered in TOOL_REGISTRY in parallel.

    Implements ToolExecutorProtocol — the same contract a future
    MCPGatewayToolExecutor or LambdaToolExecutor will satisfy, allowing
    hot-swapping without modifying AgentCoreAdapter.

    Also used as the inline executor inside the AgentCore Harness tool loop:
    when the Harness LLM emits a toolUse event, the adapter calls
    `execute_single(tool_name, request)` to run it client-side.
    """

    def run(self, tools: List[str], request: InvestigationRequest) -> EvidenceBundleResult:
        """Run all tools in parallel. Used for the direct (no-Harness) path."""
        results: List[Evidence] = []
        failures: List[ToolFailure] = []
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = {}
            for tool_name in tools:
                if tool_name in TOOL_REGISTRY:
                    futures[pool.submit(TOOL_REGISTRY[tool_name], request)] = tool_name
                else:
                    failures.append(ToolFailure(
                        tool=tool_name,
                        reason="Tool not found in registry",
                        timestamp=datetime.now(timezone.utc)
                    ))

            for future in concurrent.futures.as_completed(futures):
                tool_name = futures[future]
                try:
                    evidence = future.result(timeout=30)
                    if evidence:
                        results.append(evidence)
                except Exception as e:
                    failures.append(ToolFailure(
                        tool=tool_name,
                        reason=str(e),
                        timestamp=datetime.now(timezone.utc)
                    ))

        duration_ms = int((time.time() - start_time) * 1000)
        return EvidenceBundleResult(
            evidence=results,
            failures=failures,
            collection_duration_ms=duration_ms
        )

    def execute_single(self, tool_name: str, request: InvestigationRequest) -> Evidence:
        """
        Execute a single named tool. Used by the AgentCore inline tool loop
        when the Harness LLM emits a toolUse event for a specific tool.
        Raises on failure — the caller is responsible for catching and recording ToolFailure.
        """
        if tool_name not in TOOL_REGISTRY:
            raise ValueError(f"Tool '{tool_name}' is not registered in TOOL_REGISTRY")
        return TOOL_REGISTRY[tool_name](request)
