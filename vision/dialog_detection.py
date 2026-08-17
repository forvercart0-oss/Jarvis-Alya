"""Dialog detection for JARVIS Phase 30.

Detects common dialog types: confirmation, error, warning, login,
permission, save, open, download, and destructive actions.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.vision.dialog_detection")

_DIALOG_PATTERNS = [
    ("confirmation", re.compile(r"\b(ok|confirm|yes|no|cancel|proceed|accept|agree)\b", re.I)),
    ("error", re.compile(r"\b(error|exception|failed|fatal|critical|traceback)\b", re.I)),
    ("warning", re.compile(r"\b(warning|warn|caution|attention|alert)\b", re.I)),
    ("login", re.compile(r"\b(login|sign in|username|password|email|authenticate)\b", re.I)),
    ("permission", re.compile(r"\b(allow|deny|permission|grant|access|admin|sudo|uac)\b", re.I)),
    ("save", re.compile(r"\b(save|store|write|export|download)\b", re.I)),
    ("open", re.compile(r"\b(open|load|import|browse|choose file)\b", re.I)),
    ("download", re.compile(r"\b(download|save file|save as|saving)\b", re.I)),
]

_DESTRUCTIVE_PATTERNS = [
    re.compile(r"\b(delete|remove|erase|format|factory reset|uninstall|discard|purge)\b", re.I),
]

_CAPTCHA_PATTERNS = [
    re.compile(r"\b(captcha|recaptcha|hcaptcha|verify you are human|prove you are human)\b", re.I),
]


class DialogDetectionResult:
    def __init__(self, dialog_type: str, destructive: bool = False, captcha: bool = False,
                 confidence: float = 0.0, matched_text: str = ""):
        self.dialog_type = dialog_type
        self.destructive = destructive
        self.captcha = captcha
        self.confidence = confidence
        self.matched_text = matched_text

    def to_dict(self) -> dict[str, Any]:
        return {
            "dialog_type": self.dialog_type,
            "destructive": self.destructive,
            "captcha": self.captcha,
            "confidence": self.confidence,
            "matched_text": self.matched_text,
        }


class DialogDetector:
    def detect(self, ocr_text: str, window_title: str = "") -> DialogDetectionResult | None:
        combined = f"{window_title} {ocr_text}".lower()
        best = None
        best_score = 0.0

        for dialog_type, pattern in _DIALOG_PATTERNS:
            matches = pattern.findall(combined)
            if matches:
                score = min(len(matches) * 0.3 + 0.4, 1.0)
                if score > best_score:
                    best_score = score
                    best = DialogDetectionResult(
                        dialog_type=dialog_type,
                        destructive=False,
                        captcha=False,
                        confidence=score,
                        matched_text=matches[0],
                    )

        destructive = False
        captcha = False
        for pattern in _DESTRUCTIVE_PATTERNS:
            if pattern.search(combined):
                destructive = True
                break

        for pattern in _CAPTCHA_PATTERNS:
            if pattern.search(combined):
                captcha = True
                break

        if destructive or captcha or best:
            if not best:
                best = DialogDetectionResult(
                    dialog_type="unknown",
                    destructive=destructive,
                    captcha=captcha,
                    confidence=0.5 if destructive or captcha else 0.0,
                    matched_text="",
                )
            else:
                best.destructive = destructive
                best.captcha = captcha
                if destructive:
                    best.confidence = min(best.confidence + 0.1, 1.0)

        return best


dialog_detector = DialogDetector()
