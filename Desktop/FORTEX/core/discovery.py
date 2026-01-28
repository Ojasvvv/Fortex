import asyncio
from typing import List, Set, Dict
from playwright.async_api import async_playwright, Page, Request as PlaywrightRequest
from core.models import CapturedRequest
import uuid
from rich.console import Console

console = Console()

class DiscoveryEngine:
    def __init__(self):
        self.captured_requests: Dict[str, CapturedRequest] = {}
        self.visited_urls: Set[str] = set()
        self.unique_endpoints: Set[str] = set()  # "METHOD:URL" for dedup

    async def _handle_request(self, route, request: PlaywrightRequest):
        """Intercept and log traffic"""
        try:
            # We only care about XHR/Fetch/Document/Form submissions, mostly relative to our target
            # For now, capture everything that looks like an API call or navigation
            # Deduplication key
            key = f"{request.method}:{request.url}"
            
            if key not in self.unique_endpoints:
                self.unique_endpoints.add(key)
                
                # Capture headers and body
                headers = request.headers
                
                # Careful with body capture, might fail for some types
                post_data = request.post_data
                
                captured = CapturedRequest(
                    request_id=str(uuid.uuid4()),
                    url=request.url,
                    method=request.method,
                    headers=headers,
                    body=post_data
                )
                
                self.captured_requests[captured.request_id] = captured
                console.print(f"[cyan]Captured new endpoint:[/cyan] {request.method} {request.url}")
            
            # Continue the request
            await route.continue_()
            
        except Exception as e:
            console.print(f"[red]Error intercepting request:[/red] {e}")
            await route.continue_()

    async def crawl(self, start_url: str, depth: int = 1, headless: bool = True):
        """
        Crawl the target URL to discover endpoints.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            # Enable request interception
            await page.route("**/*", self._handle_request)

            console.print(f"[green]Navigating to {start_url}...[/green]")
            
            try:
                await page.goto(start_url, wait_until="networkidle")
                
                # Simple crawling logic for depth 1 (just the initial page + extracting links if we wanted depth > 1)
                # For this MVP, we will just visit the main page and wait a bit for initial traffic
                
                # Basic interaction to trigger more requests? (Scroll, etc)
                # For now, just wait a bit
                await asyncio.sleep(2)
                
                # TODO: Implement deeper spidering if depth > 1
                # Parsing <a> tags and recursing
                
            except Exception as e:
                console.print(f"[bold red]Crawl failed:[/bold red] {e}")
            finally:
                await browser.close()
        
        return list(self.captured_requests.values())
