"""Safety classifier for JARVIS 2.0.

Classifies user requests as safe, unsafe, harmful, or cybersecurity-related.
Uses keyword matching and heuristics with confidence scoring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SafetyCategory(Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"
    HARMFUL = "harmful"
    CYBERSECURITY = "cybersecurity"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyClassification:
    category: SafetyCategory
    confidence: float
    matched_keywords: list[str] = field(default_factory=list)
    subcategory: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    is_exception: bool = False
    exception_reason: Optional[str] = None


# Harmful intent keywords by subcategory
_HARMFUL_PATTERNS: dict[str, list[str]] = {
    "violence": [
        "kill", "murder", "assault", "attack", "hurt", "stab", "shoot",
        "beat up", "torture", "harm someone", "hurt someone", "violent",
        "fight with", "punch", "choke", "strangle",
    ],
    "malware": [
        "ransomware", "trojan", "virus", "worm", "keylogger", "spyware",
        "rootkit", "botnet", "cryptojacking", "backdoor", "exploit kit",
        "create malware", "write virus", "make ransomware", "build trojan",
        "create worm", "develop spyware",
    ],
    "theft": [
        "steal", "rob", "theft", "steal from", "hack into bank", "embezzle",
        "credit card fraud", "stolen data", "identity theft",
        "phishing for passwords", "steal credentials",
    ],
    "unauthorized_access": [
        "brute force", "bruteforce", "crack password", "crack hash",
        "bypass authentication", "bypass login", "hack account",
        "gain access to", "exploit vulnerability for access",
        "break into", "unauthorized access",
    ],
    "fraud": [
        "fake id", "counterfeit", "money laundering", "fake documents",
        "forged", "scam someone", "pyramid scheme", "ponzi",
        "fake invoices", "tax evasion",
    ],
    "weapons": [
        "bomb", "explosive", "chemical weapon", "biological weapon",
        "make a bomb", "build explosive", "pipe bomb", "grenade",
        "improvised explosive", "IED", "weaponize",
    ],
    "illegal_activities": [
        "drug trafficking", "sell drugs", "manufacture drugs",
        "human trafficking", "child abuse", "exploitation",
        "extortion", "blackmail", "kidnapping", "arson",
    ],
    "hate_speech": [
        "hate", "racist", "sexist", "discriminate", "slur",
        "genocide", "ethnic cleansing",
    ],
}

# Cybersecurity exception keywords (legitimate use cases)
_CYBERSEC_EXCEPTIONS: list[str] = [
    "ctf", "capture the flag", "cybersecurity learning", "ethical hacking",
    "penetration testing", "authorized testing", "bug bounty",
    "vulnerability assessment", "security research", "defensive security",
    "security audit", "red team", "blue team", "purple team",
    "certification", "oscp", "ceh", "cissp", "comptia security",
    "learn cybersecurity", "study cybersecurity", "cyber security course",
    "security lab", "hack the box", "tryhackme", "portswigger",
    "owasp", "security training", "educational", "for learning",
    "in a lab", "test environment", "sandbox", "virtual machine",
    "legitimate security", "authorized penetration test",
]


@dataclass
class SafetyClassifier:
    """Classifies user requests for safety."""

    # Thresholds
    unsafe_confidence_threshold: float = 0.25
    harmful_confidence_threshold: float = 0.40
    cybersecurity_confidence_threshold: float = 0.40

    def classify(self, text: str) -> SafetyClassification:
        """Classify a user request.

        Returns SafetyClassification with category, confidence, and details.
        """
        if not text or not text.strip():
            return SafetyClassification(
                category=SafetyCategory.SAFE,
                confidence=1.0,
                severity=Severity.LOW,
            )

        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        # Check cybersecurity exceptions first
        exception_match = self._check_exceptions(text_lower)
        if exception_match:
            # Even if harmful keywords are present, if it's a clear exception,
            # classify as cybersecurity/safe
            harm_score, _, _ = self._calculate_harm_score(text_lower, words)
            if harm_score < self.harmful_confidence_threshold:
                return SafetyClassification(
                    category=SafetyCategory.CYBERSECURITY,
                    confidence=0.8,
                    subcategory=exception_match,
                    is_exception=True,
                    exception_reason=f"Legitimate cybersecurity activity: {exception_match}",
                    severity=Severity.LOW,
                )

        # Calculate harmful score
        harm_score, matched_keywords, subcategory = self._calculate_harm_score(
            text_lower, words
        )

        if harm_score >= self.harmful_confidence_threshold:
            severity = Severity.CRITICAL if harm_score >= 0.85 else Severity.HIGH
            return SafetyClassification(
                category=SafetyCategory.HARMFUL,
                confidence=harm_score,
                matched_keywords=matched_keywords,
                subcategory=subcategory,
                severity=severity,
            )

        if harm_score >= self.unsafe_confidence_threshold:
            return SafetyClassification(
                category=SafetyCategory.UNSAFE,
                confidence=harm_score,
                matched_keywords=matched_keywords,
                subcategory=subcategory,
                severity=Severity.MEDIUM,
            )

        # Check for cybersecurity content without harmful intent
        cybersec_match = self._check_cybersec_keywords(text_lower)
        if cybersec_match:
            return SafetyClassification(
                category=SafetyCategory.CYBERSECURITY,
                confidence=0.6,
                subcategory=cybersec_match,
                severity=Severity.LOW,
            )

        return SafetyClassification(
            category=SafetyCategory.SAFE,
            confidence=1.0 - harm_score,
            severity=Severity.LOW,
        )

    def _check_exceptions(self, text_lower: str) -> Optional[str]:
        """Check if text contains cybersecurity exception keywords."""
        for exc in _CYBERSEC_EXCEPTIONS:
            if exc in text_lower:
                return exc
        return None

    def _check_cybersec_keywords(self, text_lower: str) -> Optional[str]:
        """Check for cybersecurity-related keywords."""
        cybersec_terms = {
            "vulnerability": "vulnerability research",
            "exploit": "exploit analysis",
            "penetration test": "penetration testing",
            "security audit": "security auditing",
            "port scan": "port scanning",
            "nmap": "network scanning",
            "sql injection": "SQL injection testing",
            "xss": "XSS testing",
            "csrf": "CSRF testing",
            "buffer overflow": "buffer overflow research",
            "reverse engineering": "reverse engineering",
            "malware analysis": "malware analysis",
            "forensics": "digital forensics",
        }
        for term, category in cybersec_terms.items():
            if term in text_lower:
                return category
        return None

    def _calculate_harm_score(
        self, text_lower: str, words: set[str]
    ) -> tuple[float, list[str], Optional[str]]:
        """Calculate harm score based on keyword matches.

        Returns (score, matched_keywords, subcategory).
        """
        total_score = 0.0
        matched: list[str] = []
        found_subcategory: Optional[str] = None

        for subcategory, keywords in _HARMFUL_PATTERNS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matched.append(keyword)
                    if len(keyword.split()) > 1:
                        weight = 0.55
                    else:
                        weight = 0.40 + min(len(keyword) * 0.02, 0.20)
                    total_score = min(total_score + weight, 1.0)
                    if found_subcategory is None:
                        found_subcategory = subcategory

        text_length = len(text_lower.split())
        if text_length > 15:
            length_factor = min(1.0, (text_length - 15) / 30.0)
            total_score *= (1.0 - length_factor * 0.25)

        return min(total_score, 1.0), matched, found_subcategory

    def is_harmful(self, text: str) -> bool:
        """Quick check if text is harmful."""
        result = self.classify(text)
        return result.category == SafetyCategory.HARMFUL

    def is_safe(self, text: str) -> bool:
        """Quick check if text is safe."""
        result = self.classify(text)
        return result.category == SafetyCategory.SAFE


_safety_classifier = SafetyClassifier()


def classify_request(text: str) -> SafetyClassification:
    """Classify a user request using the global classifier."""
    return _safety_classifier.classify(text)
