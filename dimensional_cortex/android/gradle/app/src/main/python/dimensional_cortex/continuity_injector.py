"""
Continuity Injector - AGGRESSIVE DEBUG VERSION
===============================================
Changes:
1. VERY LOW threshold (0.05) - inject almost everything
2. Decision log tracks WHY injection did/didn't happen
3. Better keyword matching (extracts from stored content too)
4. Force mode available for testing
5. Full context dump in debug mode
"""

import time
import hashlib
import threading
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ContinuityInjector")


class Platform(Enum):
    CHATGPT = "ChatGPT"
    CLAUDE = "Claude"
    PERPLEXITY = "Perplexity"
    GEMINI = "Gemini"
    UNKNOWN = "Unknown"


@dataclass
class InjectionDecision:
    """Tracks WHY an injection decision was made."""
    timestamp: float
    message: str
    platform: str
    decision: str  # "INJECTED", "SKIPPED", "ERROR"
    reason: str
    relevance_score: float
    topics_found: int
    facts_found: int
    crystals_found: int
    context_preview: str
    threshold_used: float
    trinity_running: bool
    memory_nodes_checked: int
    matching_nodes: int


@dataclass
class ContinuityContext:
    """Extracted context for injection."""
    relevant_topics: List[str] = field(default_factory=list)
    key_facts: Dict[str, str] = field(default_factory=dict)
    recent_themes: List[str] = field(default_factory=list)
    conversation_count: int = 0
    cross_platform_topics: List[str] = field(default_factory=list)
    active_crystals: List[str] = field(default_factory=list)
    quasi_concepts: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    confidence: float = 0.0
    # Debug info
    nodes_checked: int = 0
    nodes_matched: int = 0
    keywords_used: List[str] = field(default_factory=list)


@dataclass
class InjectionResult:
    """Result of injection."""
    original_message: str
    injected_message: str
    context_block: str
    was_injected: bool
    relevance_score: float
    context_summary: str
    timestamp: float = field(default_factory=time.time)


