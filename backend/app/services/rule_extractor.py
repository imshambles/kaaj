"""
AI Rule Extraction Service - Extract lending rules from PDF text using AI
"""
import json
import re
from typing import Optional
import httpx

from app.config import get_settings
from app.engine import EVALUATOR_REGISTRY


# Get all available rule types
AVAILABLE_RULE_TYPES = list(EVALUATOR_REGISTRY.keys())

EXTRACTION_PROMPT = """You are an expert at parsing lender credit policy documents.

Given the following lender guideline text, extract structured rules that can be used for automated underwriting.

AVAILABLE RULE TYPES:
{rule_types}

For each rule you identify, provide:
- rule_type: One of the available rule types above
- operator: "gte" (>=), "lte" (<=), "eq" (=), "in", "not_in"
- value: The threshold value (number, boolean, or list of strings)
- is_required: true if it's a hard requirement, false if it's a preference
- rejection_message: A message explaining why an application would fail this rule

Also extract:
- lender_name: The name of the lender
- program_name: The name of the program/product (if identifiable)
- program_description: Brief description of the program

LENDER GUIDELINE TEXT:
{text}

Respond with valid JSON in this exact format:
{{
    "lender_name": "...",
    "programs": [
        {{
            "name": "...",
            "description": "...",
            "credit_tier": "A" | "B" | "C" | "D" | null,
            "min_loan_amount": number | null,
            "max_loan_amount": number | null,
            "rules": [
                {{
                    "rule_type": "...",
                    "operator": "...",
                    "value": ...,
                    "is_required": true/false,
                    "rejection_message": "..."
                }}
            ]
        }}
    ]
}}

Only include rules that you can confidently identify from the text. If you're unsure about a value, omit that rule.
"""


async def extract_rules_with_gemini(text: str, api_key: str) -> dict:
    """
    Use Google Gemini to extract rules from lender guideline text.
    
    Args:
        text: Extracted text from PDF
        api_key: Gemini API key
        
    Returns:
        Structured lender data with programs and rules
    """
    prompt = EXTRACTION_PROMPT.format(
        rule_types="\n".join(f"- {rt}" for rt in AVAILABLE_RULE_TYPES),
        text=text[:15000]  # Limit text length for API
    )
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                }
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # Extract the text response
        try:
            content = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise Exception("Invalid Gemini API response format")
        
        # Parse JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        # Also try to find raw JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        return json.loads(content)


def validate_extracted_rules(data: dict) -> dict:
    """
    Validate and clean extracted rules.
    
    Args:
        data: Raw extracted data from AI
        
    Returns:
        Validated and cleaned data
    """
    valid_rule_types = set(AVAILABLE_RULE_TYPES)
    valid_operators = {"gte", "lte", "eq", "neq", "in", "not_in"}
    
    for program in data.get("programs", []):
        valid_rules = []
        for rule in program.get("rules", []):
            # Check rule type is valid
            if rule.get("rule_type") not in valid_rule_types:
                continue
            
            # Check operator is valid
            if rule.get("operator") not in valid_operators:
                # Try to infer operator from rule type
                if "min" in rule.get("rule_type", ""):
                    rule["operator"] = "gte"
                elif "max" in rule.get("rule_type", ""):
                    rule["operator"] = "lte"
                elif "excluded" in rule.get("rule_type", "") or "no_" in rule.get("rule_type", ""):
                    rule["operator"] = "eq"
                else:
                    continue
            
            # Ensure value exists
            if rule.get("value") is None:
                continue
            
            # Set defaults
            rule.setdefault("is_required", True)
            rule.setdefault("weight", 10)
            rule.setdefault("rejection_message", f"Failed {rule['rule_type']} requirement")
            
            valid_rules.append(rule)
        
        program["rules"] = valid_rules
    
    return data


async def extract_rules_from_text(text: str, api_key: str) -> dict:
    """
    Main entry point for rule extraction.
    
    Args:
        text: PDF text content
        api_key: Gemini API key
        
    Returns:
        Validated lender data with programs and rules
    """
    raw_data = await extract_rules_with_gemini(text, api_key)
    validated_data = validate_extracted_rules(raw_data)
    return validated_data
