import httpx

def generate_tool_example(tool_name, description, model="llama3", base_url="http://localhost:11434/api/generate"):
    prompt = f"""
Tool: {tool_name}
Description: {description}

Please return a JSON object that shows how this tool would be used.
Only return the JSON with the proper fields.
"""

    response = httpx.post(base_url, json={
        "model": model,
        "prompt": prompt,
        "stream": False
    }, timeout=None)

    if response.status_code != 200:
        raise RuntimeError(f"LLM error: {response.status_code}")

    return response.json()["response"]
