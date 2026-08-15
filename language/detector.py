"""Automatic language detection for JARVIS 2.0.

Supports:
- English
- Urdu (Perso-Arabic script)
- Roman Urdu (Latin-script Urdu)
- Hinglish / Urdu-English mixed
- Auto-detection from STT transcripts or typed input
"""

from __future__ import annotations

import re

# Urdu Unicode ranges
_URDU_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
# Roman Urdu / Hinglish keywords
_ROMAN_URDU_KEYWORDS = {
    'kya', 'kaise', 'kahan', 'kab', 'kyun', 'karna', 'karo', 'kholo', 'khol',
    'chahiye', 'hai', 'nahi', 'nahin', 'please', 'thoda', 'bahut', 'zyada',
    'kam', 'bhai', 'bhaiya', 'aap', 'tum', 'main', 'mera', 'tumhara',
    'batao', 'bata', 'suno', 'sun', 'dekh', 'dekho', 'chal', 'chalo',
    'ruk', 'ruko', 'aao', 'aaja', 'jao', 'ja', 'le', 'lo', 'do', 'de',
    'kar', 'karte', 'karta', 'karti', 'kar raha', 'kar rahi', 'karunga',
    'karungi', 'kardunga', 'kardungi', 'theek', 'thik', 'accha', 'achha',
    'bura', 'ganda', 'sahi', 'galat', 'jaldi', 'dhyaan', 'dhyan',
    'system', 'status', 'battery', 'cpu', 'ram', 'disk', 'file', 'folder',
    'browser', 'firefox', 'chrome', 'terminal', 'command', 'run', 'execute',
    'open', 'close', 'launch', 'search', 'find', 'create', 'make', 'delete',
    'read', 'write', 'install', 'update', 'download', 'upload', 'send',
    'receive', 'call', 'message', 'email', 'notification', 'reminder',
}
_ENGLISH_KEYWORDS = {
    'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
    'should', 'may', 'might', 'must', 'can', 'could', 'a', 'an', 'and',
    'but', 'or', 'nor', 'for', 'yet', 'so', 'in', 'on', 'at', 'to', 'from',
    'by', 'with', 'without', 'about', 'above', 'below', 'into', 'out',
    'up', 'down', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
    'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
    'only', 'own', 'same', 'than', 'too', 'very', 'just', 'because',
    'as', 'until', 'while', 'although', 'though', 'even', 'if', 'unless',
    'whether', 'while', 'since', 'during', 'before', 'after', 'above',
    'below', 'between', 'among', 'through', 'during', 'before', 'after',
    'open', 'close', 'run', 'execute', 'search', 'find', 'create', 'make',
    'delete', 'read', 'write', 'install', 'update', 'download', 'send',
    'please', 'thank', 'thanks', 'sorry', 'hello', 'hi', 'hey', 'good',
    'morning', 'evening', 'night', 'yes', 'no', 'ok', 'okay', 'sure',
    'help', 'what', 'when', 'where', 'who', 'why', 'how', 'which',
}


def detect_language(text: str) -> str:
    """Detect language of input text.

    Returns one of:
      - 'en' (English)
      - 'ur' (Urdu / Perso-Arabic script)
      - 'roman_urdu' (Roman Urdu / Hinglish)
      - 'mixed' (mixed Urdu + English)
    """
    if not text or not text.strip():
        return 'en'

    text_lower = text.lower()
    words = re.findall(r'[a-zA-Z]+', text_lower)
    urdu_chars = _URDU_RE.findall(text)

    has_urdu_script = len(urdu_chars) > 0
    has_roman_urdu = any(w in _ROMAN_URDU_KEYWORDS for w in words)
    has_english = any(w in _ENGLISH_KEYWORDS for w in words)

    if has_urdu_script and has_english:
        return 'mixed'
    if has_urdu_script:
        return 'ur'
    if has_roman_urdu and not has_english:
        return 'roman_urdu'
    if has_roman_urdu and has_english:
        return 'mixed'
    return 'en'


def normalize_language(lang: str) -> str:
    """Normalize language code to standard set."""
    lang = lang.strip().lower()
    mapping = {
        'english': 'en',
        'en': 'en',
        'urdu': 'ur',
        'ur': 'ur',
        'roman': 'roman_urdu',
        'roman_urdu': 'roman_urdu',
        'roman-urdu': 'roman_urdu',
        'hinglish': 'mixed',
        'mixed': 'mixed',
        'auto': 'auto',
    }
    return mapping.get(lang, 'en')


def language_name(code: str) -> str:
    names = {
        'en': 'English',
        'ur': 'Urdu',
        'roman_urdu': 'Roman Urdu',
        'mixed': 'Hinglish / Mixed',
        'auto': 'Auto Detect',
    }
    return names.get(code, code)
