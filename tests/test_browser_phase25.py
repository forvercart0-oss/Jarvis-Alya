"""Tests for Phase 25 Browser Intelligence & Web Automation 2.0."""

from __future__ import annotations

import asyncio

import pytest

from browser.browser_anti_loop import AntiLoopState, BrowserAntiLoop
from browser.browser_intelligence import BrowserIntelligenceOrchestrator
from browser.browser_memory import BrowserMemoryStore
from browser.browser_recovery import BrowserRecoveryEngine
from browser.browser_verification import BrowserVerifier
from browser.dom_analyzer import AnalyzedElement, DOMAnalyzer
from browser.download_manager import BrowserDownloadManager, DownloadTask
from browser.element_resolver import ElementResolver, ResolvedElement
from browser.page_diff import PageDiffEngine
from browser.page_inspector import InspectedPage, PageInspector, PageSection
from browser.page_reader import WebPageReader
from browser.page_summarizer import PageSummarizer
from browser.table_extractor import TableExtractor
from browser.upload_manager import BrowserUploadManager


def test_page_inspector_defaults():
    inspector = PageInspector()
    assert inspector.available in (True, False)

def test_page_section_defaults():
    section = PageSection(type="header", text="test")
    assert section.type == "header"
    d = section.to_dict()
    assert d["type"] == "header"

def test_inspected_page_defaults():
    page = InspectedPage()
    assert page.url == ""
    assert page.title == ""
    d = page.to_dict()
    assert "url" in d
    assert "tables" in d

def test_dom_analyzer_defaults():
    analyzer = DOMAnalyzer()
    assert analyzer.available in (True, False)

def test_analyzed_element_defaults():
    el = AnalyzedElement(tag="button", text="Submit", role="button")
    assert el.tag == "button"
    d = el.to_dict()
    assert d["text"] == "Submit"
    assert "selectors" in d

def test_element_resolver_defaults():
    resolver = ElementResolver(confidence_threshold=0.5)
    assert resolver.confidence_threshold == 0.5

def test_resolved_element_defaults():
    el = ResolvedElement(element_type="button", label="Submit", confidence=0.9)
    assert el.element_type == "button"
    d = el.to_dict()
    assert d["confidence"] == 0.9

def test_download_manager():
    mgr = BrowserDownloadManager(download_dir="/tmp/jarvis-test-downloads")
    task = DownloadTask(id="1", filename="test.pdf", url="http://example.com/test.pdf", status="pending")
    mgr.register(task)
    found = mgr.get("1")
    assert found is not None
    assert found.filename == "test.pdf"
    active = mgr.list_active()
    assert len(active) == 1
    completed = mgr.list_completed()
    assert len(completed) == 0
    mgr.update("1", status="complete")
    completed = mgr.list_completed()
    assert len(completed) == 1

def test_upload_manager_validates_sensitive():
    mgr = BrowserUploadManager()
    result = mgr.validate_file("/tmp/test.key")
    assert result.status == "error"

def test_upload_manager_validates_missing():
    mgr = BrowserUploadManager()
    result = mgr.validate_file("/tmp/nonexistent.txt")
    assert result.status == "error"

def test_page_reader_clean_text():
    reader = WebPageReader()
    text = "Skip to main content\n\nHello world\n\nCookie policy\n\nImportant info"
    cleaned = reader._clean_text(text)
    assert "Skip to main content" not in cleaned
    assert "Hello world" in cleaned
    assert "Important info" in cleaned

@pytest.mark.asyncio
async def test_page_summarizer():
    summarizer = PageSummarizer()
    from browser.page_context import PageContext
    ctx = PageContext(
        url="http://example.com",
        title="Example Page",
        visible_text="Introduction\nThis is the introduction paragraph.\nDocs",
        interactive_elements=[],
    )
    ctx.headings = [{"text": "Introduction", "level": 1}]
    ctx.paragraphs = ["This is the introduction paragraph."]
    ctx.links = [{"text": "Docs", "href": "http://example.com/docs"}]
    result = await summarizer.summarize(ctx)
    assert result["success"] is True
    assert result["title"] == "Example Page"

def test_table_extractor_empty():
    extractor = TableExtractor()
    assert extractor.table_to_markdown({}) == ""

def test_page_diff_engine():
    engine = PageDiffEngine()
    diff = engine.diff("http://a.com", "Title A", "text A", [{"text": "btn1"}])
    assert diff.has_changes is False
    diff2 = engine.diff("http://b.com", "Title B", "text B", [{"text": "btn2"}])
    assert diff2.has_changes is True
    assert diff2.url_changed is True

def test_page_diff_reset():
    engine = PageDiffEngine()
    engine.diff("http://a.com", "Title A", "text A", [{"text": "btn1"}])
    engine.reset()
    diff = engine.diff("http://a.com", "Title A", "text A", [{"text": "btn1"}])
    assert diff.has_changes is False

def test_browser_verifier():
    verifier = BrowserVerifier()

    class FakePage:
        url = "http://example.com/page"

    page = FakePage()
    result = asyncio.run(verifier.verify_navigation(page, "example.com/page"))
    assert result["success"] is True

def test_browser_recovery():
    recovery = BrowserRecoveryEngine()
    result = asyncio.run(recovery.recover({"action_type": "click", "target": "submit", "error": "not found"}, None))
    assert "recovery" in result

def test_browser_anti_loop():
    anti = BrowserAntiLoop(max_actions=5, max_retries=2)
    result = anti.check("s1", "click", 10, 0)
    assert result["stop"] is True
    assert result["reason"] == "max_actions_exceeded"

def test_browser_memory():
    store = BrowserMemoryStore()
    mem = store.get("s1")
    assert mem.session_id == "s1"
    mem.record_action("click", "button", "ok")
    assert len(mem.recent_actions) == 1
    mem.set_preference("dark_mode", True)
    assert mem.get_preference("dark_mode") is True
    store.clear("s1")
    mem2 = store.get("s1")
    assert len(mem2.recent_actions) == 0

def test_anti_loop_state_detects_repetition():
    state = AntiLoopState()
    result1 = state.detect_loop("http://a.com", "Title", "text", "click")
    assert result1 is False
    result2 = state.detect_loop("http://a.com", "Title", "text", "click")
    assert result2 is False
    result3 = state.detect_loop("http://a.com", "Title", "text", "click")
    assert result3 is False
    result4 = state.detect_loop("http://a.com", "Title", "text", "click")
    assert result4 is True

def test_browser_intelligence_orchestrator_defaults():
    orch = BrowserIntelligenceOrchestrator()
    assert orch.enabled is False
    assert orch._max_actions == 20
    assert orch._max_retries == 3

def test_resolved_element_to_dict():
    el = ResolvedElement(element_type="input", label="Search", selector="input#search", confidence=0.85)
    d = el.to_dict()
    assert d["element_type"] == "input"
    assert d["confidence"] == 0.85
