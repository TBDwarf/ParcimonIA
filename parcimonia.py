from pydantic import BaseModel, Field
import requests
import json
import re
from typing import Union, Generator, Iterator, Optional
import numpy as np

# ENGLISH :
# ParcimonIA — a "pipe" for OpenWebUI that dynamically chooses which model to call
# based on request complexity and cost/latency constraints.
# (e.g., gpt-5-nano -> gpt-5-mini or gpt-5 depending on the score). Goal: reduce cost
# while maintaining perceived quality.
#
# FRANCAIS :
# ParcimonIA — "pipe" pour OpenWebUI qui choisit dynamiquement quel modèle appeler
# en fonction de la complexité de la requête et des contraintes coût/latence.
# (ex: gpt-5-nano -> gpt-5-mini ou gpt-5 selon score). Objectif : réduire coût
# tout en maintenant la qualité perçue.
#
# Version 1.0
# Copyright (c) 2025 TBDwarf - Tommy RENAULT
# License: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class Pipe:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = Field(
            default="", description="OpenAI API key for authentication"
        )
        OPENAI_API_BASE: str = Field(
            default="https://api.openai.com/v1", description="OpenAI API base URL"
        )
        LIGHT_MODEL: str = Field(
            default="gpt-5-mini",
            description="Model to use for simple tasks (e.g., gpt-5-nano, gpt-5-mini)",
        )
        HEAVY_MODEL: str = Field(
            default="gpt-5",
            description="Model to use for complex tasks (e.g., gpt-5, gpt-5-mini)",
        )
        ROUTING_MODEL: str = Field(
            default="gpt-5-nano",
            description="Model to use for analyzing and routing requests",
        )
        DEBUG_ROUTING: bool = Field(
            default=True,
            description="Show complete routing model response in the answer",
        )
        SHOW_MODEL_USED: bool = Field(
            default=True,
            description="Display which model is being used at the start of response",
        )
        KEEP_MODEL_IN_CONVERSATION: bool = Field(
            default=True,
            description="Keep using the same model throughout the conversation if detected in previous response",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.selected_model_name = None
        self.routing_debug_info = None
        self.model_reused = False  # Flag to track if model was reused

    def is_gpt5_model(self, model: str) -> bool:
        """Check if model is GPT-5 (requires max_completion_tokens instead of max_tokens)"""
        return model.startswith("gpt-5")

    def extract_model_from_previous_message(self, messages: list) -> Optional[str]:
        """
        Extract model name from previous assistant message.
        Looks for pattern: [Usage of MODEL_NAME] or **[Usage of MODEL_NAME]**
        Returns the full model name if found, with prioritization for exact matches.
        """
        if not messages or len(messages) < 2:
            return None

        # Get the last assistant message
        last_assistant_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                last_assistant_msg = msg.get("content", "")
                break

        if not last_assistant_msg:
            return None

        # Search for [Usage of XXX] pattern
        pattern = r"\[Usage of ([^\]]+)\]"
        match = re.search(pattern, last_assistant_msg, re.IGNORECASE)

        if not match:
            return None

        model_found = match.group(1).strip()
        print(f"[DEBUG] Extracted from previous message: '{model_found}'")

        # ⚠️ CORRECTION : Vérifier d'abord le HEAVY_MODEL (plus spécifique)
        # Priorité 1 : Match exact
        if model_found == self.valves.HEAVY_MODEL:
            print(f"[DEBUG] Exact match with HEAVY_MODEL")
            return self.valves.HEAVY_MODEL
        if model_found == self.valves.LIGHT_MODEL:
            print(f"[DEBUG] Exact match with LIGHT_MODEL")
            return self.valves.LIGHT_MODEL

        # Priorité 2 : HEAVY_MODEL contient le pattern (ex: "gpt-5" dans "gpt-5-2025-08-07")
        if model_found in self.valves.HEAVY_MODEL:
            print(
                f"[DEBUG] Partial match with HEAVY_MODEL: '{model_found}' in '{self.valves.HEAVY_MODEL}'"
            )
            return self.valves.HEAVY_MODEL

        # Priorité 3 : LIGHT_MODEL contient le pattern
        if model_found in self.valves.LIGHT_MODEL:
            print(
                f"[DEBUG] Partial match with LIGHT_MODEL: '{model_found}' in '{self.valves.LIGHT_MODEL}'"
            )
            return self.valves.LIGHT_MODEL

        # Priorité 4 : Pattern est contenu dans HEAVY_MODEL
        if (
            model_found in self.valves.HEAVY_MODEL
            or self.valves.HEAVY_MODEL.startswith(model_found)
        ):
            print(f"[DEBUG] HEAVY_MODEL starts with '{model_found}'")
            return self.valves.HEAVY_MODEL

        # Priorité 5 : Pattern est contenu dans LIGHT_MODEL
        if (
            model_found in self.valves.LIGHT_MODEL
            or self.valves.LIGHT_MODEL.startswith(model_found)
        ):
            print(f"[DEBUG] LIGHT_MODEL starts with '{model_found}'")
            return self.valves.LIGHT_MODEL

        print(f"[DEBUG] No match found for '{model_found}'")
        return None

    def classify_task_with_llm(self, user_query: str) -> tuple:
        """Use LLM to decide which model to use"""
        prompt = f"""Analyze this user request and decide which model should handle it:

    "light" for: translations, summaries, simple questions, formatting, basic tasks
    "heavy" for: complex reasoning, coding, analysis, research, multi-step problems

User request: "{user_query}"

Answer with ONLY: light OR heavy"""

        # Initialize debug info
        self.routing_debug_info = {
            "prompt": prompt,
            "raw_response": "ERROR",
            "full_response": None,
            "error_detail": None,
        }

        try:
            # Prepare payload - ALWAYS non-streaming for routing
            payload = {
                "model": self.valves.ROUTING_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            }

            # GPT-5 models use max_completion_tokens, others use max_tokens
            if self.is_gpt5_model(self.valves.ROUTING_MODEL):
                payload["max_completion_tokens"] = 1000
            else:
                payload["max_tokens"] = 1000

            headers = {
                "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            # Make synchronous API call
            response = requests.post(
                f"{self.valves.OPENAI_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code != 200:
                self.routing_debug_info["error_detail"] = (
                    f"HTTP {response.status_code}: {response.text}"
                )
                print(f"[ERROR] Routing API error: {response.text}")
                return self.valves.LIGHT_MODEL, 0.5

            result = response.json()
            self.routing_debug_info["full_response"] = result

            # Extract decision from response
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                content = choice.get("message", {}).get("content", "").strip().lower()
                self.routing_debug_info["raw_response"] = content or "EMPTY RESPONSE"

                if not content:
                    self.routing_debug_info["error_detail"] = (
                        f"Empty content. Finish reason: {choice.get('finish_reason', 'N/A')}"
                    )
                    return self.valves.LIGHT_MODEL, 0.5

                # Parse decision
                if "heavy" in content:
                    return self.valves.HEAVY_MODEL, 0.9
                elif "light" in content:
                    return self.valves.LIGHT_MODEL, 0.9
                else:
                    self.routing_debug_info["error_detail"] = (
                        f"Unexpected response format: '{content}'"
                    )
                    return self.valves.LIGHT_MODEL, 0.5
            else:
                self.routing_debug_info["error_detail"] = "No choices in response"
                return self.valves.LIGHT_MODEL, 0.5

        except Exception as e:
            self.routing_debug_info["error_detail"] = f"Exception: {str(e)}"
            print(f"[ERROR] Routing classification failed: {e}")
            return self.valves.LIGHT_MODEL, 0.5

    def call_openai_model(
        self, model: str, messages: list, body: dict
    ) -> Union[str, Generator]:
        """Call OpenAI API with specified model"""
        try:
            # Store selected model for logging
            self.selected_model_name = model

            # Prepare payload
            payload = {
                "model": model,
                "messages": messages,
                "stream": body.get("stream", True),
            }

            # Copy other parameters if provided
            for key in [
                "temperature",
                "top_p",
                "frequency_penalty",
                "presence_penalty",
            ]:
                if key in body:
                    payload[key] = body[key]

            # Handle max_tokens based on model type
            if self.is_gpt5_model(model):
                if "max_completion_tokens" in body:
                    payload["max_completion_tokens"] = body["max_completion_tokens"]
            else:
                if "max_tokens" in body:
                    payload["max_tokens"] = body["max_tokens"]

            headers = {
                "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            # Make API call
            response = requests.post(
                f"{self.valves.OPENAI_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                stream=payload["stream"],
                timeout=600,
            )

            if response.status_code != 200:
                error_msg = (
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )
                print(f"[ERROR] {error_msg}")
                return error_msg

            # Handle streaming response
            if payload["stream"]:
                return self.stream_response(response, model)
            else:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return "Error: No response from model"

        except Exception as e:
            error_msg = f"Model call error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg

    def stream_response(self, response, model: str) -> Generator[str, None, None]:
        """Stream response from OpenAI API"""

        # Display model being used (if enabled) - IN BOLD
        if self.valves.SHOW_MODEL_USED:
            yield f"**[Utilisation de {model}]**\n\n"

        # Add debug info at the start if enabled
        if self.valves.DEBUG_ROUTING and self.routing_debug_info:
            debug_output = "=== ROUTING DEBUG ===\n"

            # Show if model was reused from previous conversation
            if self.model_reused:
                debug_output += "**[CONTINUITY] ✓ Continuing with previous model (found in last response)**\n"
            else:
                debug_output += "**[ROUTING] New analysis performed (no previous model detected)**\n"

            debug_output += f"Routing Model: {self.valves.ROUTING_MODEL}\n"
            debug_output += f"Raw Response: '{self.routing_debug_info.get('raw_response', 'N/A')}'\n\n"
            if self.routing_debug_info.get("error_detail"):
                debug_output += (
                    f"Error Details:\n{self.routing_debug_info['error_detail']}\n\n"
                )
            debug_output += (
                f"Prompt sent:\n{self.routing_debug_info.get('prompt', 'N/A')}\n\n"
            )
            debug_output += "=" * 40 + "\n\n"
            yield debug_output

        try:
            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data = line_text[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[ERROR] Stream error: {e}")
            yield f"\n\nError during streaming: {str(e)}"

    def pipe(self, body: dict) -> Union[str, Generator[str, None, None]]:
        """Main pipe method for routing and execution"""
        try:
            if not self.valves.OPENAI_API_KEY:
                return "Error: OpenAI API key not configured"

            # Extract messages from request body
            messages = body.get("messages", [])
            if not messages:
                return "Error: No messages provided"

            # Get the latest user query
            user_query = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_query = msg.get("content", "")
                    break

            if not user_query:
                return "Error: No user query found"

            # Step 1: Check if we should continue with previous model
            selected_model = None
            confidence = 0.0
            self.model_reused = False

            if self.valves.KEEP_MODEL_IN_CONVERSATION:
                previous_model = self.extract_model_from_previous_message(messages)
                if previous_model:
                    selected_model = previous_model
                    confidence = 1.0
                    self.model_reused = True
                    print(
                        f"[CONTINUITY] ✓ Continuing with previous model: {selected_model}"
                    )

                    # Create minimal routing debug info for display
                    self.routing_debug_info = {
                        "prompt": "Model reused from previous conversation",
                        "raw_response": f"REUSED: {selected_model}",
                        "full_response": None,
                        "error_detail": None,
                    }
                else:
                    print(
                        "[ROUTING] No previous model detected, performing new analysis..."
                    )

            # Step 2: If no previous model found, perform LLM-based classification
            if not selected_model:
                selected_model, confidence = self.classify_task_with_llm(user_query)

            # Step 3: Call the selected model
            return self.call_openai_model(selected_model, messages, body)

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg
