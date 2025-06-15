import asyncio
import json
import re
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from core.model_interface import OllamaModel
from urllib.parse import quote
import requests

API_KEY = "AIzaSyAGkMGwlmkJlYkwqS0CDSGN7vKD_a9yick"
CX = "b413f8a3b3ee1482d"

class Researcher:
    def __init__(self, command: str, model: OllamaModel):
        self.command = command
        self.model = model
        self.visited_urls = set()
        self.visited_results = []  # store {"url", "content", "relevant"} per page
        self.banned_domains = ["healthline.com", "facebook.com", "pinterest.com", "instagram.com"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/113.0.0.0 Safari/537.36"
        }

    async def google_search(self, query: str, num_results: int = 10):
        def do_search():
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": API_KEY,
                "cx": CX,
                "q": query,
                "num": num_results,
            }
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
                for item in data.get("items", [])
            ]

        return await asyncio.to_thread(do_search)

    async def scrape_page(self, url: str) -> str:
        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except Exception as e:
                print(f"[!] Failed to fetch {url}: {e}")
                return ""

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

    async def is_relevant(self, content: str) -> bool:
        prompt = f"""
You are a research assistant.

User query: "{self.command}"

Please answer only "yes" or "no".

Is the following content relevant to the query?

Content (first 1000 chars):
{content[:1000]}
"""
        response = await asyncio.to_thread(self.model.generate, prompt)
        answer = response.strip().lower()
        return answer.startswith("yes")

    async def research(self, query: Optional[str] = None) -> str:
        query = query or self.command
        max_rounds = 3

        for round_number in range(1, max_rounds + 1):
            print(f"[🔍 Round {round_number}] Searching for: {query}")
            search_results = await self.google_search(query)

            candidate_urls = [
                r["link"] for r in search_results
                if r["link"] not in self.visited_urls
                and not any(domain in r["link"] for domain in self.banned_domains)
            ]

            if not candidate_urls:
                print("[!] No new URLs to visit, stopping.")
                break

            for url in candidate_urls:
                print(f"[>] Visiting URL: {url}")
                self.visited_urls.add(url)
                content = await self.scrape_page(url)
                if not content:
                    print("[-] Failed to retrieve content, skipping.")
                    continue

                relevant = await self.is_relevant(content)
                print(f"[?] Content relevance: {'YES' if relevant else 'NO'}")

                self.visited_results.append({
                    "url": url,
                    "content": content,
                    "relevant": relevant
                })

                if relevant and sum(1 for r in self.visited_results if r["relevant"]) >= 5:
                    print("[>] Enough relevant content gathered, stopping search.")
                    break

            if sum(1 for r in self.visited_results if r["relevant"]) >= 5:
                break

        relevant_sources = [
            entry for entry in self.visited_results if entry["relevant"] and entry["content"]
        ]

        if not relevant_sources:
            print("[!] No relevant content found after all rounds.")
            return "No relevant information found."

        print(f"[>] Generating final summary from {len(relevant_sources[:5])} sources...")

        sources_content = "\n\n---\n\n".join(
            f"[URL: {entry['url']}]\n{entry['content']}" for entry in relevant_sources[:5]
        )
        source_list = "\n".join(f"- {entry['url']}" for entry in relevant_sources[:5])

        final_prompt = (
            f"You are an AI researcher tasked with writing a structured research report based on real, verified information retrieved from the internet. "
            f"The following are excerpts from actual web sources relevant to the query: '{self.command}'.\n\n"
            f"{sources_content}\n\n"
            f"Instructions:\n"
            f"- Carefully read and synthesize all the provided content.\n"
            f"- Write a clear, detailed, and structured research report that covers all key points and findings.\n"
            f"- Ensure the report is comprehensive and grounded in facts from the provided sources.\n"
            f"- Attribute insights or data to the sources where relevant (e.g., 'According to Source 1…').\n"
            f"- Conclude with a brief summary of your findings.\n"
            f"- At the end of the report, include a 'Sources' section listing the original URLs used.\n\n"
            f"Sources:\n{source_list}\n\n"
            f"Begin the research report now."
        )

        final_response = await asyncio.to_thread(self.model.generate, final_prompt)
        print("\n✅ Final AI Response:\n", final_response.strip())
        return final_response.strip()
