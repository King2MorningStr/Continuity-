"""
Continuity Engine - The DMC Brain
=================================
Compresses history, generates continuity payloads, respects threshold scaling & toggles.
"""

import time
import json
import os
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
import hashlib

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
from udac_portal.ivm_resilience import ivm_resilient, IVMMemoryManager, RESILIENCE
try:
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # Silent fail - will try again when actually needed


@dataclass
class ContinuitySettings:
    """User continuity preferences."""
    injection_strength: int = 5  # 0-10 scale
    continuity_enabled: bool = True
    platform_isolation_mode: bool = False  # Premium: per-platform memory
    cross_platform_insights: bool = True  # Premium: cross-AI learning
    max_context_tokens: int = 2000
    summary_compression_level: int = 2  # 1=light, 2=medium, 3=aggressive


@dataclass 
class ContinuityPayload:
    """Result of continuity enrichment."""
    final_prompt_text: str
    continuity_summary: str
    tokens_added: int
    context_sources: List[str]  # Which platforms contributed context


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    platform_id: str = ""
    thread_id: str = ""


@dataclass
class ConversationThread:
    """A conversation thread with an AI platform."""
    thread_id: str
    platform_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    summary: str = ""
    topics: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    
    def add_turn(self, role: str, content: str):
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=time.time(),
            platform_id=self.platform_id,
            thread_id=self.thread_id
        )
        self.turns.append(turn)
        self.last_active = time.time()


