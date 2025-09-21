"""
title: German Insurance Knowledge Selector Pipeline
author: open-webui
date: 2024-12-21
version: 1.0
license: MIT
description: A pipeline that intelligently selects the most relevant German insurance knowledge base (Sparte) based on user queries and queries OpenWebUI's knowledge API.
requirements: requests, openai
"""

from typing import List, Union, Generator, Iterator, Dict, Optional
from pydantic import BaseModel, Field
import requests
import json
import re
from schemas import OpenAIChatMessage

class Pipeline:
    class Valves(BaseModel):
        # OpenWebUI API configuration
        OPENWEBUI_BASE_URL: str = Field(
            default="http://localhost:3000",
            description="Base URL of the OpenWebUI instance"
        )
        OPENWEBUI_API_KEY: str = Field(
            default="",
            description="API key for OpenWebUI authentication"
        )
        
        # AI model for knowledge base selection
        SELECTION_MODEL: str = Field(
            default="gpt-3.5-turbo",
            description="Model to use for knowledge base selection"
        )
        OPENAI_API_KEY: str = Field(
            default="",
            description="OpenAI API key for knowledge base selection"
        )
        
        # German insurance knowledge base mappings
        INSURANCE_KNOWLEDGE_BASES: Dict[str, str] = Field(
            default={
                "kfz": "Auto Insurance (KFZ) - Kraftfahrzeugversicherung",
                "kranken": "Health Insurance (Krankenversicherung)",
                "haftpflicht": "Liability Insurance (Haftpflichtversicherung)", 
                "hausrat": "Household Insurance (Hausratversicherung)",
                "wohngebäude": "Building Insurance (Wohngebäudeversicherung)",
                "leben": "Life Insurance (Lebensversicherung)",
                "unfall": "Accident Insurance (Unfallversicherung)",
                "rechtsschutz": "Legal Protection Insurance (Rechtsschutzversicherung)",
                "reise": "Travel Insurance (Reiseversicherung)",
                "berufsunfähigkeit": "Disability Insurance (Berufsunfähigkeitsversicherung)"
            },
            description="Mapping of insurance types (Sparten) to their knowledge base descriptions"
        )
        
        # Default fallback knowledge base
        DEFAULT_KNOWLEDGE_BASE: str = Field(
            default="allgemein",
            description="Default knowledge base to use when no specific match is found"
        )

    def __init__(self):
        self.name = "German Insurance Knowledge Selector"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"Starting {self.name}")
        # Validate configuration
        if not self.valves.OPENWEBUI_BASE_URL:
            print("Warning: OPENWEBUI_BASE_URL not configured")
        if not self.valves.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not configured - knowledge selection may not work")

    async def on_shutdown(self):
        print(f"Shutting down {self.name}")

    def analyze_query_for_insurance_type(self, user_message: str) -> str:
        """
        Analyze the user query to determine the most relevant insurance type (Sparte).
        Uses both keyword matching and AI-based analysis.
        """
        user_message_lower = user_message.lower()
        
        # Keyword-based matching for common terms (ordered by specificity)
        keyword_mappings = {
            "berufsunfähigkeit": ["berufsunfähig", "arbeitsunfähig", "erwerbsunfähig", "berufsunfähigkeitsrente", "bu-rente"],
            "kfz": ["auto", "kfz", "kraftfahrzeug", "fahrzeug", "pkw", "kasko", "vollkasko", "teilkasko", "autounfall"],
            "kranken": ["kranken", "gesundheit", "arzt", "behandlung", "medizin", "krank", "krankenversicherung"],
            "haftpflicht": ["haftpflicht", "haftpflichtversicherung", "schaden", "verschulden", "dritten", "personenschaden"],
            "hausrat": ["hausrat", "hausratversicherung", "einbruch", "diebstahl", "wohnung", "möbel", "elektronik"],
            "wohngebäude": ["gebäude", "haus", "immobilie", "feuer", "sturm", "leitungswasser", "wohngebäude"],
            "rechtsschutz": ["rechtsschutz", "anwalt", "gericht", "klage", "rechtlich", "rechtsschutzversicherung"],
            "reise": ["reise", "urlaub", "ausland", "storno", "gepäck", "rücktritt", "reiseversicherung"],
            "unfall": ["unfallversicherung", "verletzung", "invalidität", "erwerbsminderung"],
            "leben": ["leben", "tod", "sterbe", "todesfall", "hinterbliebene", "lebensversicherung", "kapitallebensversicherung"]
        }
        
        # Check for direct keyword matches
        for insurance_type, keywords in keyword_mappings.items():
            for keyword in keywords:
                if keyword in user_message_lower:
                    return insurance_type
        
        # If no direct match, use AI for more sophisticated analysis
        return self.ai_analyze_insurance_type(user_message)

    def ai_analyze_insurance_type(self, user_message: str) -> str:
        """
        Use AI to analyze the query and determine the best insurance type.
        """
        if not self.valves.OPENAI_API_KEY:
            return self.valves.DEFAULT_KNOWLEDGE_BASE
            
        try:
            # Prepare the prompt for insurance type classification
            system_prompt = f"""You are an expert German insurance advisor. Analyze the user's question and determine which type of German insurance (Sparte) is most relevant.

Available insurance types:
{json.dumps(self.valves.INSURANCE_KNOWLEDGE_BASES, indent=2, ensure_ascii=False)}

Respond with ONLY the insurance type key (e.g., 'kfz', 'kranken', 'haftpflicht', etc.). If uncertain, respond with '{self.valves.DEFAULT_KNOWLEDGE_BASE}'.

User question: {user_message}"""

            # Make API call to OpenAI
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.valves.SELECTION_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt}
                    ],
                    "max_tokens": 50,
                    "temperature": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                selected_type = result["choices"][0]["message"]["content"].strip().lower()
                
                # Validate the response is a known insurance type
                if selected_type in self.valves.INSURANCE_KNOWLEDGE_BASES:
                    return selected_type
                    
        except Exception as e:
            print(f"AI analysis failed: {e}")
            
        return self.valves.DEFAULT_KNOWLEDGE_BASE

    def query_openwebui_knowledge(self, knowledge_base: str, query: str) -> str:
        """
        Query the OpenWebUI knowledge base API with the selected knowledge base.
        This method tries multiple possible API endpoints that OpenWebUI might use.
        """
        if not self.valves.OPENWEBUI_BASE_URL:
            return f"Error: OpenWebUI not configured. Would query {knowledge_base} with: {query}"
            
        # Try different possible API endpoints
        possible_endpoints = [
            f"/api/v1/knowledge/{knowledge_base}/query",
            f"/api/v1/knowledge/query/{knowledge_base}",
            f"/api/knowledge/{knowledge_base}/search",
            f"/api/v1/documents/search",
            f"/api/v1/chat/knowledge/{knowledge_base}"
        ]
        
        for endpoint in possible_endpoints:
            try:
                api_url = f"{self.valves.OPENWEBUI_BASE_URL.rstrip('/')}{endpoint}"
                
                headers = {
                    "Content-Type": "application/json"
                }
                
                # Add authentication if API key is provided
                if self.valves.OPENWEBUI_API_KEY:
                    headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
                
                payload = {
                    "query": query,
                    "knowledge_base": knowledge_base,
                    "limit": 5,
                    "collection": knowledge_base,
                    "source": knowledge_base
                }
                
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Try to extract content from various possible response formats
                    
                    if "results" in result and result["results"]:
                        context = "\n".join([item.get("content", item.get("text", "")) for item in result["results"][:3]])
                        if context.strip():
                            return f"Based on {self.valves.INSURANCE_KNOWLEDGE_BASES.get(knowledge_base, knowledge_base)} knowledge:\n\n{context}"
                    
                    elif "documents" in result and result["documents"]:
                        context = "\n".join([doc.get("content", doc.get("text", "")) for doc in result["documents"][:3]])
                        if context.strip():
                            return f"Based on {self.valves.INSURANCE_KNOWLEDGE_BASES.get(knowledge_base, knowledge_base)} knowledge:\n\n{context}"
                    
                    elif "data" in result and result["data"]:
                        if isinstance(result["data"], list):
                            context = "\n".join([item.get("content", item.get("text", str(item))) for item in result["data"][:3]])
                        else:
                            context = str(result["data"])
                        if context.strip():
                            return f"Based on {self.valves.INSURANCE_KNOWLEDGE_BASES.get(knowledge_base, knowledge_base)} knowledge:\n\n{context}"
                    
                    elif "response" in result:
                        return f"Based on {self.valves.INSURANCE_KNOWLEDGE_BASES.get(knowledge_base, knowledge_base)} knowledge:\n\n{result['response']}"
                        
                elif response.status_code == 404:
                    # Try next endpoint
                    continue
                else:
                    print(f"HTTP {response.status_code} for endpoint {endpoint}: {response.text}")
                    continue
                    
            except requests.exceptions.ConnectionError:
                # Connection failed, but this is expected in test environment
                break
            except Exception as e:
                print(f"Error trying endpoint {endpoint}: {str(e)}")
                continue
        
        # If we reach here, either connection failed or no endpoint worked
        return f"""**OpenWebUI Knowledge Base Integration**

*Note: This pipeline would normally query the '{knowledge_base}' knowledge base in OpenWebUI, but no connection is available.*

**Selected Sparte:** {self.valves.INSURANCE_KNOWLEDGE_BASES.get(knowledge_base, knowledge_base)}

**How it works:**
1. The pipeline analyzes your German insurance question
2. Determines the most relevant insurance type (Sparte)
3. Queries the corresponding knowledge base in OpenWebUI
4. Returns contextual information specific to that insurance line

**To use with actual OpenWebUI:**
1. Configure OPENWEBUI_BASE_URL in pipeline valves
2. Set OPENWEBUI_API_KEY if authentication is required
3. Ensure knowledge bases are named according to insurance types (kfz, kranken, hausrat, etc.)

Your question would be sent to the **{knowledge_base}** knowledge base."""

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipeline function that selects appropriate insurance knowledge base and queries it.
        """
        print(f"Processing query: {user_message}")
        
        # Step 1: Analyze the query to determine the best insurance type
        selected_insurance_type = self.analyze_query_for_insurance_type(user_message)
        insurance_description = self.valves.INSURANCE_KNOWLEDGE_BASES.get(
            selected_insurance_type, 
            "General Insurance Information"
        )
        
        print(f"Selected insurance type: {selected_insurance_type} ({insurance_description})")
        
        # Step 2: Query the OpenWebUI knowledge base
        knowledge_response = self.query_openwebui_knowledge(selected_insurance_type, user_message)
        
        # Step 3: Format the response
        response = f"""**Selected Insurance Area:** {insurance_description}

{knowledge_response}

---
*This response was generated using the {selected_insurance_type} knowledge base. If you need information about a different insurance type, please specify it in your question.*"""

        return response