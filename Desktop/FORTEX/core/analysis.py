from typing import List, Dict
from core.models import ExecutionResult, CrashSnapshot, ChaosScenario, CapturedRequest
import uuid
from rich.console import Console

console = Console()

class Analyzer:
    @staticmethod
    def analyze_results(results: List[ExecutionResult]) -> List[CrashSnapshot]:
        """
        Analyze execution results for failures.
        """
        crashes = []
        
        for res in results:
            # 1. HTTP 5xx Errors
            if res.response and res.response.status_code >= 500:
                crashes.append(Analyzer._create_snapshot(res, "HTTP_5XX_SERVER_ERROR"))
            
            # 2. Timeouts/Errors
            if res.status == "ERROR":
                crashes.append(Analyzer._create_snapshot(res, "CLIENT_ERROR_OR_TIMEOUT"))
                
            # 3. Performance degradation (Naive check)
            if res.metadata.duration_ms > 5000:  # 5 seconds
                crashes.append(Analyzer._create_snapshot(res, "HIGH_LATENCY"))
        
        # 4. Inconsistency & Race Condition Checks (Batch analysis)
        # Group by scenario to check consistency across parallel requests
        # (TODO: Implement grouping logic)
        
        return crashes

    @staticmethod
    def _create_snapshot(result: ExecutionResult, failure_type: str) -> CrashSnapshot:
        """Helper to create a reproducible snapshot"""
        # Reconstruct context (Simplified for demo)
        dummy_req = CapturedRequest(
           request_id=result.request_id, 
           url="UNKNOWN", 
           method="UNKNOWN"
        ) 
        
        return CrashSnapshot(
            id=str(uuid.uuid4()),
            scenario=ChaosScenario(
                name=result.scenario_name, 
                description="Auto-generated fail", 
                mutation_type=failure_type
            ),
            requests=[dummy_req], 
            results=[result],
            analysis=f"Detected failure type: {failure_type}. Code: {result.response.status_code if result.response else 'N/A'}"
        )

    @staticmethod
    def save_report(crashes: List[CrashSnapshot], filename: str = "reports/crash_report.json"):
        """Save crashes to a JSON file."""
        import json
        import os
        
        os.makedirs("reports", exist_ok=True)
        
        data = [c.model_dump(mode='json') for c in crashes]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
            
        console.print(f"[bold green]Report saved to {filename} ({len(crashes)} crashes detected)[/bold green]")
        
        # Also save Markdown
        md_filename = filename.replace(".json", ".md")
        with open(md_filename, "w") as f:
            f.write(f"# FORTEX Resilience Report\n\n")
            f.write(f"**Total Failures:** {len(crashes)}\n\n")
            f.write(f"## Failure Analysis\n\n")
            
            for c in crashes:
                f.write(f"### {c.scenario.name} ({c.scenario.mutation_type})\n")
                f.write(f"- **Analysis**: {c.analysis}\n")
                if "HTTP_5XX" in c.scenario.mutation_type:
                    f.write(f"- **Heuristic**: Server returned a 5xx error. If this happened during a race condition test, it likely indicates a concurrency bug or resource contention.\n")
                f.write(f"- **Timestamp**: {c.timestamp}\n\n")
                
        console.print(f"[bold green]Markdown report saved to {md_filename}[/bold green]")

    @staticmethod
    def print_summary(results: List[ExecutionResult], crashes: List[CrashSnapshot]):
        """Print a summary of the execution to the console."""
        from rich.table import Table
        
        table = Table(title="Execution Summary")
        table.add_column("Scenario", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Code", style="green")
        table.add_column("Duration (ms)", justify="right")
        
        for res in results:
            code = str(res.response.status_code) if res.response else "N/A"
            table.add_row(res.scenario_name, res.status, code, f"{res.metadata.duration_ms:.2f}")
            
        console.print(table)
        
        if crashes:
            console.print(f"[bold red]!!! DETECTED {len(crashes)} FAILURES !!![/bold red]")
            for c in crashes:
                console.print(f" - {c.scenario.mutation_type}: {c.analysis}")
        else:
            console.print("[bold green]No critical failures detected.[/bold green]")
