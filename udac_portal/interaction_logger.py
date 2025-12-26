"""
Interaction Logger - Data Trading Layer
=======================================
Stores all interactions for logging, export, and data trading features.
"""

import time
import json
import os
import threading
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict
import csv

# Try to import platformdirs, fallback to temp directory
try:
    from platformdirs import user_data_dir
    APP_NAME = "UDAC Portal"
    APP_AUTHOR = "Sunni"
    STORAGE_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
except ImportError:
    import tempfile
    STORAGE_DIR = os.path.join(tempfile.gettempdir(), "udac_portal")

from udac_portal.entitlement_engine import ENTITLEMENTS

LOGS_DIR = os.path.join(STORAGE_DIR, "logs")
try:
    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # Silent fail - will try again when actually needed


@dataclass
class InteractionEvent:
    """A single interaction event."""
    event_id: str
    event_type: str  # "user_input", "ai_output", "transcript_chunk", "live_mode_change"
    platform_id: str
    timestamp: float = field(default_factory=time.time)
    
    # Content fields
    raw_text: Optional[str] = None
    enriched_text: Optional[str] = None
    continuity_summary: Optional[str] = None
    
    # Metadata
    thread_id: Optional[str] = None
    tokens_added: int = 0
    live_mode: bool = False
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_anonymized(self) -> dict:
        """Create anonymized version for data trading."""
        # Hash the content to create topic signature
        content = self.raw_text or ""
        topic_hash = hashlib.md5(content[:100].encode()).hexdigest()[:8]
        
        return {
            "event_type": self.event_type,
            "platform_id": self.platform_id,
            "timestamp_hour": int(self.timestamp // 3600) * 3600,  # Round to hour
            "topic_signature": topic_hash,
            "content_length": len(content),
            "tokens_added": self.tokens_added,
            "live_mode": self.live_mode,
        }


@dataclass
class DataTradingSettings:
    """User preferences for data trading."""
    trading_enabled: bool = False
    anonymization_level: int = 2  # 1=light, 2=medium, 3=aggressive
    export_raw_logs: bool = False  # Only with explicit consent
    patterns_only: bool = True  # Default: only trade dimensional patterns


class InteractionLogger:
    """
    Logs all interactions for analysis, export, and data trading.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self.events: List[InteractionEvent] = []
        self.trading_settings = DataTradingSettings()
        self.session_start = time.time()
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_platform": defaultdict(int),
            "live_transcript_chunks": 0,
        }
        
        # Storage credits from trading
        self.storage_credits = 0
        self.patterns_exported = 0
        
        self._load_settings()
        print("[InteractionLogger] Initialized")
    
    def _load_settings(self):
        """Load trading settings."""
        settings_file = os.path.join(STORAGE_DIR, "trading_settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(self.trading_settings, k):
                        setattr(self.trading_settings, k, v)
                self.storage_credits = data.get("storage_credits", 0)
                self.patterns_exported = data.get("patterns_exported", 0)
            except Exception as e:
                print(f"[InteractionLogger] Error loading settings: {e}")
    
    def _save_settings(self):
        """Save trading settings."""
        settings_file = os.path.join(STORAGE_DIR, "trading_settings.json")
        data = {
            "trading_enabled": self.trading_settings.trading_enabled,
            "anonymization_level": self.trading_settings.anonymization_level,
            "export_raw_logs": self.trading_settings.export_raw_logs,
            "patterns_only": self.trading_settings.patterns_only,
            "storage_credits": self.storage_credits,
            "patterns_exported": self.patterns_exported,
        }
        with open(settings_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        return f"{int(time.time() * 1000)}_{len(self.events)}"
    
    def log_user_input(self, platform_id: str, raw: str, enriched: str, 
                       continuity_summary: str, tokens_added: int = 0,
                       thread_id: Optional[str] = None):
        """Log user input event."""
        with self._lock:
            event = InteractionEvent(
                event_id=self._generate_event_id(),
                event_type="user_input",
                platform_id=platform_id,
                raw_text=raw,
                enriched_text=enriched,
                continuity_summary=continuity_summary,
                tokens_added=tokens_added,
                thread_id=thread_id,
            )
            self._record_event(event)
    
    def log_platform_user_echo(self, platform_id: str, text: str):
        """Log when platform echoes the user message (ground truth)."""
        with self._lock:
            event = InteractionEvent(
                event_id=self._generate_event_id(),
                event_type="platform_echo",
                platform_id=platform_id,
                raw_text=text,
            )
            self._record_event(event)
    
    def log_ai_output(self, platform_id: str, text: str, thread_id: Optional[str] = None):
        """Log AI output event."""
        with self._lock:
            event = InteractionEvent(
                event_id=self._generate_event_id(),
                event_type="ai_output",
                platform_id=platform_id,
                raw_text=text,
                thread_id=thread_id,
            )
            self._record_event(event)
    
    def log_live_transcript_chunk(self, platform_id: str, text: str):
        """Log live transcript chunk."""
        with self._lock:
            event = InteractionEvent(
                event_id=self._generate_event_id(),
                event_type="transcript_chunk",
                platform_id=platform_id,
                raw_text=text,
                live_mode=True,
            )
            self._record_event(event)
            self.stats["live_transcript_chunks"] += 1
    
    def log_live_mode_state(self, platform_id: str, active: bool):
        """Log live mode state change."""
        with self._lock:
            event = InteractionEvent(
                event_id=self._generate_event_id(),
                event_type="live_mode_change",
                platform_id=platform_id,
                live_mode=active,
            )
            self._record_event(event)
    
    def _record_event(self, event: InteractionEvent):
        """Record an event."""
        self.events.append(event)
        self.stats["total_events"] += 1
        self.stats["events_by_type"][event.event_type] += 1
        self.stats["events_by_platform"][event.platform_id] += 1
        
        # Auto-flush to disk periodically
        if len(self.events) >= 100:
            self._flush_to_disk()
    
    def _flush_to_disk(self):
        """Flush events to disk."""
        if not self.events:
            return
        
        log_file = os.path.join(LOGS_DIR, f"interactions_{int(self.session_start)}.jsonl")
        try:
            with open(log_file, 'a') as f:
                for event in self.events:
                    f.write(json.dumps(event.to_dict()) + "\n")
            self.events.clear()
        except Exception as e:
            print(f"[InteractionLogger] Error flushing: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        with self._lock:
            return {
                "total_events": self.stats["total_events"],
                "events_by_type": dict(self.stats["events_by_type"]),
                "events_by_platform": dict(self.stats["events_by_platform"]),
                "live_transcript_chunks": self.stats["live_transcript_chunks"],
                "storage_credits": self.storage_credits,
                "patterns_exported": self.patterns_exported,
                "trading_enabled": self.trading_settings.trading_enabled,
            }
    
    # =========================================================================
    # DATA TRADING FUNCTIONS
    # =========================================================================
    
    def enable_trading(self, enabled: bool = True):
        """Enable or disable data trading (Premium)."""
        with self._lock:
            if enabled and not ENTITLEMENTS.is_premium():
                self.trading_settings.trading_enabled = False
            else:
                self.trading_settings.trading_enabled = enabled
            self._save_settings()
    
    def export_patterns_for_trading(self, count: int = 100) -> Dict[str, Any]:
        """
        Export anonymized patterns for data trading.
        Returns patterns and credits earned.
        """
        if not ENTITLEMENTS.is_premium():
            return {"error": "Premium required", "patterns": [], "credits": 0}

        if not self.trading_settings.trading_enabled:
            return {"error": "Trading not enabled", "patterns": [], "credits": 0}
        
        with self._lock:
            # Load recent events from disk
            all_events = self._load_recent_events(count * 2)
            
            # Anonymize events
            patterns = []
            for event in all_events[:count]:
                if event.raw_text:  # Only events with content
                    patterns.append(event.to_anonymized())
            
            if len(patterns) >= 100:
                # Award credits: 100 patterns = 500 credits
                credits_earned = (len(patterns) // 100) * 500
                self.storage_credits += credits_earned
                self.patterns_exported += len(patterns)
                self._save_settings()
                
                return {
                    "success": True,
                    "patterns_exported": len(patterns),
                    "credits_earned": credits_earned,
                    "total_credits": self.storage_credits,
                    "patterns": patterns if self.trading_settings.export_raw_logs else [],
                }
            
            return {
                "success": False,
                "error": f"Need at least 100 patterns, have {len(patterns)}",
                "patterns_available": len(patterns),
            }
    
    def _load_recent_events(self, count: int) -> List[InteractionEvent]:
        """Load recent events from disk."""
        events = list(self.events)  # Start with in-memory events
        
        # Load from disk files
        log_files = sorted(Path(LOGS_DIR).glob("interactions_*.jsonl"), reverse=True)
        for log_file in log_files[:5]:  # Check last 5 log files
            if len(events) >= count:
                break
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if len(events) >= count:
                            break
                        data = json.loads(line)
                        events.append(InteractionEvent(**data))
            except Exception as e:
                print(f"[InteractionLogger] Error loading {log_file}: {e}")
        
        return events
    
    # =========================================================================
    # EXPORT FUNCTIONS
    # =========================================================================
    
    def export_to_json(self, filepath: str, anonymize: bool = True):
        """Export all logs to JSON."""
        with self._lock:
            self._flush_to_disk()
            all_events = self._load_recent_events(10000)
            
            if anonymize:
                data = [e.to_anonymized() for e in all_events]
            else:
                data = [e.to_dict() for e in all_events]
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
    
    def export_to_csv(self, filepath: str, anonymize: bool = True):
        """Export all logs to CSV."""
        with self._lock:
            self._flush_to_disk()
            all_events = self._load_recent_events(10000)
            
            if not all_events:
                return
            
            if anonymize:
                data = [e.to_anonymized() for e in all_events]
            else:
                data = [e.to_dict() for e in all_events]
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        with self._lock:
            duration = time.time() - self.session_start
            return {
                "session_duration_minutes": int(duration / 60),
                "total_interactions": self.stats["total_events"],
                "platforms_used": list(self.stats["events_by_platform"].keys()),
                "user_inputs": self.stats["events_by_type"].get("user_input", 0),
                "ai_responses": self.stats["events_by_type"].get("ai_output", 0),
                "live_transcripts": self.stats["live_transcript_chunks"],
            }
    
    def shutdown(self):
        """Clean shutdown - flush remaining events."""
        with self._lock:
            self._flush_to_disk()
            self._save_settings()


# Global logger instance
LOGGER = InteractionLogger()
