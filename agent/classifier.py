"""Command classifier for JARVIS Phase 15."""

from __future__ import annotations

import logging
import re
from typing import Any

from agent.models import CommandCategory

logger = logging.getLogger("jarvis.agent.classifier")


class CommandClassifier:
    _READ_PATTERNS = [
        r"\bread\b", r"\bcat\b", r"\bls\b", r"\bdir\b", r"\bget\b", r"\bstat\b",
        r"\bgit\s+status\b", r"\bgit\s+log\b", r"\bgit\s+diff\b", r"\bgit\s+show\b",
    ]
    _ANALYZE_PATTERNS = [
        r"\banalyze\b", r"\banalyse\b", r"\bcheck\b", r"\binspect\b", r"\breview\b",
        r"\bdebug\b", r"\bdiagnose\b", r"\bexplain\b", r"\bunderstand\b",
    ]
    _CREATE_PATTERNS = [
        r"\bcreate\b", r"\badd\b", r"\binit\b", r"\bnew\b", r"\bmake\b", r"\bbuild\b",
        r"\btouch\b", r"\bmkdir\b", r"\bgenerate\b",
    ]
    _MODIFY_PATTERNS = [
        r"\bmodify\b", r"\bedit\b", r"\bupdate\b", r"\bchange\b", r"\brewrite\b",
        r"\bpatch\b", r"\brefactor\b", r"\bmove\b", r"\bcopy\b",
    ]
    _DELETE_PATTERNS = [
        r"\bdelete\b", r"\bremove\b", r"\brm\b", r"\bdel\b", r"\berase\b", r"\btrash\b",
        r"\bunlink\b", r"\bdrop\b",
    ]
    _COMMUNICATE_PATTERNS = [
        r"\bsend\b", r"\bmessage\b", r"\bemail\b", r"\breply\b", r"\bpost\b",
        r"\bcomment\b", r"\btweet\b", r"\bshare\b", r"\bnotify\b",
    ]
    _TRANSACTION_PATTERNS = [
        r"\bbuy\b", r"\bpurchase\b", r"\bpay\b", r"\bcheckout\b", r"\btransfer\b",
        r"\bsubscribe\b", r"\bupgrade\b",
    ]
    _SYSTEM_PATTERNS = [
        r"\binstall\b", r"\buninstall\b", r"\bupdate\b", r"\bupgrade\b", r"\brestart\b",
        r"\bshutdown\b", r"\breboot\b", r"\bstart\b", r"\bstop\b", r"\benable\b",
        r"\bdisable\b", r"\bconfigure\b", r"\bsetup\b",
    ]
    _SECURITY_PATTERNS = [
        r"\bpassword\b", r"\bapi[_-]?\s*key\b", r"\btoken\b", r"\bsecret\b", r"\bprivate[_-]?key\b",
        r"\bauth\b", r"\blogin\b", r"\blogout\b", r"\bpermission\b", r"\bacls\b",
        r"\bfirewall\b", r"\bsecurity\b", r"\bencrypt\b", r"\bdecrypt\b",
    ]

    def classify(self, text: str, arguments: dict[str, Any] | None = None) -> CommandCategory:
        combined = text
        if arguments:
            combined += " " + " ".join(str(v) for v in arguments.values() if v)
        combined = combined.lower()

        checks = [
            (CommandCategory.SECURITY, self._SECURITY_PATTERNS),
            (CommandCategory.TRANSACTION, self._TRANSACTION_PATTERNS),
            (CommandCategory.COMMUNICATE, self._COMMUNICATE_PATTERNS),
            (CommandCategory.DELETE, self._DELETE_PATTERNS),
            (CommandCategory.SYSTEM, self._SYSTEM_PATTERNS),
            (CommandCategory.CREATE, self._CREATE_PATTERNS),
            (CommandCategory.MODIFY, self._MODIFY_PATTERNS),
            (CommandCategory.ANALYZE, self._ANALYZE_PATTERNS),
            (CommandCategory.READ, self._READ_PATTERNS),
        ]

        for category, patterns in checks:
            for pattern in patterns:
                if re.search(pattern, combined):
                    return category
        return CommandCategory.READ

    def requires_approval(self, category: CommandCategory, autonomy_level: str = "assisted") -> bool:
        if autonomy_level == "autonomous":
            return category in (
                CommandCategory.DELETE,
                CommandCategory.COMMUNICATE,
                CommandCategory.TRANSACTION,
                CommandCategory.SECURITY,
                CommandCategory.SYSTEM,
            )
        if autonomy_level == "assisted":
            return category in (
                CommandCategory.DELETE,
                CommandCategory.COMMUNICATE,
                CommandCategory.TRANSACTION,
                CommandCategory.SECURITY,
            )
        return True


command_classifier = CommandClassifier()
