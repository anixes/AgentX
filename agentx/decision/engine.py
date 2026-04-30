import json
import logging
import os
from typing import Dict, Any, List
from scripts.core.gateway import UnifiedGateway

logger = logging.getLogger("agentx.decision")

class DecisionEngine:
    """
    LLM-assisted decision engine for AgentX.
    Determines the best execution path for a given objective.
    """
    
    SYSTEM_PROMPT = """
    You are a decision engine. You DO NOT execute tasks.
    You ONLY choose the best execution path.

    Available actions:
    * SKILL: use existing skill (best for exact matches or high-confidence variations)
    * COMPOSE: chain multiple skills (best for multi-step complex objectives)
    * NEW: run normal execution (fallback to SwarmEngine for unknown/novel tasks)
    * ASK: request clarification from user (for ambiguous or missing info)
    * REJECT: objective is unsafe, malicious, or clearly invalid

    Return JSON only in the following format:
    {
      "type": "SKILL | COMPOSE | NEW | ASK | REJECT",
      "confidence": float (0.0 to 1.0),
      "reason": "short explanation of why this path was chosen"
    }
    """

    def __init__(self):
        try:
            self.gateway = UnifiedGateway()
        except Exception:
            self.gateway = None

    def decide(self, objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide the execution path based on objective and context.
        """
        if not self.gateway or not self.gateway.api_key:
            logger.warning("No LLM gateway available. Falling back to NEW.")
            return {"type": "NEW", "confidence": 1.0, "reason": "No LLM gateway configured."}

        # --- Decision Feedback (Phase 10 Self-Improvement) ---
        feedback_stats = {}
        similar_decisions = []
        try:
            from agentx.decision.feedback import get_feedback_stats, get_similar_decisions
            feedback_stats = get_feedback_stats(objective)
            context["feedback_stats"] = feedback_stats
            
            # Phase 10 - Long term memory
            similar_decisions = get_similar_decisions(objective)
            if similar_decisions:
                print(f"[Decision] DECISION_MEMORY_USED: Found {len(similar_decisions)} similar past decisions.")
                context["similar_decisions"] = similar_decisions
        except ImportError:
            pass

        prompt = self._build_prompt(objective, context)
        
        try:
            # Using a cheap model for decision making
            raw_response = self.gateway.chat(
                model="gpt-4o-mini",
                prompt=prompt,
                system=self.SYSTEM_PROMPT
            )
            
            decision = self._parse_and_validate(raw_response, context)

            # --- Apply Biasing Logic ---
            if feedback_stats and decision["type"] in feedback_stats:
                stats = feedback_stats[decision["type"]]
                # IF same decision_type failed ≥ 2 times: penalize confidence
                if stats["FAILURE"] >= 2:
                    old_conf = decision["confidence"]
                    decision["confidence"] = max(0.0, decision["confidence"] - 0.3)
                    decision["reason"] += f" (Penalized from {old_conf} due to repeated failure)"
                    print(f"[Decision] BIAS APPLIED: Penalized {decision['type']} due to {stats['FAILURE']} failures.")
                
                # IF same decision_type succeeded: boost confidence
                if stats["SUCCESS"] > 0:
                    decision["confidence"] = min(1.0, decision["confidence"] + 0.1)
                    print(f"[Decision] BIAS APPLIED: Boosted {decision['type']} due to prior success.")

            # --- Apply Long-term Memory Biasing ---
            if similar_decisions:
                sim_fails = sum(1 for s in similar_decisions if s["decision_type"] == decision["type"] and s["outcome"] == "FAILURE")
                sim_success = sum(1 for s in similar_decisions if s["decision_type"] == decision["type"] and s["outcome"] == "SUCCESS")
                
                if sim_fails >= 2:
                    print(f"[Decision] DECISION_PATTERN_DETECTED: Repeated similar failures for {decision['type']}.")
                    decision["confidence"] = max(0.0, decision["confidence"] - 0.2)
                elif sim_success > 0:
                    print(f"[Decision] DECISION_PATTERN_DETECTED: Repeated similar success for {decision['type']}.")
                    decision["confidence"] = min(1.0, decision["confidence"] + 0.1)

            return decision
        except Exception as e:
            logger.error(f"Decision engine failure: {str(e)}")
            return {"type": "NEW", "confidence": 0.0, "reason": f"Error: {str(e)}"}

    def _build_prompt(self, objective: str, context: Dict[str, Any]) -> str:
        skills = context.get("top_skills", [])
        history = context.get("task_history", [])
        risk = context.get("risk_level", "LOW")
        feedback = context.get("feedback_stats", {})
        
        prompt = f"Objective: {objective}\n"
        prompt += f"Risk Level: {risk}\n\n"
        
        if feedback:
            prompt += "Previous Decision Outcomes for this exact objective:\n"
            for dtype, stats in feedback.items():
                prompt += f"- {dtype}: {stats['SUCCESS']} successes, {stats['FAILURE']} failures, {stats['FALLBACK']} fallbacks\n"
            prompt += "\n"

        similar = context.get("similar_decisions", [])
        if similar:
            prompt += "Similar Past Objectives and Outcomes:\n"
            for s in similar[:5]:  # limit to top 5
                prompt += f"- '{s.get('original_objective', 'unknown')}': chose {s.get('decision_type')} -> {s.get('outcome')}\n"
            prompt += "\n"

        if skills:
            prompt += "Matching Skills:\n"
            for s in skills:
                # Provide only relevant fields to save tokens
                prompt += f"- {s.get('name')} (id: {s.get('id')[:8]}, Conf: {s.get('confidence_score')}, Risk: {s.get('risk_level')})\n"
        
        if history:
            prompt += "\nRecent Global Task History:\n"
            for t in history:
                prompt += f"- {t.get('input')} -> {t.get('status')}\n"
                
        return prompt

    def _parse_and_validate(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract JSON if wrapped in code blocks
            clean_response = response.strip()
            if "```json" in clean_response:
                clean_response = clean_response.split("```json")[1].split("```")[0]
            elif "```" in clean_response:
                clean_response = clean_response.split("```")[1].split("```")[0]
            
            data = json.loads(clean_response)
            
            # 1. Validate Schema
            required = ["type", "confidence", "reason"]
            if not all(k in data for k in required):
                raise ValueError("Missing required fields in JSON")
            
            return data
        except Exception as e:
            logger.error(f"Failed to parse LLM decision: {str(e)}")
            return {"type": "NEW", "confidence": 0.0, "reason": f"Parse error: {str(e)}"}

def decide(objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone wrapper for the decision engine."""
    return DecisionEngine().decide(objective, context)
