import requests
import re

class GoogleSearchTool:
    def __init__(self, api_key: str, cse_id: str):
        self.name = "google_search"
        self.description = "Searches Google using Custom Search API and returns top results."
        self.api_key = api_key
        self.cse_id = cse_id

    def run(self, query: str, num_results: int = 5) -> str:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": num_results
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()

            items = data.get("items", [])
            if not items:
                return "No results found."

            results = []
            for item in items:
                title = item.get("title")
                snippet = item.get("snippet")
                link = item.get("link")
                if title and snippet and link:
                    results.append(f"• {title}\n  {snippet}\n  {link}")

            return "\n\n".join(results)

        except Exception as e:
            return f"[Error using google_search tool: {e}]"


API_KEY = "AIzaSyAGkMGwlmkJlYkwqS0CDSGN7vKD_a9yick"
CSE_ID = "b413f8a3b3ee1482d"

_google_search_tool = GoogleSearchTool(API_KEY, CSE_ID)


def extract_facts(text):
    facts = []

    # Pattern for key-value style facts
    pattern = re.compile(r"([a-zA-Z ]{2,30}?) (?:is|was|are|were) ([A-Z][a-z]+(?: [A-Z][a-z]+){0,3})", re.IGNORECASE)
    for match in pattern.finditer(text):
        key = match.group(1).strip().lower().replace(" ", "_")
        value = match.group(2).strip()
        facts.append((key, value))

    # Extract unique capitalized phrases (proper nouns/entities)
    capitalized_phrases = set(re.findall(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b", text))
    for phrase in capitalized_phrases:
        facts.append(("entity", phrase))

    return facts

def run(command: str, model=None, memory=None, history=None) -> str:
    raw_results = _google_search_tool.run(command)

    if memory:
        facts = extract_facts(raw_results)
        # Add facts with more context-specific keys if possible
        for key, value in facts:
            memory.add_fact(key, value)

    if model is None:
        return raw_results

    context = memory.get_all_facts_summary() if memory else ""
    previous_dialogue = ""
    if history:
        # history is list of (user_question, assistant_answer)
        for q, a in history:
            previous_dialogue += f"User: {q}\nAssistant: {a}\n"

    prompt = (
        f"{previous_dialogue}"
        f"{context}"
        f"User asked: \"{command}\"\n"
        f"Here are the search results:\n{raw_results}\n\n"
        "Please summarize and answer the user question clearly based on the above search results and prior information."
    )

    try:
        answer = model.generate(prompt)
        return answer
    except Exception as e:
        return f"{raw_results}\n\n[Error generating summary: {e}]"
