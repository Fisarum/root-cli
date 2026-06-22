import httpx


class OpenAIError(Exception):
    pass


def generate(base_url: str, model: str, api_key: str, prompt: str, system: str) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 256,
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.ConnectError:
        raise OpenAIError(f"Cannot connect to {base_url}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise OpenAIError("Invalid API key. Check your config: ~/.root/config.toml")
        raise OpenAIError(f"API error: {e}")
    except (KeyError, IndexError):
        raise OpenAIError("Unexpected response format from API.")
    except Exception as e:
        raise OpenAIError(f"OpenAI backend error: {e}")
