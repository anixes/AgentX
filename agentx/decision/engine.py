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

        prompt = self._build_prompt(objective, context)
        
        try:
            # Using a cheap model for decision making
            raw_response = self.gateway.chat(
                model="gpt-4o-mini",
                prompt=prompt,
                system=self.SYSTEM_PROMPT
            )
            
            decision = self._parse_and_validate(raw_response, context)
            return decision
        except Exception as e:
            logger.error(f"Decision engine failure: {str(e)}")
            return {"type": "NEW", "confidence": 0.0, "reason": f"Error: {str(e)}"}

    def _build_prompt(self, objective: str, context: Dict[str, Any]) -> str:
        skills = context.get("top_skills", [])
        history = context.get("task_history", [])
        risk = context.get("risk_level", "LOW")
        
        prompt = f"Objective: {objective}\n"
        prompt += f"Risk Level: {risk}\n\n"
        
        if skills:
            prompt += "Matching Skills:\n"
            for s in skills:
                # Provide only relevant fields to save tokens
                prompt += f"- {s.get('name')} (id: {s.get('id')[:8]}, Conf: {s.get('confidence_score')}, Risk: {s.get('risk_level')})\n"
        
        if history:
            prompt += "\nRecent Task History:\n"
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
            
            # 2. Validate Type
            valid_types = ["SKILL", "COMPOSE", "NEW", "ASK", "REJECT"]
            if data["type"] not in valid_types:
                logger.warning(f"Invalid decision type: {data['type']}. Falling back to NEW.")
                data["type"] = "NEW"
            
            # 3. Hard Constraint: HIGH Risk -> ASK or REJECT
            risk = context.get("risk_level", "LOW")
            if risk == "HIGH" and data["type"] not in ["ASK", "REJECT"]:
                data["type"] = "ASK"
                data["reason"] = f"[REDACTED] Forced to ASK due to HIGH risk (Original decision: {data['type']})"
            
            # 4. Hard Constraint: Low Confidence -> NEW
            if float(data["confidence"]) < 0.6 and data["type"] != "NEW":
                data["type"] = "NEW"
                data["reason"] = f"Confidence {data['confidence']} too low, falling back to NEW (Original decision: {data['type']})"
                
            return data
        except Exception as e:
            logger.error(f"Failed to parse LLM decision: {str(e)}")
            return {"type": "NEW", "confidence": 0.0, "reason": f"Parse error: {str(e)}"}

def decide(objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone wrapper for the decision engine."""
    return DecisionEngine().decide(objective, context)
