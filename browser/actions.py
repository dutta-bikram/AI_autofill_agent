import asyncio
from typing import Optional, List
from browser.extractor import FormField

class BrowserActionHandler:
    """Performs resilient and human-like form filling actions on a Playwright page."""

    def __init__(self, page, slow_mo_ms: int = 150, highlight: bool = True):
        self.page = page
        self.slow_mo_ms = slow_mo_ms
        self.highlight = highlight

    async def highlight_element(self, selector: str, color: str = "#10b981"):
        """Temporarily highlights an element with a glowing border to visualize agent action."""
        if not self.highlight:
            return
        js = """
        ({selector, color}) => {
            const el = document.querySelector(selector);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                const originalOutline = el.style.outline;
                const originalBoxShadow = el.style.boxShadow;
                el.style.outline = `3px solid ${color}`;
                el.style.boxShadow = `0 0 15px ${color}`;
                setTimeout(() => {
                    el.style.outline = originalOutline;
                    el.style.boxShadow = originalBoxShadow;
                }, 2000);
            }
        }
        """
        try:
            await self.page.evaluate(js, {"selector": selector, "color": color})
        except Exception:
            pass

    async def fill_field(self, field: FormField, value: str) -> bool:
        """Fills a single form field according to its type and selector."""
        if value is None or str(value).strip() == "":
            return False

        value_str = str(value).strip()
        selector = field.selector

        try:
            # 1. Scroll and highlight
            await self.highlight_element(selector, color="#3b82f6")
            await asyncio.sleep(self.slow_mo_ms / 1000.0)

            # 2. Handle Text, Textarea, Number, Email, Tel, Date, Password
            if field.element_type in ["text", "textarea", "number", "email", "tel", "url", "password", "date"]:
                locator = self.page.locator(selector).first
                await locator.scroll_into_view_if_needed()
                await locator.fill(value_str)
                # Dispatch change and input events
                await locator.dispatch_event("input")
                await locator.dispatch_event("change")
                await self.highlight_element(selector, color="#10b981")
                return True

            # 3. Handle Select Dropdowns
            elif field.element_type == "select":
                locator = self.page.locator(selector).first
                # Try selecting by label, value, or index
                options = await locator.locator("option").all_inner_texts()
                matched_option = None
                for opt in options:
                    if value_str.lower() in opt.lower() or opt.lower() in value_str.lower():
                        matched_option = opt.strip()
                        break
                
                if matched_option:
                    await locator.select_option(label=matched_option)
                else:
                    try:
                        await locator.select_option(value=value_str)
                    except Exception:
                        await locator.select_option(index=1)
                
                await locator.dispatch_event("change")
                await self.highlight_element(selector, color="#10b981")
                return True

            # 4. Handle Radio Groups
            elif field.element_type == "radio":
                # Find the radio whose label or value matches
                radios = await self.page.locator(selector).all()
                for r in radios:
                    r_val = await r.get_attribute("value") or ""
                    # Check text content of parent or sibling
                    r_id = await r.get_attribute("id")
                    label_text = ""
                    if r_id:
                        lbl = self.page.locator(f"label[for='{r_id}']")
                        if await lbl.count() > 0:
                            label_text = await lbl.first.inner_text()
                    if not label_text:
                        parent_text = await r.evaluate("el => el.parentElement ? el.parentElement.innerText : ''")
                        label_text = parent_text

                    if (value_str.lower() in r_val.lower()) or (value_str.lower() in label_text.lower()) or (r_val.lower() in value_str.lower()):
                        await r.scroll_into_view_if_needed()
                        await r.check()
                        await r.dispatch_event("change")
                        await self.highlight_element(selector, color="#10b981")
                        return True

                # If no direct match, check the first one if value is affirmative
                if value_str.lower() in ["yes", "true", "1"] and len(radios) > 0:
                    await radios[0].check()
                    return True
                elif value_str.lower() in ["no", "false", "0"] and len(radios) > 1:
                    await radios[1].check()
                    return True

            # 5. Handle Checkbox
            elif field.element_type == "checkbox":
                locator = self.page.locator(selector).first
                should_check = value_str.lower() in ["true", "yes", "1", "agree", "checked", "on"]
                if should_check:
                    await locator.check()
                else:
                    await locator.uncheck()
                await locator.dispatch_event("change")
                await self.highlight_element(selector, color="#10b981")
                return True

        except Exception as e:
            print(f"[BrowserActionHandler] Failed to fill {field.label or field.name} ({selector}): {e}")
            return False

        return False
