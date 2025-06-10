import requests
import json


class A2AClient:
    def send_request(self, agent_url: str, scenario_input: dict) -> dict:
        """
        Sends a request to the agent and returns the response.
        For now, this is a simple HTTP POST request.
        """
        try:
            # We can expand this to handle different auth types later
            headers = {"Content-Type": "application/json"}

            # The scenario_input is expected to be the payload
            response = requests.post(
                agent_url,
                headers=headers,
                data=json.dumps(scenario_input),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"A2A request failed: {e}"}
        except json.JSONDecodeError:
            return {"error": "Failed to decode agent's JSON response."}