class ContinuityEngine:
    """
    The brain of UDAC - manages continuity across all AI platforms.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self.settings = ContinuitySettings()
        
        # Global continuity container
        self.global_threads: Dict[str, ConversationThread] = {}
        
        # Per-platform containers (for isolation mode)
        self.platform_threads: Dict[str, Dict[str, ConversationThread]] = defaultdict(dict)
        
        # Active thread tracking
        self.active_thread_ids: Dict[str, str] = {}  # platform_id -> thread_id
        
        # Global context synthesis
        self.user_profile: Dict[str, Any] = {
            "topics_of_interest": [],
            "communication_style": "neutral",
            "expertise_areas": [],
            "preferences": {}
        }
        
        # Cross-platform insights
        self.cross_platform_memory: List[Dict] = []
        
        self._load_state()
        print("[ContinuityEngine] Initialized")
    
    def _get_storage_key(self, platform_id: str) -> str:
        """Get the storage key based on isolation mode."""
        if self.settings.platform_isolation_mode:
            return platform_id
        return "global"
    
    def _load_state(self):
        """Load persisted state."""
        state_file = os.path.join(STORAGE_DIR, "continuity_state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                # Restore settings
                if "settings" in data:
                    for k, v in data["settings"].items():
                        if hasattr(self.settings, k):
                            setattr(self.settings, k, v)
                # Restore user profile
                if "user_profile" in data:
                    self.user_profile.update(data["user_profile"])
                # Restore cross-platform memory
                if "cross_platform_memory" in data:
                    self.cross_platform_memory = data["cross_platform_memory"][-100:]  # Keep last 100
            except Exception as e:
                print(f"[ContinuityEngine] Error loading state: {e}")
    
    def _save_state(self):
        """Persist state."""
        try:
            # Ensure directory exists before writing
            Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)

            state_file = os.path.join(STORAGE_DIR, "continuity_state.json")
            data = {
                "settings": {
                    "injection_strength": self.settings.injection_strength,
                    "continuity_enabled": self.settings.continuity_enabled,
                    "platform_isolation_mode": self.settings.platform_isolation_mode,
                    "cross_platform_insights": self.settings.cross_platform_insights,
                    "max_context_tokens": self.settings.max_context_tokens,
                },
                "user_profile": self.user_profile,
                "cross_platform_memory": self.cross_platform_memory[-100:],
            }
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ContinuityEngine] Error saving state: {e}")
    
    def get_or_create_thread(self, platform_id: str, thread_id: Optional[str] = None) -> ConversationThread:
        """Get existing thread or create new one."""
        with self._lock:
            if thread_id is None:
                thread_id = f"{platform_id}_{int(time.time())}"
            
            key = self._get_storage_key(platform_id)
            
            if key == "global":
                if thread_id not in self.global_threads:
                    self.global_threads[thread_id] = ConversationThread(
                        thread_id=thread_id,
                        platform_id=platform_id
                    )
                self.active_thread_ids[platform_id] = thread_id
                return self.global_threads[thread_id]
            else:
                if thread_id not in self.platform_threads[platform_id]:
                    self.platform_threads[platform_id][thread_id] = ConversationThread(
                        thread_id=thread_id,
                        platform_id=platform_id
                    )
                self.active_thread_ids[platform_id] = thread_id
                return self.platform_threads[platform_id][thread_id]
    
    @ivm_resilient(
        component="continuity_enrichment",
        fallback=None,
        silent=False,
        use_circuit_breaker=True
    )
    def enrich_input(self, platform_id: str, raw_user_text: str) -> ContinuityPayload:
        """
        Main entry point: Enrich user input with continuity context.
        IVM-protected for maximum resilience.
        """
        # Fallback if anything goes wrong
        default_payload = ContinuityPayload(
            final_prompt_text=raw_user_text,
            continuity_summary="",
            tokens_added=0,
            context_sources=[]
        )

        if not self.settings.continuity_enabled or self.settings.injection_strength == 0:
            return default_payload

        try:
            return self._enrich_input_internal(platform_id, raw_user_text)
        except Exception as e:
            print(f"[ContinuityEngine] Enrichment failed, using raw text: {e}")
            return default_payload

    def _enrich_input_internal(self, platform_id: str, raw_user_text: str) -> ContinuityPayload:
        """Internal enrichment logic (separated for error handling)."""

        with self._lock:
            is_premium = ENTITLEMENTS.is_premium()
            # Free tier safety clamps
            if not is_premium:
                self.settings.platform_isolation_mode = False
                self.settings.cross_platform_insights = False
                self.settings.injection_strength = min(self.settings.injection_strength, 5)
                self.settings.max_context_tokens = min(self.settings.max_context_tokens, 1200)

            # Get active thread for this platform (with IVM memory management)
            thread_id = self.active_thread_ids.get(platform_id)
            thread = self.get_or_create_thread(platform_id, thread_id)

            # IVM Memory Management: Prevent unbounded thread growth
            if len(thread.turns) > 500:
                # Keep most recent 250 turns
                thread.turns = thread.turns[-250:]
                print(f"[IVM] Pruned thread {thread_id} to maintain equilibrium")

            # Record the user input
            thread.add_turn("user", raw_user_text)
            
            # Build continuity context
            context_parts = []
            sources = []
            
            # 1. Recent conversation summary from current thread
            if len(thread.turns) > 2:
                recent_summary = self._summarize_recent_turns(thread.turns[-6:])
                if recent_summary:
                    context_parts.append(f"[Recent context: {recent_summary}]")
                    sources.append(platform_id)
            
            # 2. Cross-platform insights (if enabled)
            if self.settings.cross_platform_insights and not self.settings.platform_isolation_mode:
                cross_context = self._get_cross_platform_context(platform_id, raw_user_text)
                if cross_context:
                    context_parts.append(f"[Cross-platform insight: {cross_context}]")
                    sources.extend([m["platform"] for m in self.cross_platform_memory[-5:] 
                                  if m["platform"] != platform_id])
            
            # 3. User profile context (at higher injection levels)
            if self.settings.injection_strength >= 7:
                profile_context = self._get_profile_context()
                if profile_context:
                    context_parts.append(f"[User context: {profile_context}]")
            
            # Build final prompt
            if context_parts:
                # Scale context by injection strength
                max_context_chars = int(self.settings.max_context_tokens * 4 * 
                                       (self.settings.injection_strength / 10))
                
                continuity_block = " ".join(context_parts)
                if len(continuity_block) > max_context_chars:
                    continuity_block = continuity_block[:max_context_chars] + "..."
                
                final_text = f"{continuity_block}\n\n{raw_user_text}"
                tokens_added = len(continuity_block) // 4  # Rough estimate
            else:
                final_text = raw_user_text
                continuity_block = ""
                tokens_added = 0
            
            self._save_state()
            
            return ContinuityPayload(
                final_prompt_text=final_text,
                continuity_summary=continuity_block,
                tokens_added=tokens_added,
                context_sources=list(set(sources))
            )
    
    @ivm_resilient(component="record_output", silent=True, use_circuit_breaker=False)
    def record_output(self, platform_id: str, output_text: str):
        """
        Record AI output for continuity building.
        IVM-protected to prevent crashes from bad data.
        """
        with self._lock:
            thread_id = self.active_thread_ids.get(platform_id)
            if thread_id:
                thread = self.get_or_create_thread(platform_id, thread_id)
                thread.add_turn("assistant", output_text)

                # IVM Memory Management: Prevent unbounded memory growth
                IVMMemoryManager.bounded_dict(self.global_threads, max_size=100,
                    key_accessor=lambda t: t.last_active)

                # Update cross-platform memory
                if self.settings.cross_platform_insights:
                    self._update_cross_platform_memory(platform_id, output_text)
                
                # Extract topics for user profile
                self._extract_topics(output_text)
                
                self._save_state()
    
    def _summarize_recent_turns(self, turns: List[ConversationTurn]) -> str:
        """Create a compressed summary of recent turns."""
        if not turns:
            return ""
        
        # Simple compression: take key phrases from each turn
        summaries = []
        for turn in turns:
            content = turn.content[:200]  # Truncate long content
            if turn.role == "user":
                summaries.append(f"User asked about: {self._extract_topic(content)}")
            else:
                summaries.append(f"AI discussed: {self._extract_topic(content)}")
        
        # Join with compression based on level
        if self.settings.summary_compression_level == 1:
            return " | ".join(summaries[-4:])
        elif self.settings.summary_compression_level == 2:
            return " | ".join(summaries[-2:])
        else:
            return summaries[-1] if summaries else ""
    
    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text (simple heuristic)."""
        # Take first sentence or first 50 chars
        text = text.strip()
        if "." in text[:100]:
            return text[:text.index(".")+1]
        return text[:50] + "..." if len(text) > 50 else text
    
    def _get_cross_platform_context(self, current_platform: str, user_text: str) -> str:
        """Get relevant context from other platforms."""
        if not self.cross_platform_memory:
            return ""
        
        # Find recent relevant memories from other platforms
        relevant = []
        user_words = set(user_text.lower().split())
        
        for memory in self.cross_platform_memory[-20:]:
            if memory["platform"] == current_platform:
                continue
            memory_words = set(memory.get("topic", "").lower().split())
            overlap = len(user_words & memory_words)
            if overlap > 0:
                relevant.append((overlap, memory))
        
        if not relevant:
            return ""
        
        # Sort by relevance and take top
        relevant.sort(key=lambda x: x[0], reverse=True)
        top = relevant[0][1]
        return f"From {top['platform']}: {top['topic']}"
    
    def _update_cross_platform_memory(self, platform_id: str, output_text: str):
        """Update cross-platform memory with insights."""
        topic = self._extract_topic(output_text)
        self.cross_platform_memory.append({
            "platform": platform_id,
            "topic": topic,
            "timestamp": time.time()
        })
        # Keep only recent memories
        self.cross_platform_memory = self.cross_platform_memory[-100:]
    
    def _get_profile_context(self) -> str:
        """Get user profile context."""
        parts = []
        if self.user_profile["topics_of_interest"]:
            parts.append(f"Interests: {', '.join(self.user_profile['topics_of_interest'][:3])}")
        if self.user_profile["expertise_areas"]:
            parts.append(f"Expertise: {', '.join(self.user_profile['expertise_areas'][:2])}")
        return " | ".join(parts) if parts else ""
    
    def _extract_topics(self, text: str):
        """Extract topics for user profile building."""
        # Simple keyword extraction (could be enhanced with NLP)
        words = text.lower().split()
        # Filter common words and keep potential topics
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", 
                    "being", "have", "has", "had", "do", "does", "did", "will",
                    "would", "could", "should", "may", "might", "must", "shall",
                    "can", "need", "dare", "ought", "used", "to", "of", "in",
                    "for", "on", "with", "at", "by", "from", "as", "into", "through",
                    "during", "before", "after", "above", "below", "between", "under",
                    "again", "further", "then", "once", "here", "there", "when", "where",
                    "why", "how", "all", "each", "every", "both", "few", "more", "most",
                    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
                    "so", "than", "too", "very", "just", "and", "but", "if", "or",
                    "because", "until", "while", "although", "this", "that", "these",
                    "those", "i", "you", "he", "she", "it", "we", "they", "what", "which"}
        
        potential_topics = [w for w in words if len(w) > 4 and w not in stopwords]
        
        # Add to interests (deduplicated)
        for topic in potential_topics[:3]:
            if topic not in self.user_profile["topics_of_interest"]:
                self.user_profile["topics_of_interest"].append(topic)
        
        # Keep only recent interests
        self.user_profile["topics_of_interest"] = self.user_profile["topics_of_interest"][-20:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get continuity statistics."""
        with self._lock:
            total_turns = sum(len(t.turns) for t in self.global_threads.values())
            for platform_threads in self.platform_threads.values():
                total_turns += sum(len(t.turns) for t in platform_threads.values())
            
            return {
                "enabled": self.settings.continuity_enabled,
                "injection_strength": self.settings.injection_strength,
                "platform_isolation": self.settings.platform_isolation_mode,
                "total_threads": len(self.global_threads) + sum(len(p) for p in self.platform_threads.values()),
                "total_turns": total_turns,
                "cross_platform_memories": len(self.cross_platform_memory),
                "topics_tracked": len(self.user_profile["topics_of_interest"]),
            }
    
    def update_settings(self, **kwargs):
        """Update continuity settings (entitlement-aware)."""
        with self._lock:
            is_premium = ENTITLEMENTS.is_premium()

            # Enforce premium gates
            if "cross_platform_insights" in kwargs and kwargs["cross_platform_insights"] and not is_premium:
                kwargs["cross_platform_insights"] = False

            if "platform_isolation_mode" in kwargs and kwargs["platform_isolation_mode"] and not is_premium:
                kwargs["platform_isolation_mode"] = False

            # Enforce injection strength caps on free tier
            if "injection_strength" in kwargs and not is_premium:
                kwargs["injection_strength"] = min(int(kwargs["injection_strength"]), 5)

            # Enforce context budget caps on free tier
            if "max_context_tokens" in kwargs and not is_premium:
                kwargs["max_context_tokens"] = min(int(kwargs["max_context_tokens"]), 1200)

            for key, value in kwargs.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)

            self._save_state()

    def clear_all_data(self):
        """Clear all continuity data (user requested)."""
        with self._lock:
            self.global_threads.clear()
            self.platform_threads.clear()
            self.active_thread_ids.clear()
            self.cross_platform_memory.clear()
            self.user_profile = {
                "topics_of_interest": [],
                "communication_style": "neutral",
                "expertise_areas": [],
                "preferences": {}
            }
            self._save_state()


# Global engine instance
ENGINE = ContinuityEngine()
