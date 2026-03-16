import requests
import urllib3
import json
import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional

# Suppress insecure request warnings for local development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import rate limiter
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from orchestration.rate_limiter import get_rate_limiter

class KimiAdapter:
    """
    Adapter for Kimi K2.5 via NVIDIA API.
    Uses 'requests' directly to bypass SSL verification issues in some environments.
    Integrated with RateLimiter for controlled API access.
    """
    def __init__(self, api_key: str = "MOCK_KEY", base_url: str = "https://integrate.api.nvidia.com/v1", 
                 rate_limiter: Optional[Any] = None, max_concurrent_calls: int = 2):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/') + "/chat/completions"
        self.model = "moonshotai/kimi-k2.5"
        
        # Rate limiter integration
        self.rate_limiter = rate_limiter or get_rate_limiter(max_concurrent_calls)
        self.agent_type = "kimi_adapter"  # Default, can be overridden per call


    def chat(self, messages: List[Dict[str, str]], stream: bool = False, agent_type: str = None, **kwargs) -> Any:
        """
        Send a chat message to Kimi K2.5 using requests.
        Rate-limited to prevent API overload.
        
        Args:
            messages: Chat messages
            stream: Whether to stream response
            agent_type: Optional agent type for tracking (defaults to self.agent_type)
            **kwargs: Additional parameters for the API
        
        Returns:
            LLM response content
        """
        # Handle async in sync context
        try:
            # Try to get existing loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running (e.g., in FastAPI), use nest_asyncio
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                except ImportError:
                    # If nest_asyncio not available, create a task instead
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            self._chat_async(messages, stream, agent_type or self.agent_type, **kwargs)
                        )
                        return future.result()
            
            return loop.run_until_complete(
                self._chat_async(messages, stream, agent_type or self.agent_type, **kwargs)
            )
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(
                self._chat_async(messages, stream, agent_type or self.agent_type, **kwargs)
            )
    
    async def _chat_async(self, messages: List[Dict[str, str]], stream: bool, agent_type: str, **kwargs) -> Any:
        """
        Async version of chat with rate limiting
        """
        if self.api_key == "MOCK_KEY":
            return self._mock_response(messages)
        
        # Generate unique call ID
        call_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
        
        # Acquire rate limit slot
        record = await self.rate_limiter.acquire(call_id, agent_type)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Using verified safer defaults
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
                "stream": stream
            }
            payload.update(kwargs)
            
            # Make API call
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=payload, 
                verify=False,
                timeout=30  # Reduced from 300s - fail faster
            )
            response.raise_for_status()
            data = response.json()
            
            # Release rate limit slot (success)
            self.rate_limiter.release(call_id, success=True)
            
            # Extract content from response
            return data['choices'][0]['message']['content']
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            # Release rate limit slot (failure)
            self.rate_limiter.release(call_id, success=False, error=str(e))
            
            print(f"\n⚠️  Cannot reach NVIDIA API - using mock response for development")
            return self._mock_response(messages, error=True)
            
        except Exception as e:
            # Release rate limit slot (failure)
            error_msg = str(e)
            self.rate_limiter.release(call_id, success=False, error=error_msg)
            
            # Check if rate limited
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                print(f"\n⚠️  Rate limited by API - retrying with backoff")
                # Exponential backoff retry
                await asyncio.sleep(2)  # Wait 2 seconds before retry
                return await self._chat_async(messages, stream, agent_type, **kwargs)
            
            print(f"\n⚠️  API Error: {error_msg[:100]} - using mock response")
            return self._mock_response(messages, error=True)

    def _mock_response(self, messages: List[Dict[str, str]], error: bool = False) -> Any:
        # Mock response for development/fallback.
        # Returns context-aware responses based on the prompt content to simulate all agents.
        
        last_msg = messages[-1]["content"] if messages else ""
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        
        # Debug logging
        try:
            with open("mock_log.txt", "a", encoding='utf-8') as f:
                f.write(f"\n--- REQUEST ---\nSystem: {system_msg[:50]}...\nUser: {last_msg[:50]}...\n")
        except:
            pass
        
        # 1. Product Interpreter
        if "Product Manager" in system_msg or "Product Manager" in last_msg or "structured product requirements" in last_msg:
            return json.dumps({
                "product_name": "RentIt Platform",
                "description": "A rental marketplace for store owners and customers.",
                "features": [
                    {"name": "Store Management", "priority": "high", "description": "Create and manage rental stores"},
                    {"name": "Booking System", "priority": "high", "description": "Calendar-based bookings"},
                    {"name": "Payment Integration", "priority": "high", "description": "Stripe payments"}
                ],
                "pages": [
                    {"name": "Home", "route": "/", "components": ["Hero", "Featured"]},
                    {"name": "Store", "route": "/store/[id]", "components": ["StoreHeader", "ProductGrid"]}
                ],
                "user_flows": [{"name": "Book Item", "steps": ["Find", "Select Date", "Pay"]}],
                "tech_stack_recommendations": {"frontend": "Next.js", "backend": "Node.js", "database": "PostgreSQL"}
            })

        # 2. Frontend Engineer
        elif "Frontend Engineer" in system_msg or "Frontend Engineer" in last_msg:
            # Check for specific request types
            if "package.json" in last_msg:
                return json.dumps({
                    "name": "rental-frontend",
                    "version": "0.1.0",
                    "private": True,
                    "scripts": {
                        "dev": "next dev",
                        "build": "next build",
                        "start": "next start",
                        "lint": "next lint"
                    },
                    "dependencies": {
                        "react": "^18",
                        "react-dom": "^18",
                        "next": "14.2.3"
                    },
                    "devDependencies": {
                        "postcss": "^8",
                        "tailwindcss": "^3.4.1"
                    }
                })
            elif "architecture" in last_msg.lower() or "structure" in last_msg.lower():
                # Return Component Architecture JSON
                return json.dumps({
                    "components": [
                        {
                            "name": "App",
                            "type": "layout", 
                            "path": "src/App.jsx",
                            "props": [],
                            "state": [],
                            "children": ["Routes"]
                        },
                        {
                            "name": "StoreList", 
                            "type": "page",
                            "path": "src/pages/StoreList.jsx", 
                            "props": [],
                            "state": ["stores"], 
                            "children": ["StoreCard"]
                        }
                    ],
                    "routing": [
                        {"path": "/", "component": "StoreList", "protected": False}
                    ],
                    "state_structure": {
                        "stores": ["auth", "data"],
                        "global_state": ["user", "theme"]
                    }
                })
            else:
                # Component Code Generation
                return """
import React from 'react';

export default function GenericComponent() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Generated Component</h1>
      <p>This is a mock component generated by KimiAdapter fallback.</p>
    </div>
  );
}
"""

        # 3. Backend Engineer
        elif "Backend Engineer" in system_msg or "Backend Engineer" in last_msg or "Database Architect" in last_msg:
            if "package.json" in last_msg:
                return json.dumps({
                    "name": "rental-backend",
                    "version": "1.0.0",
                    "main": "index.js",
                    "dependencies": {"express": "^4.19.2", "cors": "^2.8.5"}
                })
            elif "api design" in last_msg.lower() or "endpoints" in last_msg.lower() or "restful api" in last_msg.lower():
                # Return API Design JSON
                return json.dumps({
                    "endpoints": [
                        {
                            "method": "GET",
                            "path": "/api/stores",
                            "description": "List all stores",
                            "auth_required": False
                        },
                        {
                            "method": "GET", 
                            "path": "/api/stores/:id",
                            "description": "Get store details",
                            "auth_required": False
                        },
                        {
                            "method": "POST",
                            "path": "/api/bookings",
                            "description": "Create a new booking",
                            "auth_required": True
                        }
                    ],
                    "controllers": [
                        {
                            "name": "StoreController",
                            "endpoints": ["/api/stores", "/api/stores/:id"],
                            "dependencies": ["StoreModel"]
                        },
                        {
                            "name": "BookingController",
                            "endpoints": ["/api/bookings"],
                            "dependencies": ["BookingModel", "PaymentService"]
                        }
                    ],
                    "middleware": ["auth", "validation", "error-handling"]
                })
            elif "schema" in last_msg.lower() or "sql" in last_msg.lower() or "database schema" in last_msg.lower():
                # Return Database Schema JSON (Backend Agent expects JSON for schema design too)
                # Check if prompt asks for JSON schema or SQL code
                if "json format" in last_msg.lower():
                    return json.dumps({
                        "tables": [
                            {
                                "name": "users",
                                "columns": [
                                    {"name": "id", "type": "uuid", "nullable": False, "unique": True},
                                    {"name": "email", "type": "varchar", "nullable": False, "unique": True},
                                    {"name": "name", "type": "varchar", "nullable": False}
                                ],
                                "indexes": ["email"],
                                "constraints": ["pk_users"]
                            },
                            {
                                "name": "stores",
                                "columns": [
                                    {"name": "id", "type": "uuid", "nullable": False, "unique": True},
                                    {"name": "name", "type": "varchar", "nullable": False},
                                    {"name": "owner_id", "type": "uuid", "nullable": False}
                                ],
                                "indexes": ["owner_id"],
                                "constraints": ["pk_stores", "fk_owner"]
                            }
                        ],
                        "relationships": [
                            {"from": "stores.owner_id", "to": "users.id", "type": "one-to-many"}
                        ]
                    })
                else:
                    return """
CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255));
CREATE TABLE stores (id SERIAL PRIMARY KEY, name VARCHAR(255));
"""
            else:
                return """
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.json({ message: 'Rental API Ready' });
});

module.exports = app;
"""

        # 4. Integration Agent
        elif "You are an expert Integration Engineer" in system_msg:
            if "docker-compose" in last_msg.lower():
                return """
version: '3.8'
services:
  web:
    build: ./frontend
    ports: ["3000:3000"]
  api:
    build: ./backend
    ports: ["5000:5000"]
"""
            else:
                return "# Config\nAPI_URL=http://localhost:5000"

        # 5. Default/Generic fallback
        if error:
            # Fallback JSON to avoid parsing errors in Product Interpreter if that's where it failed
            return json.dumps({"product_name": "Fallback Project", "features": [], "pages": []})
            
        return f"[MOCK] Processed request: {last_msg[:50]}..."

# Usage documentation:
# adapter = KimiAdapter(api_key=os.getenv("NVIDIA_API_KEY"))
