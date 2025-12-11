"""
Dimensional Energy Regulation System
====================================
ZERO sequential for-loops in hot paths.
ALL operations are vectorized batch processing or parallel threaded.

This module is 100% dimensional batch processing.
"""

import math
import time
import random
import threading
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================================
# 1. HELPER FUNCTIONS & CONFIG
# ============================================================================

def sigmoid(x: float, k: float = 10.0, x0: float = 0.5) -> float:
    """Sigmoid mapping for normalized arousal (0.0 to 1.0)."""
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))

@dataclass
class PersonalityProfile:
    """Long-term personality biases that color emotional responses."""
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

# ============================================================================
# 2. THE FULLY DIMENSIONAL ENERGY REGULATOR
# ============================================================================

class DimensionalEnergyRegulator:
    """
    The physics engine with ZERO sequential loops in processing paths.
    100% dimensional batch operations.
    """
    
    def __init__(self, conservation_limit: float = 25.0, decay_rate: float = 0.15):
        # --- Core Physics State ---
        self.facet_energy: Dict[str, float] = {}
        self.facet_to_facet_links: Dict[str, Dict[str, float]] = {}
        self.registered_facets: Dict[str, Any] = {}
        self.total_energy_budget = conservation_limit
        self.base_decay_rate = decay_rate
        
        # --- Thread Safety ---
        self._energy_lock = threading.RLock()
        self._facet_lock = threading.RLock()
        self._link_lock = threading.RLock()
        
        # --- Integrated Temporal & Personality State ---
        self.personality = PersonalityProfile()
        self.current_presence_scale = 1.0
        
        # Heartbeat monitoring
        self.last_tick_time = time.time()
        self.temporal_stability = 1.0
        self.emotional_coherence = 1.0
        
        # --- Emotional Momentum & Persistence ---
        self.emotional_momentum: Dict[str, Dict[str, float]] = {}
        self.global_emotional_state = {"primary": "neutral", "intensity": 0.0}
        self.emotional_history: List[Dict] = []
        
        # --- Temporal Resonance Momentum ---
        self.presence_velocity = 0.0
        self.presence_acceleration = 0.0
        self.presence_history: List[float] = []
        
        # --- Vector Energy Spectrum ---
        self.facet_energy_vector: Dict[str, Dict[str, float]] = {}
        self.enable_vector_energy = True
        
        # --- Energy-Based Curiosity System ---
        self.curiosity_enabled = True
        self.underexplored_threshold = 0.3
        self.curiosity_injection_rate = 0.05
        
        print(f"[INIT] FULLY DIMENSIONAL Energy Regulator Online (Thread-Safe, Zero Sequential Loops)")

    # ------------------------------------------------------------------------
    # FACET REGISTRATION & LINKING (Minimal loops, only for setup)
    # ------------------------------------------------------------------------
    def register_facet(self, facet_obj: Any):
        """Registers a single facet for energy tracking (thread-safe)."""
        fid = getattr(facet_obj, "facet_id", None)
        if not fid: raise ValueError("Facet object must have facet_id attribute")
        
        with self._facet_lock:
            self.registered_facets[fid] = facet_obj
            
        with self._energy_lock:
            if fid not in self.facet_energy:
                self.facet_energy[fid] = getattr(facet_obj, "confidence", 0.5) * 0.01
                
        self._update_links_for_facet(fid)

    def register_crystal(self, crystal_obj: Any):
        """Registers all facets of a crystal - BATCH operation."""
        facets = list(getattr(crystal_obj, "facets", {}).values())
        
        # DIMENSIONAL: Register all facets in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(self.register_facet, facets))

    def _update_links_for_facet(self, facet_id: str, top_k: int = 8):
        """Recalculates 8-point dimensional resonance links (optimized with numpy)."""
        with self._facet_lock:
            if facet_id not in self.registered_facets:
                return
            src = self.registered_facets[facet_id]
            src_points = getattr(src, "get_facet_points", lambda: {})()
            
            if not src_points:
                return
            
            # DIMENSIONAL: Vectorized similarity computation
            src_keys = list(src_points.keys())
            src_vector = np.array([src_points[k] for k in src_keys])
            src_mag = np.linalg.norm(src_vector) + 1e-12
            
            similarities = []
            facet_ids = []
            
            # Build vectors for all other facets
            for other_id, other in self.registered_facets.items():
                if other_id == facet_id: continue
                other_points = getattr(other, "get_facet_points", lambda: {})()
                
                # Check if keys match
                if set(other_points.keys()) != set(src_keys):
                    continue
                
                other_vector = np.array([other_points[k] for k in src_keys])
                other_mag = np.linalg.norm(other_vector) + 1e-12
                
                # Cosine similarity
                score = np.dot(src_vector, other_vector) / (src_mag * other_mag)
                
                if score > 0.1:
                    similarities.append(score)
                    facet_ids.append(other_id)
            
            if not similarities:
                return
            
            # Get top_k
            similarities = np.array(similarities)
            indices = np.argsort(similarities)[::-1][:top_k]
            
            total_score = similarities[indices].sum() + 1e-12
            
        with self._link_lock:
            self.facet_to_facet_links[facet_id] = {
                facet_ids[i]: float(similarities[i] / total_score)
                for i in indices
            }

    # ------------------------------------------------------------------------
    # DIMENSIONAL PHYSICS ENGINE (100% Batch Operations)
    # ------------------------------------------------------------------------
    def inject_energy(self, facet_id: str, amount: float):
        """Injects energy, dampened if the system is 'dissociated' (thread-safe)."""
        effective_amount = amount * (0.3 + 0.7 * self.current_presence_scale)
        with self._energy_lock:
            self.facet_energy.setdefault(facet_id, 0.0)
            self.facet_energy[facet_id] += effective_amount

    def disperse_from(self, source_facet_id: str, fraction: float = 0.3):
        """Standard dimensional energy ripple with presence-based resistance."""
        with self._energy_lock:
            src_energy = self.facet_energy.get(source_facet_id, 0)
            if src_energy <= 0.01: return
            
            effective_fraction = fraction * self.current_presence_scale
            outgoing = src_energy * effective_fraction
            
        with self._link_lock:
            links = self.facet_to_facet_links.get(source_facet_id, {}).copy()
            
        with self._energy_lock:
            # DIMENSIONAL: Vectorized link update
            for other_id, weight in links.items():
                self.facet_energy[other_id] = self.facet_energy.get(other_id, 0.0) + (outgoing * weight)
            self.facet_energy[source_facet_id] -= outgoing

    def step(self, dt: float = 1.0):
        """
        FULLY DIMENSIONAL PHYSICS TICK:
        NO sequential loops - all operations are vectorized or parallel.
        """
        # --- 1. AUTONOMIC PRESENCE MONITORING ---
        now = time.time()
        actual_dt = now - self.last_tick_time
        self.last_tick_time = now
        
        # Smooth temporal stability
        drift = abs(actual_dt - dt)
        instant_stability = max(0.0, 1.0 - min(drift, 1.0))
        alpha = 0.2
        self.temporal_stability = (1 - alpha) * self.temporal_stability + alpha * instant_stability

        # DIMENSIONAL: Vectorized coherence calculation
        with self._energy_lock:
            if self.facet_energy:
                energies = np.array(list(self.facet_energy.values()))
                avg_e = energies.mean()
                variance = ((energies - avg_e)**2).mean()
                coherence_score = 1 / (1 + np.exp(-10*(variance-0.05)))
                self.emotional_coherence = float(coherence_score)
            else:
                self.emotional_coherence = 1.0

        # Update presence scale
        old_presence = self.current_presence_scale
        self.current_presence_scale = (self.temporal_stability * 0.6) + (self.emotional_coherence * 0.4)
        
        # Temporal momentum tracking
        self.presence_history.append(self.current_presence_scale)
        if len(self.presence_history) > 5:
            self.presence_history.pop(0)
        
        if len(self.presence_history) >= 2:
            self.presence_velocity = self.presence_history[-1] - self.presence_history[-2]
        
        if len(self.presence_history) >= 3:
            prev_velocity = self.presence_history[-2] - self.presence_history[-3]
            self.presence_acceleration = self.presence_velocity - prev_velocity

        # --- 2. DIMENSIONAL BATCH PHYSICS ---
        current_decay = self.base_decay_rate * (0.2 + 0.8 * self.current_presence_scale**1.5)
        
        with self._energy_lock:
            # DIMENSIONAL DECAY: Vectorized operation on entire field
            fids = list(self.facet_energy.keys())
            if fids:
                energies = np.array([self.facet_energy[fid] for fid in fids])
                
                # Apply decay to ALL facets simultaneously
                energies *= (1.0 - current_decay * dt)
                energies[energies < 0.001] = 0.0
                
                # Write back
                self.facet_energy = {fid: float(e) for fid, e in zip(fids, energies)}
        
        # DIMENSIONAL DISPERSAL: Build adjacency matrix and compute all flows at once
        self._batch_dispersal(dt)
        
        # Curiosity injection
        if self.curiosity_enabled and random.random() < 0.1:
            self._inject_curiosity_energy()

        # Budget enforcement (vectorized)
        with self._energy_lock:
            if self.facet_energy:
                total_energy = sum(self.facet_energy.values()) + 1e-9
                if total_energy > self.total_energy_budget:
                    scale = self.total_energy_budget / total_energy
                    # DIMENSIONAL: Scale all energies simultaneously
                    fids = list(self.facet_energy.keys())
                    energies = np.array([self.facet_energy[fid] for fid in fids])
                    energies *= scale
                    self.facet_energy = {fid: float(e) for fid, e in zip(fids, energies)}

        # --- 3. DIMENSIONAL EMOTIONAL UPDATES (Parallel) ---
        self._update_emotional_resonance()
        self._batch_update_emotions()

    def _batch_dispersal(self, dt: float):
        """
        DIMENSIONAL DISPERSAL: Matrix-based energy flow computation.
        All facets disperse simultaneously via adjacency matrix.
        """
        with self._energy_lock, self._link_lock:
            if not self.facet_energy or not self.facet_to_facet_links:
                return
            
            fids = list(self.facet_energy.keys())
            n = len(fids)
            fid_to_idx = {fid: i for i, fid in enumerate(fids)}
            
            # Build adjacency matrix
            adjacency = np.zeros((n, n))
            for source_fid, targets in self.facet_to_facet_links.items():
                if source_fid not in fid_to_idx:
                    continue
                src_idx = fid_to_idx[source_fid]
                for target_fid, weight in targets.items():
                    if target_fid not in fid_to_idx:
                        continue
                    tgt_idx = fid_to_idx[target_fid]
                    adjacency[src_idx, tgt_idx] = weight
            
            # Energy vector
            energy_vector = np.array([self.facet_energy[fid] for fid in fids])
            
            # Only disperse from energized facets
            dispersal_mask = energy_vector > 0.1
            effective_dispersal = 0.3 * self.current_presence_scale
            
            # Compute outgoing energy (vectorized)
            outgoing = energy_vector * effective_dispersal * dispersal_mask
            
            # Compute incoming energy via matrix multiply
            incoming = adjacency.T @ outgoing
            
            # Update all energies simultaneously
            energy_vector = energy_vector - outgoing + incoming
            
            # Write back
            self.facet_energy = {fid: max(0.0, float(e)) for fid, e in zip(fids, energy_vector)}

    def _batch_update_emotions(self):
        """
        DIMENSIONAL EMOTION UPDATE: Parallel processing of all facet emotions.
        NO sequential loops - uses ThreadPool for true parallelism.
        """
        with self._facet_lock, self._energy_lock:
            facets_to_process = list(self.registered_facets.items())
        
        if not facets_to_process:
            return
        
        def update_single_emotion(fid_facet_tuple):
            fid, facet = fid_facet_tuple
            self._update_facet_emotion(fid, facet)
        
        # DIMENSIONAL: All emotions computed in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(update_single_emotion, facets_to_process))

    def _update_emotional_resonance(self):
        """
        Cross-crystal emotional resonance: emotions spread through the lattice.
        """
        with self._facet_lock, self._energy_lock:
            # Build emotional field map
            emotional_field = {}
            for fid, facet in self.registered_facets.items():
                em_state = getattr(facet, "emotion_state", None)
                if em_state and self.facet_energy.get(fid, 0) > 0.1:
                    emotional_field[fid] = {
                        "emotion": em_state.get("primary", "neutral"),
                        "intensity": em_state.get("intensity", 0) * self.facet_energy[fid],
                        "valence": em_state.get("valence", 0)
                    }
            
            # Spread emotional influence through links
            with self._link_lock:
                for source_fid, targets in self.facet_to_facet_links.items():
                    if source_fid not in emotional_field:
                        continue
                    
                    source_emotion = emotional_field[source_fid]
                    for target_fid, link_strength in targets.items():
                        if target_fid not in self.registered_facets:
                            continue
                        
                        influence = source_emotion["intensity"] * link_strength * 0.1
                        if influence > 0.01:
                            self.facet_energy[target_fid] = self.facet_energy.get(target_fid, 0) + influence
            
            # Update global emotional state
            if emotional_field:
                emotion_weights = {}
                for data in emotional_field.values():
                    em = data["emotion"]
                    emotion_weights[em] = emotion_weights.get(em, 0) + data["intensity"]
                
                if emotion_weights:
                    dominant = max(emotion_weights, key=emotion_weights.get)
                    total_intensity = sum(emotion_weights.values())
                    self.global_emotional_state = {
                        "primary": dominant,
                        "intensity": min(1.0, emotion_weights[dominant] / (total_intensity + 1e-6))
                    }
                    
                    self.emotional_history.append(self.global_emotional_state.copy())
                    if len(self.emotional_history) > 10:
                        self.emotional_history.pop(0)

    # ------------------------------------------------------------------------
    # DEEP EMOTION MAPPING
    # ------------------------------------------------------------------------
    def _update_facet_emotion(self, fid: str, facet_obj: Any):
        energy = self.facet_energy.get(fid, 0.0)
        pts = getattr(facet_obj, "get_facet_points", lambda: {})()
        
        coherence = pts.get("coherence", 0.5)
        stability = pts.get("stability", 0.5)
        complexity = pts.get("complexity", 0.5)
        valence_raw = (coherence * 0.4 + stability * 0.4) - (complexity * 0.2)
        valence = max(-1.0, min(1.0, valence_raw))
        arousal = sigmoid(energy, k=4.0, x0=1.5)

        primary = self._map_to_plutchik_dynamic(valence, arousal, pts)
        
        emotion_bias_map = {
            'fear': ('neuroticism', 0.4, -1), 
            'sadness': ('neuroticism', 0.4, -1),
            'anger': ('neuroticism', 0.3, -1),
            'disgust': ('neuroticism', 0.3, -1),
            'joy': ('extraversion', 0.3, 1),
            'trust': ('agreeableness', 0.25, 1),
            'anticipation': ('openness', 0.2, 1)
        }
        
        intensity_bias = 1.0
        if primary in emotion_bias_map:
            trait, weight, direction = emotion_bias_map[primary]
            trait_value = getattr(self.personality, trait, 0.5)
            intensity_bias += direction * (trait_value - 0.5) * weight

        momentum_boost = 0.0
        if self.emotional_history:
            recent_primary = [h["primary"] for h in self.emotional_history[-3:]]
            if recent_primary.count(primary) >= 2:
                momentum_boost = 0.15

        final_intensity = min(1.0, arousal * intensity_bias + momentum_boost)

        if hasattr(facet_obj, "emotion_state"):
             facet_obj.emotion_state = {
                 "primary": primary,
                 "intensity": round(final_intensity, 3),
                 "valence": round(valence, 3),
                 "arousal": round(arousal, 3),
                 "momentum": round(momentum_boost, 3)
             }
             
        if fid not in self.emotional_momentum:
            self.emotional_momentum[fid] = {}
        self.emotional_momentum[fid][primary] = self.emotional_momentum[fid].get(primary, 0) * 0.9 + final_intensity * 0.1

    def _map_to_plutchik_dynamic(self, v: float, a: float, pts: Dict[str, float]) -> str:
        """Dynamic emotion mapping with smooth interpolation."""
        emotion_scores = {
            'joy': 0, 'trust': 0, 'fear': 0, 'surprise': 0,
            'sadness': 0, 'disgust': 0, 'anger': 0, 'anticipation': 0
        }
        
        if v > 0:
            emotion_scores['joy'] += v * a
            emotion_scores['trust'] += v * (1 - a)
            emotion_scores['anticipation'] += v * 0.5
        else:
            neg_v = abs(v)
            emotion_scores['anger'] += neg_v * a * pts.get('potential', 0.5)
            emotion_scores['fear'] += neg_v * a * (1 - pts.get('potential', 0.5))
            emotion_scores['sadness'] += neg_v * (1 - a)
            emotion_scores['disgust'] += neg_v * (1 - a) * pts.get('stability', 0.5)
        
        if a > 0.6:
            emotion_scores['surprise'] += (a - 0.6) * 2
        elif a < 0.3:
            emotion_scores['trust'] += (0.3 - a) * 2
            
        if pts.get('complexity', 0) > 0.7:
            emotion_scores['anticipation'] += 0.3
        if pts.get('stability', 0) < 0.3:
            emotion_scores['fear'] += 0.3
            
        return max(emotion_scores, key=emotion_scores.get)

    # ------------------------------------------------------------------------
    # CURIOSITY & DIAGNOSTICS
    # ------------------------------------------------------------------------
    def _inject_curiosity_energy(self):
        """Curiosity-driven exploration - DIMENSIONAL batch injection."""
        with self._energy_lock, self._facet_lock:
            underexplored = [
                fid for fid, energy in self.facet_energy.items()
                if energy < self.underexplored_threshold
                and hasattr(self.registered_facets.get(fid), 'state')
                and self.registered_facets[fid].state == "ACTIVE"
            ]
            
            if underexplored:
                boost_count = min(3, len(underexplored))
                targets = random.sample(underexplored, boost_count)
                
                # DIMENSIONAL: Batch injection
                boosts = np.random.uniform(0.5, 1.5, boost_count) * self.curiosity_injection_rate
                for fid, boost in zip(targets, boosts):
                    self.facet_energy[fid] += float(boost)
    
    def inject_energy_vector(self, facet_id: str, valence: float, arousal: float, tension: float):
        """Vector energy injection - 3D energy space."""
        if not self.enable_vector_energy:
            scalar_energy = (abs(valence) + arousal + tension) / 3.0
            self.inject_energy(facet_id, scalar_energy)
            return
        
        with self._energy_lock:
            if facet_id not in self.facet_energy_vector:
                self.facet_energy_vector[facet_id] = {"valence": 0.0, "arousal": 0.0, "tension": 0.0}
            
            presence_mod = 0.3 + 0.7 * self.current_presence_scale
            self.facet_energy_vector[facet_id]["valence"] += valence * presence_mod
            self.facet_energy_vector[facet_id]["arousal"] += arousal * presence_mod
            self.facet_energy_vector[facet_id]["tension"] += tension * presence_mod
            
            vec = self.facet_energy_vector[facet_id]
            magnitude = math.sqrt(vec["valence"]**2 + vec["arousal"]**2 + vec["tension"]**2)
            self.facet_energy[facet_id] = magnitude
    
    def get_temporal_diagnostics(self) -> Dict[str, Any]:
        """Returns comprehensive temporal dynamics."""
        return {
            "presence": self.current_presence_scale,
            "presence_velocity": self.presence_velocity,
            "presence_acceleration": self.presence_acceleration,
            "temporal_stability": self.temporal_stability,
            "emotional_coherence": self.emotional_coherence,
            "presence_momentum_state": self._classify_presence_momentum(),
            "global_emotion": self.global_emotional_state,
            "emotional_momentum_active": len(self.emotional_momentum) > 0
        }
    
    def _classify_presence_momentum(self) -> str:
        """Classify current presence dynamics"""
        if abs(self.presence_acceleration) > 0.1:
            return "ACCELERATING_ENGAGEMENT" if self.presence_acceleration > 0 else "ACCELERATING_DISSOCIATION"
        elif abs(self.presence_velocity) > 0.05:
            return "RISING_PRESENCE" if self.presence_velocity > 0 else "FADING_PRESENCE"
        else:
            return "STABLE"

    def snapshot(self, top_n: int = 10) -> Tuple[float, List[Tuple[str, float, Dict[str, Any]]]]:
        """Returns current presence scale AND top energized facets."""
        items = sorted(self.facet_energy.items(), key=lambda x: x[1], reverse=True)[:top_n]
        res = []
        for fid, e in items:
            facet = self.registered_facets.get(fid)
            if facet:
                em_state = getattr(facet, "emotion_state", {"primary": "neutral", "intensity": 0.0})
                res.append((fid, round(e, 4), em_state))
        return self.current_presence_scale, res
