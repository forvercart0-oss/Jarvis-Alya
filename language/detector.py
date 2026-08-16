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
    'chahiye', 'hai', 'nahi', 'nahin', 'thoda', 'bahut', 'zyada',
    'kam', 'bhai', 'bhaiya', 'aap', 'tum', 'main', 'mera', 'tumhara',
    'batao', 'bata', 'suno', 'sun', 'dekh', 'dekho', 'chal', 'chalo',
    'ruk', 'ruko', 'aao', 'aaja', 'jao', 'ja', 'le', 'lo', 'do', 'de',
    'kar', 'karte', 'karta', 'karti', 'kar raha', 'kar rahi', 'karunga',
    'karungi', 'kardunga', 'kardungi', 'theek', 'thik', 'accha', 'achha',
    'bura', 'ganda', 'sahi', 'galat', 'jaldi', 'dhyaan', 'dhyan',
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
    'whether', 'since', 'during', 'before', 'after', 'between', 'among', 'through', 'open', 'close', 'run', 'execute', 'search', 'find', 'create', 'make',
    'delete', 'read', 'write', 'install', 'update', 'download', 'send',
    'please', 'thank', 'thanks', 'sorry', 'hello', 'hi', 'hey', 'good',
    'morning', 'evening', 'night', 'yes', 'ok', 'okay', 'sure',
    'help', 'what', 'who', 'which',
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
    roman_urdu_count = sum(1 for w in words if w in _ROMAN_URDU_KEYWORDS)
    english_count = sum(1 for w in words if w in _ENGLISH_KEYWORDS)

    if has_urdu_script and english_count > 0:
        return 'mixed'
    if has_urdu_script:
        return 'ur'
    if roman_urdu_count > english_count:
        return 'roman_urdu'
    if roman_urdu_count > 0 and english_count > 0:
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
