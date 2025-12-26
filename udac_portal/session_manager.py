"""
Session Manager - Traffic Controller
=====================================
Routes events between WebView, ContinuityEngine, and Logger.
"""

import time
import threading
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field

from udac_portal.platform_registry import REGISTRY, AiWebPlatform
# Lazy imports to avoid circular dependencies
from udac_portal.continuity_engine import ContinuityPayload


@dataclass
class ActiveSession:
    """Represents an active session with a platform."""
    platform_id: str
    thread_id: str
    started_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_live_mode: bool = False
    messages_sent: int = 0
    messages_received: int = 0


class SessionManager:
    """
    Central traffic controller for UDAC.
    Manages platform sessions and routes events.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.active_sessions: Dict[str, ActiveSession] = {}
        self.current_platform_id: Optional[str] = None

        # Callbacks for UI updates
        self._on_ai_message_callbacks: list = []
        self._on_continuity_update_callbacks: list = []

        # Lazy-loaded instances (avoid circular imports)
        self._engine = None
        self._logger = None

        print("[SessionManager] Initialized")

    def _get_engine(self):
        """Lazy load ENGINE to avoid circular import."""
        if self._engine is None:
            from udac_portal.continuity_engine import ENGINE
            self._engine = ENGINE
        return self._engine

    def _get_logger(self):
        """Lazy load LOGGER to avoid circular import."""
        if self._logger is None:
            from udac_portal.interaction_logger import LOGGER
            self._logger = LOGGER
        return self._logger
    
    def start_session(self, platform_id: str) -> ActiveSession:
        """Start or resume a session with a platform."""
        with self._lock:
            if platform_id in self.active_sessions:
                session = self.active_sessions[platform_id]
                session.last_activity = time.time()
            else:
                thread_id = f"{platform_id}_{int(time.time())}"
                session = ActiveSession(
                    platform_id=platform_id,
                    thread_id=thread_id
                )
                self.active_sessions[platform_id] = session
            
            self.current_platform_id = platform_id
            return session
    
    def get_current_session(self) -> Optional[ActiveSession]:
        """Get the current active session."""
        if self.current_platform_id:
            return self.active_sessions.get(self.current_platform_id)
        return None
    
    def on_user_submit_from_udac(self, platform_id: str, raw_user_text: str) -> ContinuityPayload:
        """
        User submitted text via UDAC's input bar.
        This is the main entry point for user messages.
        
        Returns: ContinuityPayload with enriched text to inject.
        """
        with self._lock:
            # Ensure session exists
            session = self.start_session(platform_id)
            
            # Get enriched input from continuity engine
            payload = self._get_engine().enrich_input(platform_id, raw_user_text)

            # Log the interaction
            self._get_logger().log_user_input(
                platform_id=platform_id,
                raw=raw_user_text,
                enriched=payload.final_prompt_text,
                continuity_summary=payload.continuity_summary,
                tokens_added=payload.tokens_added,
                thread_id=session.thread_id
            )
            
            # Update session stats
            session.messages_sent += 1
            session.last_activity = time.time()
            
            # Notify UI
            self._notify_continuity_update(platform_id, payload)
            
            return payload
    
    def on_platform_user_message(self, platform_id: str, text: str):
        """
        Platform detected a user message in the DOM.
        This is "ground truth" of what actually got sent.
        """
        with self._lock:
            self._get_logger().log_platform_user_echo(platform_id, text)
    
    def on_platform_ai_message(self, platform_id: str, text: str):
        """
        Platform detected an AI response in the DOM.
        """
        with self._lock:
            session = self.active_sessions.get(platform_id)
            thread_id = session.thread_id if session else None
            
            # Log it
            self._get_logger().log_ai_output(platform_id, text, thread_id)

            # Feed to continuity engine
            self._get_engine().record_output(platform_id, text)
            
            # Update session stats
            if session:
                session.messages_received += 1
                session.last_activity = time.time()
            
            # Notify UI
            self._notify_ai_message(platform_id, text)
    
    def on_live_transcript_chunk(self, platform_id: str, text: str):
        """
        Live transcript chunk detected (voice mode).
        """
        with self._lock:
            # Log it
            self._get_logger().log_live_transcript_chunk(platform_id, text)

            # Feed to continuity engine (transcripts count as both input and context)
            self._get_engine().record_output(platform_id, text)
    
    def on_live_mode_changed(self, platform_id: str, active: bool):
        """
        Platform's live/voice mode state changed.
        """
        with self._lock:
            session = self.active_sessions.get(platform_id)
            if session:
                session.is_live_mode = active

            self._get_logger().log_live_mode_state(platform_id, active)
    
    # =========================================================================
    # CALLBACK REGISTRATION
    # =========================================================================
    
    def register_ai_message_callback(self, callback: Callable[[str, str], None]):
        """Register callback for AI messages: callback(platform_id, text)"""
        self._on_ai_message_callbacks.append(callback)
    
    def register_continuity_update_callback(self, callback: Callable[[str, ContinuityPayload], None]):
        """Register callback for continuity updates: callback(platform_id, payload)"""
        self._on_continuity_update_callbacks.append(callback)
    
    def _notify_ai_message(self, platform_id: str, text: str):
        """Notify all registered callbacks of AI message."""
        for callback in self._on_ai_message_callbacks:
            try:
                callback(platform_id, text)
            except Exception as e:
                print(f"[SessionManager] Callback error: {e}")
    
    def _notify_continuity_update(self, platform_id: str, payload: ContinuityPayload):
        """Notify all registered callbacks of continuity update."""
        for callback in self._on_continuity_update_callbacks:
            try:
                callback(platform_id, payload)
            except Exception as e:
                print(f"[SessionManager] Callback error: {e}")
    
    # =========================================================================
    # STATS & INFO
    # =========================================================================
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for all sessions."""
        with self._lock:
            stats = {
                "active_sessions": len(self.active_sessions),
                "current_platform": self.current_platform_id,
                "sessions": {}
            }
            
            for pid, session in self.active_sessions.items():
                platform = REGISTRY.get_platform(pid)
                stats["sessions"][pid] = {
                    "platform_name": platform.name if platform else pid,
                    "messages_sent": session.messages_sent,
                    "messages_received": session.messages_received,
                    "is_live_mode": session.is_live_mode,
                    "duration_minutes": int((time.time() - session.started_at) / 60),
                }
            
            return stats
    
    def get_continuity_info(self, platform_id: str) -> Dict[str, Any]:
        """Get continuity info for a platform."""
        session = self.active_sessions.get(platform_id)
        engine_stats = self._get_engine().get_stats()
        
        return {
            "enabled": engine_stats["enabled"],
            "injection_strength": engine_stats["injection_strength"],
            "platform_isolation": engine_stats["platform_isolation"],
            "session_messages": session.messages_sent + session.messages_received if session else 0,
            "cross_platform_memories": engine_stats["cross_platform_memories"],
        }
    
    def shutdown(self):
        """Clean shutdown."""
        with self._lock:
            self._get_logger().shutdown()
            self.active_sessions.clear()


# Global session manager instance
SESSION = SessionManager()
