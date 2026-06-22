import httpx


class OllamaError(Exception):
    pass


def generate(host: str, model: str, prompt: str, system: str) -> str:
    url = f"{host.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 256,
            "stop": ["\n", "```", "#"],
        },
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except httpx.ConnectError:
        raise OllamaError(
            "Cannot connect to Ollama. Is it running?\n"
            "Start it with:  ollama serve\n"
            "Install from:   https://ollama.com"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise OllamaError(
                f"Model '{model}' not found in Ollama.\n"
                f"Pull it with:  ollama pull {model}"
            )
        raise OllamaError(f"Ollama HTTP error: {e}")
    except Exception as e:
        raise OllamaError(f"Ollama error: {e}")


def is_available(host: str) -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{host.rstrip('/')}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


def list_models(host: str) -> list[str]:
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{host.rstrip('/')}/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return []


def pull_model(host: str, model: str) -> None:
    url = f"{host.rstrip('/')}/api/pull"
    with httpx.Client(timeout=None) as client:
        with client.stream("POST", url, json={"name": model}) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                pass
