import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from browser.extractor import FormField
from browser.controller import BrowserController
from memory.profile_store import ProfileStore
from memory.vector_store import RAGMemoryStore
from agent.llm_provider import LLMProvider, get_llm_provider
from agent.prompts import AUTOFILL_SYSTEM_PROMPT, FIELD_MATCHING_PROMPT
from config import settings

class FormFillDecision(BaseModel):
    field_id: str
    field_label: str
    element_type: str
    proposed_value: str
    confidence: float
    reasoning: str
    source: str  # "profile", "rag_memory", "llm_reasoning"
    approved: bool = True
    edited: bool = False
    original_value: str = ""
    selector: str = ""

class AutofillPlan(BaseModel):
    url: str = ""
    total_fields: int = 0
    decisions: List[FormFillDecision] = Field(default_factory=list)
    average_confidence: float = 0.0

class AutofillEngine:
    """Core autonomous agent coordinating form perception, RAG retrieval, LLM reasoning, HITL review, and browser execution."""

    def __init__(
        self,
        profile_store: Optional[ProfileStore] = None,
        vector_store: Optional[RAGMemoryStore] = None,
        llm_provider: Optional[LLMProvider] = None,
        browser_controller: Optional[BrowserController] = None
    ):
        self.profile_store = profile_store or ProfileStore()
        self.vector_store = vector_store or RAGMemoryStore()
        self.llm_provider = llm_provider or get_llm_provider()
        self.browser_controller = browser_controller or BrowserController()

    async def analyze_and_plan(self, url: Optional[str] = None) -> AutofillPlan:
        """Navigates to URL (if provided), extracts form fields, and generates an AutofillPlan."""
        if url:
            nav_ok = await self.browser_controller.navigate(url)
            if not nav_ok:
                raise RuntimeError(f"Failed to navigate to {url}")
        
        fields = await self.browser_controller.extract_form_fields()
        current_url = self.browser_controller.page.url if self.browser_controller.page else (url or "")
        
        decisions: List[FormFillDecision] = []
        profile_summary = self.profile_store.get_summary_text()

        for field in fields:
            # Query RAG memory store for relevant context based on label, name, and placeholder
            query_str = f"{field.label} {field.placeholder} {field.context_hint}".strip()
            rag_chunks = self.vector_store.query(query_str, top_k=2)
            rag_context_text = "\n\n".join([f"- [Relevance: {c['score']}] {c['content']}" for c in rag_chunks]) if rag_chunks else "No specific documents matched."

            user_prompt = FIELD_MATCHING_PROMPT.format(
                field_name=field.name,
                field_label=field.label or field.name,
                element_type=field.element_type,
                placeholder=field.placeholder,
                required=field.required,
                options=field.options,
                context_hint=field.context_hint,
                profile_summary=profile_summary,
                rag_context=rag_context_text
            )

            try:
                res = await self.llm_provider.generate_json(
                    system_prompt=AUTOFILL_SYSTEM_PROMPT,
                    user_prompt=user_prompt
                )
                suggested_val = str(res.get("suggested_value", "")).strip()
                confidence = float(res.get("confidence", 0.75))
                reasoning = res.get("reasoning", "Extracted based on profile context")
                source = res.get("source", "profile")
            except Exception as e:
                print(f"[AutofillEngine] Reasoning error on {field.label}: {e}")
                suggested_val = ""
                confidence = 0.5
                reasoning = f"Fallback error: {e}"
                source = "fallback"

            decision = FormFillDecision(
                field_id=field.id,
                field_label=field.label or field.name or field.id,
                element_type=field.element_type,
                proposed_value=suggested_val,
                confidence=round(confidence, 2),
                reasoning=reasoning,
                source=source,
                approved=True,
                original_value=suggested_val,
                selector=field.selector
            )
            decisions.append(decision)

        avg_conf = round(sum(d.confidence for d in decisions) / len(decisions), 2) if decisions else 0.0

        return AutofillPlan(
            url=current_url,
            total_fields=len(decisions),
            decisions=decisions,
            average_confidence=avg_conf
        )

    async def execute_plan(self, plan: AutofillPlan, fields_cache: Optional[List[FormField]] = None) -> Dict[str, Any]:
        """Applies approved field entries to the live browser page."""
        if not self.browser_controller.page:
            raise RuntimeError("Browser is not currently active.")

        if not fields_cache:
            fields_cache = await self.browser_controller.extract_form_fields()

        field_map = {f.id: f for f in fields_cache}
        # Also map by selector or name in case id was dynamic
        selector_map = {f.selector: f for f in fields_cache}

        filled_count = 0
        skipped_count = 0
        failed_count = 0
        results = []

        for decision in plan.decisions:
            if not decision.approved:
                skipped_count += 1
                results.append({"field": decision.field_label, "status": "skipped", "value": decision.proposed_value})
                continue

            target_field = field_map.get(decision.field_id) or selector_map.get(decision.selector)
            if not target_field:
                failed_count += 1
                results.append({"field": decision.field_label, "status": "not_found", "value": decision.proposed_value})
                continue

            success = await self.browser_controller.fill_field(target_field, decision.proposed_value)
            if success:
                filled_count += 1
                results.append({"field": decision.field_label, "status": "filled", "value": decision.proposed_value})
            else:
                failed_count += 1
                results.append({"field": decision.field_label, "status": "failed", "value": decision.proposed_value})

        return {
            "total": len(plan.decisions),
            "filled": filled_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "details": results
        }

    async def submit_page(self) -> bool:
        """Submits the form on the current page."""
        return await self.browser_controller.submit_form()
