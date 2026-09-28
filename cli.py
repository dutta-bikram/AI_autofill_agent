import asyncio
import argparse
import sys
import threading
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from config import settings
from memory.profile_store import ProfileStore
from memory.vector_store import RAGMemoryStore
from memory.document_loader import DocumentLoader
from browser.controller import BrowserController
from agent.autofill_engine import AutofillEngine
from agent.llm_provider import get_llm_provider
from hitl.review_manager import HITLReviewManager

console = Console(safe_box=True)

def run_local_server():
    from server.app import app
    uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT, log_level="warning")

async def run_autofill_cli(url: str, headless: bool = False, auto_approve: bool = False):
    console.print(Panel.fit(
        "[bold cyan]AI Autofill Agent[/bold cyan]\n"
        "[dim]Playwright | RAG Memory | LLM Reasoning | Human-in-the-Loop Verification[/dim]",
        border_style="cyan"
    ))

    # 1. Initialize Memory & Documents
    console.print("\n[bold]1. Initializing Memory & Knowledge Base...[/bold]")
    profile_store = ProfileStore()
    vector_store = RAGMemoryStore()
    doc_loader = DocumentLoader(vector_store)
    
    if settings.DOCUMENTS_DIR.exists():
        loaded = doc_loader.load_directory(settings.DOCUMENTS_DIR)
        console.print(f"  [green][OK][/green] Loaded {loaded} document chunk(s) from {settings.DOCUMENTS_DIR}")
    
    console.print(f"  [green][OK][/green] Loaded Profile: [bold]{profile_store.profile.full_name}[/bold] ({profile_store.profile.email})")

    # 2. Launch Browser & Extract Fields
    console.print("\n[bold]2. Launching Playwright Browser & Inspecting Target Form...[/bold]")
    browser_controller = BrowserController(headless=headless, slow_mo=settings.BROWSER_SLOW_MO)
    await browser_controller.start()

    engine = AutofillEngine(
        profile_store=profile_store,
        vector_store=vector_store,
        llm_provider=get_llm_provider(),
        browser_controller=browser_controller
    )

    console.print(f"  [cyan]->[/cyan] Navigating to: [underline]{url}[/underline]")
    plan = await engine.analyze_and_plan(url=url)
    console.print(f"  [green][OK][/green] Perception complete: Detected [bold]{plan.total_fields}[/bold] form field(s).")

    # 3. Human-In-The-Loop Review
    if auto_approve:
        console.print("  [yellow]Auto-approve mode active. Skipping manual verification.[/yellow]")
    else:
        review_mgr = HITLReviewManager(mode=settings.HITL_MODE)
        plan = review_mgr.review_plan_cli(plan)

    approved_count = sum(1 for d in plan.decisions if d.approved)
    if approved_count == 0:
        console.print("[bold red]No fields approved. Aborting autofill.[/bold red]")
        await browser_controller.close()
        return

    # 4. Browser Action Execution
    console.print(f"\n[bold]4. Applying {approved_count} Approved Entries to Browser Session...[/bold]")
    result = await engine.execute_plan(plan)
    console.print(f"  [bold green][OK] Autofill Execution Finished:[/bold green] Filled: {result['filled']}, Skipped: {result['skipped']}, Failed: {result['failed']}")

    # 5. Final Submission Review
    if not auto_approve:
        should_submit = Confirm.ask("\n[bold yellow]Do you want the AI agent to submit the form now?[/bold yellow]", default=False)
    else:
        should_submit = True

    if should_submit:
        console.print("  [cyan]->[/cyan] Submitting form...")
        submitted = await engine.submit_page()
        if submitted:
            console.print("  [bold green][SUCCESS] Form submitted successfully![/bold green]")
        else:
            console.print("  [yellow]Submit element not found or already submitted.[/yellow]")

    if not auto_approve:
        console.print("\n[dim]Press Enter to close browser and exit...[/dim]")
        input()
    await browser_controller.close()
    console.print("[bold green]Agent run finished cleanly.[/bold green]")

def main():
    parser = argparse.ArgumentParser(description="AI Autofill Agent CLI")
    parser.add_argument("--url", type=str, default="", help="Target web form URL")
    parser.add_argument("--demo", action="store_true", help="Launch built-in demo job application form")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve without HITL review prompt")
    args = parser.parse_args()

    target_url = args.url
    if args.demo or not target_url:
        target_url = f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/demo-form"
        # Start demo form server in background thread
        console.print(f"[dim]Starting demo server on {target_url}...[/dim]")
        server_thread = threading.Thread(target=run_local_server, daemon=True)
        server_thread.start()
        import time
        time.sleep(1.2)

    asyncio.run(run_autofill_cli(url=target_url, headless=args.headless, auto_approve=args.auto_approve))

if __name__ == "__main__":
    main()
