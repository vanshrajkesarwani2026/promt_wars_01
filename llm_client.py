"""Thin wrapper around the Google Gemini API for structured JSON calls."""
from __future__ import annotations

import json
import os
import re
import time
import random
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# Using Gemini 3.6 Flash for high-speed multi-agent parallelism
MODEL = "gemini-3.6-flash" 

def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

class LLMClient:
    def __init__(self, mode: str = "live", mock_responses: dict | None = None):
        self.mode = mode
        self.mock_responses = mock_responses or {}

        if self.mode == "live":
            import google.generativeai as genai
            genai.configure() 

    def call_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        call_key: str | None = None,
    ) -> T:
        if self.mode == "mock":
            if call_key is None or call_key not in self.mock_responses:
                raise KeyError(
                    f"No mock response registered for call_key={call_key!r}. "
                    "Add one to panel/mock_data.py."
                )
            return response_model.model_validate(self.mock_responses[call_key])

        return self._call_live(system_prompt, user_prompt, response_model)

    def _call_live(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        
        # --- RATE LIMIT FIX ---
        # Stagger the requests by 2 to 5 seconds to prevent the 4 parallel 
        # agents from hitting Google's 15 RPM free-tier limit all at once.
        time.sleep(random.uniform(2.0, 5.0))
        # ----------------------
        
        import google.generativeai as genai
        
        # 1. Convert the Pydantic model to a raw JSON schema
        schema = response_model.model_json_schema()
        
        # Extract definitions block for resolving references
        defs = schema.pop("$defs", {})
        
        # 2. HELPER FUNCTION: Flatten $refs and clean tags Gemini rejects
        def clean_schema_for_gemini(d):
            if isinstance(d, dict):
                # If it's a reference, replace it with the actual unpacked definition
                if "$ref" in d:
                    ref_key = d["$ref"].split("/")[-1]
                    resolved = defs.get(ref_key, {}).copy()
                    return clean_schema_for_gemini(resolved)
                
                cleaned = {}
                for k, v in d.items():
                    # Gemini rejects 'default', 'title', and numeric bounds
                    if k in ["default", "title", "maximum", "minimum", "exclusiveMaximum", "exclusiveMinimum"]:
                        continue
                        
                    # Preemptively flatten Pydantic v2 'anyOf' optional fields
                    if k == "anyOf" and isinstance(v, list):
                        # Grab the first non-null type from the anyOf list
                        types = [item.get("type") for item in v if item.get("type") != "null"]
                        if types:
                            cleaned["type"] = types[0]
                        continue
                        
                    cleaned[k] = clean_schema_for_gemini(v)
                return cleaned
            elif isinstance(d, list):
                return [clean_schema_for_gemini(item) for item in d]
            return d
            
        final_schema = clean_schema_for_gemini(schema)

        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=system_prompt
        )

        last_error = None
        for attempt in range(2):
            try:
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=final_schema,
                        temperature=0.2, 
                    )
                )
                
                raw_text = response.text
                cleaned = _strip_code_fences(raw_text)
                data = json.loads(cleaned)
                return response_model.model_validate(data)
                
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                continue
            except Exception as e:
                raise RuntimeError(f"Gemini API Error: {e}")

        raise RuntimeError(
            f"LLM failed to return valid {response_model.__name__} after retry: {last_error}"
        )