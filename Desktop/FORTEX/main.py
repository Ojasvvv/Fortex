import typer
import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="FORTEX: Autonomous Chaos Testing System")
console = Console()

@app.command()
def crawl(url: str, depth: int = 1, headless: bool = True):
    """
    Discover target endpoints by crawling a URL.
    """
    from core.discovery import DiscoveryEngine
    
    console.print(f"[bold green]Starting crawl on {url} (Depth: {depth})[/bold green]")
    
    engine = DiscoveryEngine()
    requests = asyncio.run(engine.crawl(url, depth=depth, headless=headless))
    
    console.print(f"[bold blue]Discovered {len(requests)} unique requests.[/bold blue]")
    for req in requests:
        console.print(f" - {req.method} {req.url}")

@app.command()
def attack(url: str, method: str = "GET", scenario: str = "all"):
    """
    Run chaos scenarios against a target.
    """
    from core.models import CapturedRequest
    
    # In a real flow, we'd load these from the discovery phase (JSON file)
    # For this demo, we construct a dummy request or use the URL provided
    
    console.print(f"[bold red]Initiating attack sequence on {url} with scenario: {scenario}[/bold red]")
    
    # specific imports inside command to avoid circular deps or heavy init
    from core.replay import Replayer
    from core.chaos import ChaosEngine
    from core.mutation import Mutator
    import uuid
    
    target_req = CapturedRequest(
        request_id=str(uuid.uuid4()),
        url=url,
        method=method,
        headers={"User-Agent": "FORTEX-Chaos-Agent"},
        body=None
    )
    
    async def run_scenario(req: CapturedRequest, sc_name: str):
        replayer = Replayer()
        chaos = ChaosEngine(replayer)
        results = []
        
        # 1. Baseline
        console.print(f"[yellow]Running baseline request on {req.url}...[/yellow]")
        base_res = await replayer.execute(req, "baseline")
        results.append(base_res)
        
        # 2. Chaos Scenarios
        if sc_name in ["all", "race"]:
            console.print("[bold red]>>> Executing Race Condition...[/bold red]")
            race_results = await chaos.execute_scenario("race_condition", req)
            results.extend(race_results)

        if sc_name in ["all", "double"]:
            console.print("[bold red]>>> Executing Double Submit...[/bold red]")
            double_results = await chaos.execute_scenario("double_submit", req)
            results.extend(double_results)
        
        # 3. Mutation Scenarios
        if sc_name in ["all", "mutation"]:
             console.print("[bold red]>>> Executing Mutations...[/bold red]")
             mutants = Mutator.mutate(req)
             for m in mutants:
                 res = await replayer.execute(m, f"mutation_{m.request_id}")
                 results.append(res)

        await replayer.close()
        return results

    results = asyncio.run(run_scenario(target_req, scenario))
    
    _analyze_and_report(results)

def _analyze_and_report(results):
    from core.analysis import Analyzer
    
    console.print("[bold blue]Analyzing results...[/bold blue]")
    crashes = Analyzer.analyze_results(results)
    Analyzer.print_summary(results, crashes)
    
    if crashes:
        Analyzer.save_report(crashes, f"reports/report_{uuid.uuid4().hex[:8]}.json")

@app.command()
def scan(url: str, depth: int = 1, headless: bool = True):
    """
    Auto-discover endpoints and attack them (Crawl + Chaos).
    """
    from core.discovery import DiscoveryEngine
    from core.models import CapturedRequest
    
    # 1. Discovery
    console.print(f"[bold green]Step 1: Discovering endpoints on {url}...[/bold green]")
    engine = DiscoveryEngine()
    requests = asyncio.run(engine.crawl(url, depth=depth, headless=headless))
    
    if not requests:
        console.print("[bold red]No endpoints found to attack.[/bold red]")
        return

    console.print(f"[bold blue]Found {len(requests)} endpoints. Starting Attack Phase...[/bold blue]")
    
    # 2. Attack Loop
    # We reuse the logic by constructing a cleaner internal function if possible, 
    # but for now we essentially repeat the simple flow or repurpose the existing one.
    # To keep it clean, we'll just implement the loop here using the helper we extracted (conceptually)
    # Actually, I'll essentially inline the attack logic for the batch here since I didn't fully extract it to a global function above recursively.
    # Let's fix the extraction in the 'attack' command first to be globally accessible if needed, 
    # but since I am using replace_file_content, I need to be careful with scope.
    # EASIER APPROACH: Just define `run_scenario` outside or duplicate the small runner logic.
    # I will inline the runner logic here for safety of the edit.
    
    from core.replay import Replayer
    from core.chaos import ChaosEngine
    from core.mutation import Mutator
    import uuid
    
    async def run_scan():
        replayer = Replayer()
        chaos = ChaosEngine(replayer)
        all_results = []
        
        for req in requests:
            console.print(f"\n[bold magenta]Targeting: {req.method} {req.url}[/bold magenta]")
            
            # Baseline
            base_res = await replayer.execute(req, "baseline")
            all_results.append(base_res)
            
            # Only attack interesting methods or if explicitly aggressive
            # For this demo, we attack everything slightly
            
            # Race (only meaningful for state changers usually, but good to test read-races too)
            race_results = await chaos.execute_scenario("race_condition", req)
            all_results.extend(race_results)
            
            # Mutations
            mutants = Mutator.mutate(req)
            for m in mutants:
                res = await replayer.execute(m, f"mutation_{m.request_id}")
                all_results.append(res)
                
        await replayer.close()
        return all_results

    if requests:
        results = asyncio.run(run_scan())
        _analyze_and_report(results)


if __name__ == "__main__":
    app()
