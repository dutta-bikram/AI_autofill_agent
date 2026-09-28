"""Browser automation module for AI Autofill Agent using Playwright.
"""
from browser.controller import BrowserController
from browser.extractor import FormFieldExtractor, FormField
from browser.actions import BrowserActionHandler

__all__ = ["BrowserController", "FormFieldExtractor", "FormField", "BrowserActionHandler"]
