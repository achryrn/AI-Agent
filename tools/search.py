# tools/search.py

import asyncio
import httpx
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Set, Optional
from tools.base_tool import Tool
from memory.buffer_memory import BufferMemory


class IntelligentSearchTool(Tool):
    name = "intelligent_search"
    description = "Performs intelligent web search with iterative crawling using conversation context"

    def __init__(self, memory: BufferMemory = None):
        self.memory = memory or BufferMemory()
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]
        
        self.search_engines = [
            {"name": "bing", "url": "https://www.bing.com/search", "params": {"q": "{}"}},
            {"name": "duckduckgo", "url": "https://html.duckduckgo.com/html/", "params": {"q": "{}"}}
        ]
        
        self.scraped_urls: Set[str] = set()
        self.collected_data: List[Dict[str, Any]] = []
        self.max_iterations = 3
        self.max_urls_per_iteration = 4
        self.timeout = 10.0
        self.min_content_length = 300

    async def run(self, input: dict) -> str:
        """Main entry point"""
        query = input.get("query", "").strip()
        if not query:
            return "[ERROR] No search query provided."
        
        # Reset state
        self.scraped_urls.clear()
        self.collected_data.clear()
        
        print(f"[Search] Starting search for: {query}")
        
        try:
            # Get initial search results
            urls = await self._search_engines_parallel(query)
            if not urls:
                return f"[Search] No URLs found for query: {query}"
            
            print(f"[Search] Found {len(urls)} URLs to scrape")
            
            # Scrape URLs iteratively
            iteration = 0
            while iteration < self.max_iterations and urls:
                iteration += 1
                print(f"[Search] Iteration {iteration}")
                
                # Take batch of URLs
                batch_urls = urls[:self.max_urls_per_iteration]
                urls = urls[self.max_urls_per_iteration:]
                
                # Scrape batch
                scraped = await self._scrape_batch(batch_urls)
                if scraped:
                    self.collected_data.extend(scraped)
                    print(f"[Search] Scraped {len(scraped)} pages")
                    
                    # Check if we have enough info
                    if self._has_sufficient_info(query):
                        print(f"[Search] Sufficient information after {iteration} iterations")
                        break
                    
                    # Discover more URLs from scraped content
                    new_urls = self._extract_related_urls()
                    urls.extend(new_urls)
                
                await asyncio.sleep(0.5)  # Brief delay
            
            return self._compile_results(query)
            
        except Exception as e:
            return f"[ERROR] Search failed: {str(e)}"

    async def _search_engines_parallel(self, query: str) -> List[str]:
        """Search multiple engines in parallel"""
        tasks = []
        for engine in self.search_engines:
            task = self._search_single_engine(engine, query)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_urls = []
        for result in results:
            if isinstance(result, list):
                all_urls.extend(result)
        
        # Remove duplicates and filter
        unique_urls = []
        seen = set()
        for url in all_urls:
            if url not in seen and self._is_valid_url(url):
                unique_urls.append(url)
                seen.add(url)
        
        return unique_urls[:15]  # Limit total URLs

    async def _search_single_engine(self, engine: Dict[str, Any], query: str) -> List[str]:
        """Search single engine with timeout"""
        try:
            headers = {"User-Agent": random.choice(self.user_agents)}
            
            async with httpx.AsyncClient(
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                
                if engine["name"] == "duckduckgo":
                    response = await client.post(engine["url"], data={"q": query})
                else:
                    params = {"q": query}
                    response = await client.get(engine["url"], params=params)
                
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                return self._extract_search_urls(soup, engine["name"])
                
        except Exception as e:
            print(f"[Search] Engine {engine['name']} failed: {e}")
            return []

    def _extract_search_urls(self, soup: BeautifulSoup, engine_name: str) -> List[str]:
        """Extract URLs from search results"""
        urls = []
        
        # Define selectors for each engine
        selectors = {
            "bing": ['h2 a', '.b_algo h2 a', 'a[href*="http"]'],
            "duckduckgo": ['.result__a', 'a[href*="http"]']
        }
        
        for selector in selectors.get(engine_name, ['a[href*="http"]']):
            try:
                for link in soup.select(selector):
                    href = link.get('href')
                    if href and href.startswith('http'):
                        clean_url = self._clean_url(href)
                        if clean_url:
                            urls.append(clean_url)
            except:
                continue
        
        return list(dict.fromkeys(urls))[:8]  # Remove duplicates, limit

    def _clean_url(self, url: str) -> Optional[str]:
        """Clean tracking parameters from URL"""
        try:
            # Handle redirect URLs
            if '/url?q=' in url:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                if 'q' in parsed:
                    return parsed['q'][0]
            return url
        except:
            return url

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is worth scraping"""
        try:
            parsed = urlparse(url)
            
            if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                return False
            
            # Skip problematic domains
            excluded = ['google.com', 'facebook.com', 'twitter.com', 'youtube.com', 
                       'amazon.com', 'reddit.com', 'pinterest.com']
            
            domain = parsed.netloc.lower()
            if any(ex in domain for ex in excluded):
                return False
            
            # Skip file downloads
            path = parsed.path.lower()
            if any(path.endswith(ext) for ext in ['.pdf', '.doc', '.zip', '.mp4', '.jpg', '.png']):
                return False
            
            return True
        except:
            return False

    async def _scrape_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently"""
        tasks = []
        for url in urls:
            if url not in self.scraped_urls:
                task = self._scrape_url(url)
                tasks.append(task)
        
        if not tasks:
            return []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scraped_data = []
        for result in results:
            if isinstance(result, dict) and result.get('text'):
                scraped_data.append(result)
        
        return scraped_data

    async def _scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape single URL"""
        try:
            self.scraped_urls.add(url)
            
            headers = {"User-Agent": random.choice(self.user_agents)}
            
            async with httpx.AsyncClient(
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                
                response = await client.get(url)
                response.raise_for_status()
                
                if 'html' not in response.headers.get('content-type', ''):
                    return None
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                    tag.decompose()
                
                title = self._extract_title(soup)
                text = self._extract_text(soup)
                links = self._extract_links(soup, url)
                
                if len(text) < self.min_content_length:
                    return None
                
                return {
                    'url': url,
                    'title': title,
                    'text': text,
                    'links': links,
                    'relevance': self._calculate_relevance(title + " " + text)
                }
                
        except Exception as e:
            print(f"[Scraper] Failed {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        try:
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()[:150]
            
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.get_text().strip()[:150]
            
            return "No title"
        except:
            return "No title"

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        try:
            # Try to find main content
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('[role="main"]') or 
                          soup.find('body'))
            
            if not main_content:
                return ""
            
            text = main_content.get_text()
            
            # Clean text
            lines = [line.strip() for line in text.splitlines() if line.strip() and len(line.strip()) > 15]
            clean_text = ' '.join(lines)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            
            return clean_text[:3000]  # Limit length
        except:
            return ""

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract relevant links"""
        try:
            links = []
            for link in soup.find_all('a', href=True)[:10]:  # Limit
                href = link['href']
                full_url = urljoin(base_url, href)
                if self._is_valid_url(full_url):
                    links.append(full_url)
            return links
        except:
            return []

    def _calculate_relevance(self, text: str) -> int:
        """Simple relevance scoring"""
        # This would typically use the original query
        # For now, just return text length as proxy
        return min(len(text) // 100, 10)

    def _extract_related_urls(self) -> List[str]:
        """Extract URLs from scraped content for next iteration"""
        new_urls = []
        
        # Get URLs from recent scrapes
        recent_data = self.collected_data[-2:] if len(self.collected_data) > 1 else self.collected_data
        
        for data in recent_data:
            for link in data.get('links', [])[:2]:  # Limit per page
                if link not in self.scraped_urls:
                    new_urls.append(link)
        
        return new_urls[:5]  # Limit total

    def _has_sufficient_info(self, query: str) -> bool:
        """Check if we have enough information"""
        if len(self.collected_data) < 2:
            return False
        
        total_content = sum(len(data.get('text', '')) for data in self.collected_data)
        avg_relevance = sum(data.get('relevance', 0) for data in self.collected_data) / len(self.collected_data)
        
        # We have enough if we have good content and relevance
        return (len(self.collected_data) >= 3 and total_content > 2000) or \
               (len(self.collected_data) >= 2 and avg_relevance > 5)

    def _compile_results(self, query: str) -> str:
        """Compile final search results"""
        if not self.collected_data:
            return f"[Search] No relevant information found for: {query}"
        
        # Sort by relevance
        sorted_data = sorted(self.collected_data, key=lambda x: x.get('relevance', 0), reverse=True)
        
        result = f"Search Results for: {query}\n\n"
        result += f"Found {len(sorted_data)} relevant sources:\n\n"
        
        for i, data in enumerate(sorted_data[:5], 1):  # Top 5 results
            title = data.get('title', 'Unknown')
            url = data.get('url', 'Unknown')
            text = data.get('text', '')
            relevance = data.get('relevance', 0)
            
            result += f"{i}. {title} (Score: {relevance})\n"
            result += f"   URL: {url}\n"
            result += f"   Content: {text[:400]}{'...' if len(text) > 400 else ''}\n\n"
        
        # Summary
        total_content = sum(len(data.get('text', '')) for data in sorted_data)
        result += f"\n[Summary] Processed {len(self.scraped_urls)} URLs, "
        result += f"extracted {len(sorted_data)} relevant sources, "
        result += f"{total_content:,} characters of content.\n"
        
        return result
    @property
    def example_usage(self) -> str:
        return '''
        {
            "query": "best investment opportunities 2025",
            "max_depth": 2
        }
        '''