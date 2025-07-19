import requests

def query_lmstudio(self, prompt: str, endpoint: Optional[str] = None) -> Optional[str]:
        """Query LM Studio with given prompt."""
        endpoint = endpoint or self.endpoint
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.config.get('LMStudio', 'model', fallback="local-model"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.getfloat('LMStudio', 'temperature', fallback=0.7),
            "max_tokens": self.config.getint('LMStudio', 'max_tokens', fallback=2048),
            "stream": False
        }
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying LM Studio at {endpoint}: {str(e)}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Unexpected response format from {endpoint}: {response.text}")
            return None
