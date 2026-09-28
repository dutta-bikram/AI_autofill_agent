import sys
import argparse
import uvicorn
from rich.console import Console
from rich.panel import Panel
from config import settings

console = Console()

def run_web(host: str = settings.SERVER_HOST, port: int = settings.SERVER_PORT):
    console.print(Panel.fit(
        f"[bold cyan]AI Autofill Agent &bull; Web Dashboard[/bold cyan]\n"
        f"[green]Dashboard URL:[/green] [underline]http://{host}:{port}[/underline]\n"
        f"[green]Built-in Demo Form:[/green] [underline]http://{host}:{port}/demo-form[/underline]\n\n"
        f"[dim]Features: Playwright Browser Control &bull; RAG Memory &bull; Human-In-The-Loop Verification[/dim]",
        border_style="cyan"
    ))
    uvicorn.run("server.app:app", host=host, port=port, reload=False)

def main():
    parser = argparse.ArgumentParser(description="AI Autofill Agent Runner")
    parser.add_argument("--mode", choices=["web", "cli"], default="web", help="Launch mode: 'web' or 'cli'")
    parser.add_argument("--url", type=str, default="", help="Target URL (for cli mode)")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo form (for cli mode)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--port", type=int, default=settings.SERVER_PORT, help="Port for web server")
    args = parser.parse_args()

    if args.mode == "cli" or args.url or args.demo:
        from cli import main as cli_main
        cli_main()
    else:
        run_web(port=args.port)

if __name__ == "__main__":
    main()
