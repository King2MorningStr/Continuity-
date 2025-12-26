"""
Entitlement Engine - Premium Access Control
=========================================
Local entitlement state machine with a future-proof hook for external verification.
"""

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "UDAC Portal"
APP_AUTHOR = "Sunni"
STORAGE_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
try:
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # Silent fail - will try again when actually needed

ENTITLEMENT_FILE = os.path.join(STORAGE_DIR, "entitlement_state.json")


@dataclass
class EntitlementState:
    tier: str = "FREE"  # FREE | PREMIUM
    verified: bool = False  # True if verified by external rail in the future


class EntitlementEngine:
    """Single source of truth for feature entitlements."""

    def __init__(self):
        self._lock = threading.RLock()
        self.state = EntitlementState()
        self._load()

    def _load(self):
        if os.path.exists(ENTITLEMENT_FILE):
            try:
                with open(ENTITLEMENT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.state.tier = data.get("tier", "FREE")
                self.state.verified = bool(data.get("verified", False))
            except Exception:
                # Fail closed
                self.state = EntitlementState()

    def _save(self):
        data = {"tier": self.state.tier, "verified": self.state.verified}
        with open(ENTITLEMENT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def is_premium(self) -> bool:
        return self.state.tier.upper() == "PREMIUM"

    def set_tier(self, tier: str, verified: bool = False):
        with self._lock:
            tier = (tier or "FREE").upper()
            if tier not in ("FREE", "PREMIUM"):
                tier = "FREE"
            self.state.tier = tier
            self.state.verified = bool(verified)
            self._save()

    def verify_with_external_provider(self) -> bool:
        """
        Future hook: call Stripe/Play Billing/etc and set tier accordingly.
        For now, returns current state without network calls.
        """
        return self.is_premium()


ENTITLEMENTS = EntitlementEngine()
