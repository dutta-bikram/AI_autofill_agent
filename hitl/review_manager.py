import sys
from typing import Optional, Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from agent.autofill_engine import AutofillPlan, FormFillDecision
from config import settings

class HITLReviewManager:
    """Manages Human-in-the-Loop review workflows via CLI or Web callbacks."""

    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or settings.HITL_MODE
        self.console = Console(safe_box=True)

    def review_plan_cli(self, plan: AutofillPlan) -> AutofillPlan:
        """Presents an interactive terminal review interface to the user."""
        if self.mode == "never":
            self.console.print("[dim]HITL mode is 'never'. Auto-approving all entries.[/dim]")
            return plan

        while True:
            self._render_review_table(plan)

            self.console.print("\n[bold cyan]Human-in-the-Loop Actions:[/bold cyan]")
            self.console.print("  [bold green][A][/bold green] Approve all & Fill Form")
            self.console.print("  [bold yellow][E <index>][/bold yellow] Edit field value (e.g. 'e 3')")
            self.console.print("  [bold magenta][S <index>][/bold magenta] Toggle skip/include field (e.g. 's 2')")
            self.console.print("  [bold red][C][/bold red] Cancel operation")

            choice = Prompt.ask("\nSelect action", default="A").strip()
            choice_upper = choice.upper()

            if choice_upper == "A":
                self.console.print("[bold green][OK] Plan approved by user. Proceeding to fill...[/bold green]")
                return plan

            elif choice_upper == "C":
                self.console.print("[bold red][X] Operation aborted by user.[/bold red]")
                for d in plan.decisions:
                    d.approved = False
                return plan

            elif choice_upper.startswith("E "):
                parts = choice.split(maxsplit=1)
                if len(parts) > 1 and parts[1].isdigit():
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(plan.decisions):
                        target = plan.decisions[idx]
                        new_val = Prompt.ask(
                            f"Enter new value for '[bold]{target.field_label}[/bold]'",
                            default=target.proposed_value
                        )
                        target.proposed_value = new_val
                        target.edited = True
                        target.approved = True
                        self.console.print(f"[green]Updated field #{idx + 1} to: '{new_val}'[/green]")
                    else:
                        self.console.print("[red]Invalid index.[/red]")

            elif choice_upper.startswith("S "):
                parts = choice.split(maxsplit=1)
                if len(parts) > 1 and parts[1].isdigit():
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(plan.decisions):
                        target = plan.decisions[idx]
                        target.approved = not target.approved
                        status = "APPROVED" if target.approved else "SKIPPED"
                        self.console.print(f"[yellow]Field #{idx + 1} is now {status}[/yellow]")
                    else:
                        self.console.print("[red]Invalid index.[/red]")
            else:
                self.console.print("[dim]Command not recognized. Type 'A' to approve, 'E <num>' to edit, or 'C' to cancel.[/dim]")

    def _render_review_table(self, plan: AutofillPlan):
        table = Table(
            title=f"AI Autofill Review & Verification ({plan.total_fields} fields detected)",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Field Label", style="bold white", width=25)
        table.add_column("Type", style="cyan", width=10)
        table.add_column("Proposed Entry", style="green", width=32)
        table.add_column("Confidence", justify="right", width=12)
        table.add_column("Source", style="dim", width=12)
        table.add_column("Status", width=10)

        for i, d in enumerate(plan.decisions, start=1):
            # Confidence color styling
            if d.confidence >= 0.90:
                conf_str = f"[bold green]{int(d.confidence * 100)}%[/bold green]"
            elif d.confidence >= 0.75:
                conf_str = f"[yellow]{int(d.confidence * 100)}%[/yellow]"
            else:
                conf_str = f"[bold red]{int(d.confidence * 100)}%[/bold red]"

            # Status styling
            if not d.approved:
                status_str = "[dim red]SKIP[/dim red]"
            elif d.edited:
                status_str = "[bold yellow]EDITED[/bold yellow]"
            else:
                status_str = "[bold green]READY[/bold green]"

            # Truncate proposed value if very long
            val_display = d.proposed_value
            if len(val_display) > 50:
                val_display = val_display[:47] + "..."

            table.add_row(
                str(i),
                d.field_label,
                d.element_type,
                val_display,
                conf_str,
                d.source,
                status_str
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print(f"[dim]Average Confidence: {int(plan.average_confidence * 100)}% | Target: {plan.url}[/dim]")
