from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FormField(BaseModel):
    id: str
    name: str = ""
    label: str = ""
    element_type: str = "text"  # text, textarea, select, radio, checkbox, number, email, tel, date
    tag_name: str = "input"
    placeholder: str = ""
    required: bool = False
    options: List[str] = Field(default_factory=list)  # for select or radio groups
    current_value: str = ""
    selector: str = ""
    is_visible: bool = True
    context_hint: str = ""  # any surrounding helper text, aria-describedby, etc.

class FormFieldExtractor:
    """Extracts interactive form fields from the DOM via Playwright."""

    # JavaScript snippet executed directly inside the browser context
    EXTRACT_JS = """
    () => {
        const fields = [];
        const seenRadios = new Set();

        function cleanText(str) {
            return str ? str.replace(/\\s+/g, ' ').trim() : '';
        }

        function findLabel(el) {
            // 1. Check aria-label
            if (el.getAttribute('aria-label')) {
                return cleanText(el.getAttribute('aria-label'));
            }

            // 2. Check aria-labelledby
            const labelledBy = el.getAttribute('aria-labelledby');
            if (labelledBy) {
                const labelEl = document.getElementById(labelledBy);
                if (labelEl) return cleanText(labelEl.innerText || labelEl.textContent);
            }

            // 3. Check for matching <label for="id">
            if (el.id) {
                const labelEl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                if (labelEl) return cleanText(labelEl.innerText || labelEl.textContent);
            }

            // 4. Check enclosing <label>
            const parentLabel = el.closest('label');
            if (parentLabel) {
                // Clone and remove inputs inside to get pure text
                const clone = parentLabel.cloneNode(true);
                const innerInputs = clone.querySelectorAll('input, select, textarea, button');
                innerInputs.forEach(i => i.remove());
                const txt = cleanText(clone.innerText || clone.textContent);
                if (txt) return txt;
            }

            // 5. Check placeholder
            if (el.placeholder) {
                return cleanText(el.placeholder);
            }

            // 6. Check preceding sibling or parent container label
            let prev = el.previousElementSibling;
            while (prev) {
                if (['LABEL', 'P', 'SPAN', 'DIV', 'H3', 'H4', 'H5'].includes(prev.tagName)) {
                    const txt = cleanText(prev.innerText || prev.textContent);
                    if (txt && txt.length < 150) return txt;
                }
                prev = prev.previousElementSibling;
            }

            // 7. Check parent container heading or label
            const formGroup = el.closest('.form-group, .field, .input-group, div, fieldset');
            if (formGroup) {
                const legend = formGroup.querySelector('legend');
                if (legend) return cleanText(legend.innerText || legend.textContent);
                const lbl = formGroup.querySelector('label');
                if (lbl) return cleanText(lbl.innerText || lbl.textContent);
            }

            // 8. Fallback to name or id
            return el.name || el.id || '';
        }

        function getContextHint(el) {
            const describedBy = el.getAttribute('aria-describedby');
            if (describedBy) {
                const descEl = document.getElementById(describedBy);
                if (descEl) return cleanText(descEl.innerText);
            }
            const parent = el.closest('.form-group, .field, div');
            if (parent) {
                const help = parent.querySelector('.help-text, .form-text, small, span.hint');
                if (help) return cleanText(help.innerText);
            }
            return '';
        }

        // Query all form inputs, textareas, selects
        const elements = document.querySelectorAll('input, select, textarea');

        for (let i = 0; i < elements.length; i++) {
            const el = elements[i];
            const tag = el.tagName.toLowerCase();
            const type = (el.getAttribute('type') || (tag === 'textarea' ? 'textarea' : (tag === 'select' ? 'select' : 'text'))).toLowerCase();

            // Ignore hidden, submit, button, reset inputs
            if (['hidden', 'submit', 'button', 'reset', 'image'].includes(type)) {
                continue;
            }

            // Ignore invisible elements
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0' || el.offsetWidth === 0 && el.offsetHeight === 0) {
                // Keep if parent is not display none (might be custom styled radio)
                if (type !== 'radio' && type !== 'checkbox') continue;
            }

            // Radio button grouping
            if (type === 'radio') {
                const groupName = el.name || el.id;
                if (!groupName || seenRadios.has(groupName)) {
                    continue;
                }
                seenRadios.add(groupName);

                const radioGroup = document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`);
                const options = [];
                let groupLabel = '';

                // Try to find fieldset legend or parent question
                const fieldset = el.closest('fieldset');
                if (fieldset) {
                    const legend = fieldset.querySelector('legend');
                    if (legend) groupLabel = cleanText(legend.innerText);
                }
                if (!groupLabel) {
                    groupLabel = findLabel(el);
                }

                radioGroup.forEach(r => {
                    const rLbl = findLabel(r) || r.value;
                    options.push(cleanText(rLbl) || r.value);
                });

                fields.push({
                    id: el.id || `radio_${groupName}`,
                    name: el.name || groupName,
                    label: groupLabel || groupName,
                    element_type: 'radio',
                    tag_name: tag,
                    placeholder: '',
                    required: el.required || false,
                    options: options,
                    current_value: Array.from(radioGroup).find(r => r.checked)?.value || '',
                    selector: `input[type="radio"][name="${CSS.escape(el.name)}"]`,
                    is_visible: true,
                    context_hint: getContextHint(el)
                });
                continue;
            }

            // Handle Select element
            let options = [];
            if (tag === 'select') {
                for (let opt of el.options) {
                    if (opt.text.trim()) {
                        options.push(cleanText(opt.text));
                    }
                }
            }

            // Build unique selector
            let selector = '';
            if (el.id) {
                selector = `#${CSS.escape(el.id)}`;
            } else if (el.name) {
                selector = `${tag}[name="${CSS.escape(el.name)}"]`;
            } else {
                selector = `${tag}:nth-of-type(${i + 1})`;
            }

            fields.push({
                id: el.id || el.name || `field_${i}`,
                name: el.name || '',
                label: findLabel(el),
                element_type: tag === 'select' ? 'select' : (tag === 'textarea' ? 'textarea' : type),
                tag_name: tag,
                placeholder: el.placeholder || '',
                required: el.required || el.hasAttribute('aria-required'),
                options: options,
                current_value: el.value || '',
                selector: selector,
                is_visible: true,
                context_hint: getContextHint(el)
            });
        }

        return fields;
    }
    """

    @classmethod
    async def extract_fields(cls, page) -> List[FormField]:
        """Runs the extraction script on a Playwright page and returns parsed FormField objects."""
        raw_fields = await page.evaluate(cls.EXTRACT_JS)
        return [FormField(**f) for f in raw_fields]
