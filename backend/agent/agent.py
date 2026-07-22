"""
The Investigation Agent Orchestrator.
Wraps the AgentCore Harness and the Deterministic Pipeline.
"""
from typing import List, Optional
from backend.agent.agentcore_adapter import AgentCoreAdapter
from backend.agent.planner.selector import SkillPlanner

class InvestigationAgent:
    """
    The main interactive endpoint.
    It orchestrates the Planner, initializes the Core Harness, and provides the strict 
    boundary preventing the LLM from interacting directly with deterministic APIs.
    """
    def __init__(self):
        self.harness = AgentCoreAdapter()
        self.planner = SkillPlanner()

    def handle_request(self, user_query: str, session_id: Optional[str] = None) -> str:
        """
        Handles the conversational interface.
        If session_id is None, it initiates a completely new investigation from scratch.
        If session_id is provided, it processes a follow-up interaction (Block 3).
        Returns the session_id so the client can continue the stateful conversation.
        """
        is_new_session = session_id is None
        
        if is_new_session:
            # 1. Initialize a new hygienic memory context
            session_id = self.harness.create_session(user_query)
            memory = self.harness.get_memory(session_id)
            
            # 2. Planning Phase
            skills_to_run = self.planner.select_skills(user_query)
            memory.executed_skills.extend(skills_to_run)
            
            # --- DETERMINISTIC EXECUTION BOUNDARY ---
            # 3. Invocation Phase
            # At this explicit boundary, the Agent passes control to the Deterministic Investigation Engine.
            # The LLM is forced to wait until the `OperationalReport` is returned.
            # (Mocked for structural architecture phase)
            
            memory.add_message("system", f"Engine executed sequence: {', '.join(skills_to_run)}")
            
            # 4. Agentic Summarization
            # Here, the LLM processes the returned OperationalReport and writes the human-readable reply.
            memory.add_message("agent", f"I have completed the investigation using {skills_to_run[0]}. How else can I help?")
            
        else:
            # Multi-turn interaction handling
            memory = self.harness.get_memory(session_id)
            memory.add_message("user", user_query)
            
            # Use the LLM strictly as a filter/summarizer over the existing report
            response = self._handle_followup(memory, user_query)
            
        return session_id

    def _handle_followup(self, memory, user_query: str) -> str:
        """
        Processes a multi-turn interaction strictly using the LLM for summarization/filtering.
        It must never restart the investigation or invent facts.
        """
        # In production, this invokes the LLM via an AWS Bedrock/Anthropic SDK.
        # The prompt injected physically restricts the LLM from inventing facts.
        llm_system_prompt = f"""
        You are an operational investigation orchestrator. 
        Your ONLY job is to filter, summarize, or explain the following frozen Operational Report.
        DO NOT invent evidence. DO NOT infer root causes not explicitly stated.
        If the user asks a question not covered by the report, state that you do not have the evidence.
        
        === FROZEN EVIDENCE ===
        Operational Report: {memory.operational_report}
        """
        
        # Mocking the LLM context filtering response for architectural demonstration
        query_lower = user_query.lower()
        
        if "sagemaker" in query_lower:
            response = "Filtering timeline: Found SageMaker events. I have extracted these exclusively from the existing Operational Report."
        elif "which task triggered" in query_lower or "why" in query_lower:
            response = "Based on the deterministic correlation graph in my memory, the events were triggered by the root cause stated in the report."
        else:
            response = "I have reviewed the Operational Report and summarized the findings based exactly on the provided evidence."
            
        memory.add_message("agent", response)
        return response

    def end_investigation(self, session_id: str):
        """Tears down the hygienic environment."""
        self.harness.end_session(session_id)