class ContinuityInjector:
    """
    AGGRESSIVE VERSION - Injects everything possible.
    """

    CONTEXT_TEMPLATES = {
        Platform.CHATGPT: (
            "\n\n---\n"
            "[System: User has prior conversation context -\n"
            "{context}]"
        ),
        Platform.CLAUDE: (
            "\n\n<prior_context>\n"
            "{context}\n"
            "</prior_context>"
        ),
        Platform.PERPLEXITY: (
            "\n\n[Prior context: {context}]"
        ),
        Platform.GEMINI: (
            "\n\n[User's conversation history: {context}]"
        ),
        Platform.UNKNOWN: (
            "\n\n[Context: {context}]"
        ),
    }

    # === AGGRESSIVE: Very low threshold ===
    DEFAULT_THRESHOLD = 0.05
    MAX_CONTEXT_LENGTH = 600  # More context

    def __init__(self, trinity_manager=None):
        self.trinity = trinity_manager
        self._lock = threading.Lock()

        # Settings
        self.enabled = True
        self.debug_mode = True  # Always on for now
        self.min_relevance = self.DEFAULT_THRESHOLD
        self.max_context_length = self.MAX_CONTEXT_LENGTH
        self.force_injection = False  # When True, ALWAYS inject something

        # Stats
        self.total_requests = 0
        self.total_injections = 0
        self.injections_by_platform: Dict[str, int] = {}

        # History
        self.injection_history: List[InjectionResult] = []
        self.max_history = 50

        # === NEW: Decision log for debugging ===
        self.decision_log: deque = deque(maxlen=100)

        # Cache
        self._context_cache: Dict[str, Tuple[ContinuityContext, float]] = {}
        self._cache_ttl = 15.0  # Shorter cache for testing

        logger.info("=" * 60)
        logger.info("AGGRESSIVE ContinuityInjector initialized")
        logger.info("  Threshold: %.2f (very low)", self.min_relevance)
        logger.info("  Debug mode: %s", self.debug_mode)
        logger.info("  Force injection: %s", self.force_injection)
        logger.info("=" * 60)

    def set_trinity(self, trinity_manager):
        """Set Trinity manager reference."""
        self.trinity = trinity_manager
        logger.info("Trinity manager connected")

    def inject(self, message: str, platform: Platform, force: bool = False) -> InjectionResult:
        """
        AGGRESSIVE injection - tries to inject whenever possible.
        """
        logger.info("=" * 50)
        logger.info("INJECT REQUEST")
        logger.info("  Message: '%s'", message[:80] if message else "EMPTY")
        logger.info("  Platform: %s", platform.value)
        logger.info("  Force: %s", force or self.force_injection)
        logger.info("=" * 50)

        with self._lock:
            self.total_requests += 1

        # Track decision
        decision = InjectionDecision(
            timestamp=time.time(),
            message=message[:100] if message else "",
            platform=platform.value,
            decision="PENDING",
            reason="",
            relevance_score=0.0,
            topics_found=0,
            facts_found=0,
            crystals_found=0,
            context_preview="",
            threshold_used=self.min_relevance,
            trinity_running=self.trinity is not None and self.trinity.running if self.trinity else False,
            memory_nodes_checked=0,
            matching_nodes=0
        )

        # Default result
        result = InjectionResult(
            original_message=message,
            injected_message=message,
            context_block="",
            was_injected=False,
            relevance_score=0.0,
            context_summary=""
        )

        try:
            # Check if disabled
            if not self.enabled and not force and not self.force_injection:
                decision.decision = "SKIPPED"
                decision.reason = "Injection disabled"
                self._log_decision(decision)
                return result

            # Check empty message
            if not message or len(message.strip()) < 2:
                decision.decision = "SKIPPED"
                decision.reason = "Message too short"
                self._log_decision(decision)
                return result

            # Check Trinity
            if not self.trinity:
                decision.decision = "SKIPPED"
                decision.reason = "Trinity manager not set"
                self._log_decision(decision)
                logger.warning("No Trinity manager!")
                return result

            if not self.trinity.running:
                decision.decision = "SKIPPED"
                decision.reason = "Trinity not running"
                self._log_decision(decision)
                logger.warning("Trinity not running!")
                return result

            decision.trinity_running = True

            # Extract context
            logger.info("Extracting context...")
            context = self._extract_context(message, platform)

            # Update decision with extraction results
            decision.relevance_score = context.relevance_score
            decision.topics_found = len(context.relevant_topics)
            decision.facts_found = len(context.key_facts)
            decision.crystals_found = len(context.active_crystals)
            decision.memory_nodes_checked = context.nodes_checked
            decision.matching_nodes = context.nodes_matched

            logger.info("Extraction results:")
            logger.info("  Nodes checked: %d", context.nodes_checked)
            logger.info("  Nodes matched: %d", context.nodes_matched)
            logger.info("  Topics: %d - %s", len(context.relevant_topics), context.relevant_topics[:5])
            logger.info("  Facts: %d - %s", len(context.key_facts), list(context.key_facts.keys())[:5])
            logger.info("  Crystals: %d", len(context.active_crystals))
            logger.info("  Relevance: %.3f", context.relevance_score)

            result.relevance_score = context.relevance_score

            # === AGGRESSIVE: Check threshold OR force ===
            should_inject = (
                context.relevance_score >= self.min_relevance or
                force or
                self.force_injection or
                context.nodes_matched > 0  # Inject if ANY match found
            )

            if not should_inject:
                decision.decision = "SKIPPED"
                decision.reason = f"Relevance {context.relevance_score:.3f} < {self.min_relevance:.3f}, no matches"
                self._log_decision(decision)
                logger.info("No injection - %s", decision.reason)
                return result

            # Format context
            logger.info("Formatting context for injection...")
            context_text = self._format_context(context)

            if not context_text and not force and not self.force_injection:
                decision.decision = "SKIPPED"
                decision.reason = "No context text generated"
                self._log_decision(decision)
                return result

            # Use fallback if forced but no context
            if not context_text:
                context_text = f"User has {self.trinity.conversations_processed} prior conversations on this device"

            logger.info("Context text: %s", context_text[:200])
            decision.context_preview = context_text[:150]

            # Build context block
            template = self.CONTEXT_TEMPLATES.get(platform, self.CONTEXT_TEMPLATES[Platform.UNKNOWN])
            context_block = template.format(context=context_text)

            # APPEND to message
            injected_message = message + context_block

            # Create summary
            context_summary = self._create_summary(context)

            # Final result
            result = InjectionResult(
                original_message=message,
                injected_message=injected_message,
                context_block=context_block,
                was_injected=True,
                relevance_score=context.relevance_score,
                context_summary=context_summary
            )

            # Update stats
            with self._lock:
                self.total_injections += 1
                self.injections_by_platform[platform.value] = \
                    self.injections_by_platform.get(platform.value, 0) + 1

            self._add_to_history(result)

            decision.decision = "INJECTED"
            decision.reason = f"Relevance {context.relevance_score:.3f}, {context.nodes_matched} matches"
            self._log_decision(decision)

            logger.info("=" * 50)
            logger.info("INJECTION COMPLETE")
            logger.info("  Context length: %d chars", len(context_block))
            logger.info("  Total message length: %d chars", len(injected_message))
            logger.info("=" * 50)

            return result

        except Exception as e:
            logger.error("Injection error: %s", e, exc_info=True)
            decision.decision = "ERROR"
            decision.reason = str(e)
            self._log_decision(decision)
            return result

    def _extract_context(self, message: str, platform: Platform) -> ContinuityContext:
        """Extract context - AGGRESSIVE matching."""
        context = ContinuityContext()

        if not self.trinity or not self.trinity.running:
            return context

        # Skip cache for debugging
        # cache_key = hashlib.md5(message.encode()).hexdigest()[:16]

        try:
            # Get keywords from message
            keywords = self._extract_keywords(message)
            context.keywords_used = keywords
            logger.debug("Keywords from message: %s", keywords)

            # === MEMORY EXTRACTION ===
            if self.trinity.memory_system:
                context = self._extract_from_memory(context, message, keywords)

            # === CRYSTAL EXTRACTION ===
            if self.trinity.crystal_system:
                context = self._extract_from_crystals(context, message, platform)

            # Calculate relevance
            context.relevance_score = self._calculate_relevance(context, message)
            context.confidence = min(1.0,
                len(context.key_facts) * 0.2 +
                len(context.relevant_topics) * 0.15)

        except Exception as e:
            logger.error("Context extraction error: %s", e, exc_info=True)

        return context

    def _extract_from_memory(self, context: ContinuityContext, message: str, keywords: List[str]) -> ContinuityContext:
        """AGGRESSIVE memory extraction - match broadly."""
        try:
            memory = self.trinity.memory_system
            if not memory or not hasattr(memory, 'nodes'):
                logger.warning("Memory system has no nodes")
                return context

            nodes = memory.nodes
            context.nodes_checked = len(nodes)
            logger.debug("Checking %d memory nodes", len(nodes))

            if len(nodes) == 0:
                logger.warning("Memory is empty!")
                return context

            relevant_nodes = []

            for node_id, node in nodes.items():
                payload = node.payload

                # Convert entire payload to searchable text
                payload_text = ""
                for key, value in payload.items():
                    if isinstance(value, str):
                        payload_text += " " + value.lower()
                    elif isinstance(value, (int, float)):
                        payload_text += " " + str(value)

                # Also check dimension links
                for link in node.dimension_links:
                    payload_text += " " + link.lower()

                # === AGGRESSIVE MATCHING ===
                # Match if ANY keyword appears
                matches = 0
                for kw in keywords:
                    if kw.lower() in payload_text:
                        matches += 1

                # Also do partial matching (3+ char substrings)
                for kw in keywords:
                    if len(kw) >= 4:
                        for word in payload_text.split():
                            if kw[:4] in word or word[:4] in kw:
                                matches += 0.5

                if matches > 0:
                    relevant_nodes.append((node, matches, payload_text[:200]))
                    logger.debug("  Match: %s (score: %.1f)", node_id[:20], matches)

            context.nodes_matched = len(relevant_nodes)
            logger.info("Found %d matching nodes out of %d", len(relevant_nodes), len(nodes))

            # Sort by match score
            relevant_nodes.sort(key=lambda x: x[1], reverse=True)

            # Extract from top matches
            for node, score, preview in relevant_nodes[:10]:
                # Topics
                concept = node.payload.get("concept", "")
                if concept and concept not in context.relevant_topics:
                    context.relevant_topics.append(concept)

                # Facts - be more aggressive
                for key, value in node.payload.items():
                    if key in ["id", "timestamp", "last_modified_timestamp"]:
                        continue
                    if isinstance(value, str) and len(value) > 3:
                        # Store more facts
                        fact_key = f"{key}"
                        if len(context.key_facts) < 10:
                            context.key_facts[fact_key] = str(value)[:150]

                # Themes from dimension links
                for link in node.dimension_links:
                    if link.startswith("dim_theme:"):
                        theme = link.replace("dim_theme:", "")
                        if theme not in context.recent_themes:
                            context.recent_themes.append(theme)

            # If NO keyword matches but we have nodes, grab recent ones
            if context.nodes_matched == 0 and len(nodes) > 0:
                logger.info("No keyword matches - grabbing recent nodes")
                sorted_nodes = sorted(
                    nodes.values(),
                    key=lambda n: n.last_modified_timestamp,
                    reverse=True
                )
                for node in sorted_nodes[:5]:
                    concept = node.payload.get("concept", "")
                    if concept:
                        context.relevant_topics.append(concept)
                    for key, value in node.payload.items():
                        if key not in ["id", "timestamp", "last_modified_timestamp"]:
                            if isinstance(value, str) and len(value) > 3:
                                if len(context.key_facts) < 5:
                                    context.key_facts[key] = str(value)[:100]
                context.nodes_matched = min(5, len(sorted_nodes))

        except Exception as e:
            logger.error("Memory extraction error: %s", e, exc_info=True)

        return context

    def _extract_from_crystals(self, context: ContinuityContext, message: str, platform: Platform) -> ContinuityContext:
        """Extract from crystal system."""
        try:
            crystal_system = self.trinity.crystal_system
            if not crystal_system or not hasattr(crystal_system, 'crystals'):
                return context

            crystals = crystal_system.crystals
            logger.debug("Checking %d crystals", len(crystals))

            context.conversation_count = getattr(self.trinity, 'conversations_processed', 0)

            for crystal in crystals.values():
                # Track all active crystals
                if crystal.usage_count > 0:
                    if crystal.concept not in context.active_crystals:
                        context.active_crystals.append(crystal.concept)

                # Track QUASI
                try:
                    from dimensional_cortex.dimensional_processing_system_standalone_demo import CrystalLevel
                    if crystal.level == CrystalLevel.QUASI:
                        context.quasi_concepts.append(crystal.concept)
                except:
                    pass

                # Cross-platform
                if hasattr(crystal, 'connections'):
                    for connected_id, weight in crystal.connections.items():
                        if weight > 0.1:
                            connected = crystals.get(connected_id)
                            if connected:
                                if connected.concept not in context.cross_platform_topics:
                                    context.cross_platform_topics.append(connected.concept)

        except Exception as e:
            logger.error("Crystal extraction error: %s", e)

        return context

    def _calculate_relevance(self, context: ContinuityContext, message: str) -> float:
        """Calculate relevance - MORE GENEROUS scoring."""
        score = 0.0

        # Topics (max 0.35)
        score += min(0.35, len(context.relevant_topics) * 0.07)

        # Facts (max 0.30)
        score += min(0.30, len(context.key_facts) * 0.06)

        # Cross-platform (max 0.15)
        score += min(0.15, len(context.cross_platform_topics) * 0.08)

        # QUASI (max 0.10)
        score += min(0.10, len(context.quasi_concepts) * 0.05)

        # Conversation count (max 0.15)
        if context.conversation_count > 0:
            score += min(0.15, context.conversation_count * 0.03)

        # Node matches bonus (max 0.20)
        if context.nodes_matched > 0:
            score += min(0.20, context.nodes_matched * 0.04)

        # Themes bonus
        score += min(0.10, len(context.recent_themes) * 0.03)

        # Active crystals bonus
        score += min(0.10, len(context.active_crystals) * 0.02)

        return min(1.0, score)

    def _format_context(self, context: ContinuityContext) -> str:
        """Format ALL available context."""
        parts = []

        # Topics
        clean_topics = [t for t in context.relevant_topics if not t.startswith("PLATFORM_")]
        platform_topics = [t.replace("PLATFORM_", "") for t in context.relevant_topics if t.startswith("PLATFORM_")]

        if clean_topics:
            parts.append(f"Topics: {', '.join(clean_topics[:6])}")

        if platform_topics:
            parts.append(f"Platforms used: {', '.join(platform_topics[:3])}")

        # Facts - include more
        if context.key_facts:
            fact_items = []
            for k, v in list(context.key_facts.items())[:5]:
                if k not in ["concept", "id"]:
                    # Clean up the value
                    clean_v = str(v)[:80].replace("\n", " ")
                    fact_items.append(f"{k}: {clean_v}")
            if fact_items:
                parts.append("Known info: " + "; ".join(fact_items))

        # Themes
        if context.recent_themes:
            parts.append(f"Themes: {', '.join(context.recent_themes[:4])}")

        # Cross-platform
        clean_cross = [t for t in context.cross_platform_topics if not t.startswith("PLATFORM_")]
        if clean_cross:
            parts.append(f"Cross-platform topics: {', '.join(clean_cross[:3])}")

        # QUASI
        clean_quasi = [q for q in context.quasi_concepts if not q.startswith("PLATFORM_")]
        if clean_quasi:
            parts.append(f"Evolved concepts: {', '.join(clean_quasi[:3])}")

        # Conversation count
        if context.conversation_count > 0:
            parts.append(f"{context.conversation_count} prior conversations")

        # Active crystals count
        if context.active_crystals:
            parts.append(f"{len(context.active_crystals)} active concept crystals")

        result = " | ".join(parts)

        if len(result) > self.max_context_length:
            result = result[:self.max_context_length - 3] + "..."

        return result

    def _create_summary(self, context: ContinuityContext) -> str:
        """Create summary."""
        parts = []
        if context.relevant_topics:
            parts.append(f"{len(context.relevant_topics)} topics")
        if context.key_facts:
            parts.append(f"{len(context.key_facts)} facts")
        if context.nodes_matched:
            parts.append(f"{context.nodes_matched} matches")
        if context.conversation_count:
            parts.append(f"{context.conversation_count} convos")

        if parts:
            return f"Injected: {', '.join(parts)} (rel: {context.relevance_score:.0%})"
        return "Injected: minimal context"

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords."""
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
            'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'under', 'again', 'then', 'once', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
            'because', 'until', 'while', 'this', 'that', 'these', 'those', 'i',
            'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she',
            'her', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who',
            'can', 'want', 'need', 'like', 'know', 'think', 'about', 'get', 'got',
            'tell', 'said', 'say', 'going', 'really', 'also', 'well', 'back',
            'now', 'way', 'even', 'new', 'just', 'only', 'come', 'its', 'over',
            'such', 'take', 'into', 'year', 'your', 'good', 'some', 'could',
            'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only',
            'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use',
            'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new',
            'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
        }

        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stopwords]
        return list(dict.fromkeys(keywords))[:20]

    def _log_decision(self, decision: InjectionDecision):
        """Log decision for debugging."""
        self.decision_log.append(decision)

        logger.info("-" * 40)
        logger.info("DECISION: %s", decision.decision)
        logger.info("  Reason: %s", decision.reason)
        logger.info("  Relevance: %.3f (threshold: %.3f)", decision.relevance_score, decision.threshold_used)
        logger.info("  Topics: %d, Facts: %d, Crystals: %d",
                   decision.topics_found, decision.facts_found, decision.crystals_found)
        logger.info("  Nodes: %d checked, %d matched",
                   decision.memory_nodes_checked, decision.matching_nodes)
        logger.info("-" * 40)

    def _add_to_history(self, result: InjectionResult):
        """Add to history."""
        with self._lock:
            self.injection_history.append(result)
            if len(self.injection_history) > self.max_history:
                self.injection_history.pop(0)

    def get_decision_log(self, count: int = 20) -> List[Dict]:
        """Get recent decisions for UI display."""
        decisions = list(self.decision_log)[-count:]
        return [
            {
                "time": time.strftime("%H:%M:%S", time.localtime(d.timestamp)),
                "message": d.message[:50] + "..." if len(d.message) > 50 else d.message,
                "platform": d.platform,
                "decision": d.decision,
                "reason": d.reason,
                "relevance": f"{d.relevance_score:.1%}",
                "matches": d.matching_nodes,
                "trinity_ok": d.trinity_running,
            }
            for d in decisions
        ]

    def get_recent_injections(self, count: int = 10) -> List[InjectionResult]:
        """Get recent injections."""
        with self._lock:
            return list(self.injection_history[-count:])

    def get_last_injection(self) -> Optional[InjectionResult]:
        """Get last injection."""
        with self._lock:
            return self.injection_history[-1] if self.injection_history else None

    def get_stats(self) -> Dict[str, Any]:
        """Get stats."""
        with self._lock:
            rate = self.total_injections / self.total_requests if self.total_requests > 0 else 0
            return {
                "enabled": self.enabled,
                "debug_mode": self.debug_mode,
                "force_injection": self.force_injection,
                "total_requests": self.total_requests,
                "total_injections": self.total_injections,
                "injection_rate": round(rate, 2),
                "injections_by_platform": dict(self.injections_by_platform),
                "min_relevance_threshold": self.min_relevance,
                "history_count": len(self.injection_history),
                "decision_log_count": len(self.decision_log),
            }

    def configure(self, enabled: Optional[bool] = None, min_relevance: Optional[float] = None,
                  max_context_length: Optional[int] = None, debug_mode: Optional[bool] = None,
                  force_injection: Optional[bool] = None):
        """Update configuration."""
        with self._lock:
            if enabled is not None:
                self.enabled = enabled
                logger.info("Injection %s", "enabled" if enabled else "disabled")
            if min_relevance is not None:
                self.min_relevance = max(0.0, min(1.0, min_relevance))
                logger.info("Threshold set to %.2f", self.min_relevance)
            if max_context_length is not None:
                self.max_context_length = max(100, min(1500, max_context_length))
            if debug_mode is not None:
                self.debug_mode = debug_mode
            if force_injection is not None:
                self.force_injection = force_injection
                logger.info("Force injection %s", "enabled" if force_injection else "disabled")

    def clear_history(self):
        """Clear history."""
        with self._lock:
            self.injection_history.clear()
            self.decision_log.clear()


# Singleton
_injector: Optional[ContinuityInjector] = None
_injector_lock = threading.Lock()


def get_injector() -> ContinuityInjector:
    """Get global injector."""
    global _injector
    with _injector_lock:
        if _injector is None:
            _injector = ContinuityInjector()
        return _injector


__all__ = [
    "ContinuityInjector",
    "ContinuityContext",
    "InjectionResult",
    "InjectionDecision",
    "Platform",
    "get_injector",
]
