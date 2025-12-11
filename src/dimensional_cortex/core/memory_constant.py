"""
Dimensional Memory Constant
===========================

This module contains the Dimensional Processing System.
It is a "living" system that can learn and evolve.

This is the "PERFECTED" module, implementing:
1.  **Inherited Governance ("Mutation"):** Parent Laws (like JSON) can
    "mutate" the logic of Child Laws (like Security).
2.  **Generational Linking ("Cross-Law"):** The system uses recursion
    to process nested data, creating two-way parent-child links
    between DataNodes.
"""

import threading
import queue
import json
import time
import os
import uuid
import logging
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable

# --- Configuration Constants ---
# These should ideally be relative to a data directory or configured
BASE_SAVE_FILE = "system_base_state.json"
DELTA_LOG_FILE = "system_live.deltalog"
TEMP_SAVE_FILE = "system_base_state.tmp"
MERGE_INTERVAL_SECONDS = 30
LOG_FORMAT = '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# --- Global "Live Save" Components ---
SAVE_QUEUE = queue.Queue()
_save_thread_active = threading.Event()
_merge_thread_active = threading.Event()


# ============================================================================
# 1. CORE DATA STRUCTURES (The "Autonomic" System)
# ============================================================================

@dataclass
class DataNode:
    """
    The smallest unit of data. It includes the "live save" trigger.
    (No changes were needed for perfection)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dimension_links: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    last_modified_timestamp: float = field(default_factory=time.time)

    def modify(self, payload_update: Dict[str, Any] = None, link_update: List[str] = None):
        """
        The "Setter" function. This is the "live" part of the "live save."
        It updates the node and pushes it to the save queue.
        """
        modified = False
        
        if payload_update:
            for key, value in payload_update.items():
                if self.payload.get(key) != value:
                    self.payload[key] = value
                    modified = True
            
        if link_update:
            for link in link_update:
                if link not in self.dimension_links:
                    self.dimension_links.append(link)
                    modified = True
        
        if modified:
            logging.info(f"Modifying Node {self.id}...")
            self.last_modified_timestamp = time.time()
            SAVE_QUEUE.put(self)
            logging.info(f"Node {self.id} queued for live save.")

    def to_dict(self):
        return {
            "id": self.id, "dimension_links": self.dimension_links,
            "payload": self.payload, "last_modified_timestamp": self.last_modified_timestamp
        }
    
    @staticmethod
    def from_dict(data: Dict):
        return DataNode(
            id=data.get('id', str(uuid.uuid4())),
            dimension_links=data.get('dimension_links', []),
            payload=data.get('payload', {}),
            last_modified_timestamp=data.get('last_modified_timestamp', time.time())
        )


class DimensionalMemory:
    """
    The "Universe" object. Holds all DataNodes and provides
    fast, indexed access. This is the "unconscious" part of the brain.
    """
    def __init__(self):
        self.nodes: Dict[str, DataNode] = {}
        self.dimension_index: Dict[str, List[str]] = {}
        self.concept_index: Dict[str, str] = {}
        self.last_global_save_timestamp: float = 0.0
        self._load_from_base_file()

    def _load_from_base_file(self):
        logging.info(f"Loading from {BASE_SAVE_FILE}...")
        if not os.path.exists(BASE_SAVE_FILE):
            logging.warning(f"{BASE_SAVE_FILE} not found. Starting fresh.")
            return
        try:
            with open(BASE_SAVE_FILE, 'r') as f:
                data = json.load(f)
            self.last_global_save_timestamp = data.get('last_global_save_timestamp', 0.0)
            loaded_nodes = data.get('nodes', {})
            for node_id, node_data in loaded_nodes.items():
                node = DataNode.from_dict(node_data)
                self.nodes[node_id] = node
                self._update_indices(node)
            logging.info(f"Load complete. {len(self.nodes)} nodes loaded.")
        except Exception as e:
            logging.error(f"CRITICAL: Failed to load {BASE_SAVE_FILE}. Error: {e}")

    def _update_indices(self, node: DataNode):
        for link in node.dimension_links:
            if link not in self.dimension_index:
                self.dimension_index[link] = []
            if node.id not in self.dimension_index[link]:
                self.dimension_index[link].append(node.id)
        concept = node.payload.get("concept")
        if concept:
            self.concept_index[concept] = node.id

    def add_node(self, node: DataNode):
        if node.id in self.nodes:
            logging.warning(f"Node {node.id} already exists. Overwriting.")
        self.nodes[node.id] = node
        self._update_indices(node)
        node.modify() # Trigger the save queue

    def modify_node(self, node_id: str, payload_update: Dict[str, Any] = None, link_update: List[str] = None):
        if node_id not in self.nodes:
            logging.error(f"Modify failed: Node {node_id} not found.")
            return
        node = self.nodes[node_id]
        node.modify(payload_update, link_update)
        if link_update or (payload_update and "concept" in payload_update):
            self._update_indices(node)
    
    def get_node(self, node_id: str) -> Optional[DataNode]:
        return self.nodes.get(node_id)
        
    def find_node_id_by_concept(self, concept_name: str) -> Optional[str]:
        return self.concept_index.get(concept_name)


# ============================================================================
# 2. KNOWN LAW SET PLUG-INS (The "Known World")
# --- PERFECTION: All 'analyze_data' functions now accept 'parent_law' ---
# ============================================================================

class SecurityLawSet:
    """Applies laws to Security data."""
    def __init__(self):
        self.name = "SECURITY"
        self.fingerprint_keys = {"ip", "action", "threat_level", "vector_complexity"}
        logging.info("Security Law Set initialized.")
        
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        logging.info(f"SECURITY LAWSET: Analyzing {data.get('ip')}...")
        
        # 1. Standard "SecurityLaw" logic
        concept_name = f"IP_{data.get('ip')}"
        dimensions = ["dim_theme:security"]
        action = data.get("action", "unknown")
        if action == "login_fail": dimensions.append("dim_event:auth_fail")
        elif action == "port_scan": dimensions.append("dim_event:port_scan")
        payload_update = { "last_action": action, "last_threat_level": data.get("threat_level") }

        # --- PERFECTION: "Inherited Governance" (Mutation) Logic ---
        if parent_law:
            dimensions.append(f"dim_mutator:{parent_law.name}")
            if parent_law.name == "JSON":
                # Mutate the payload to fit the parent's "JSON" structure
                payload_update = {
                    "json_leaf_data": payload_update,
                    "structural_role": "security_content"
                }

        # 2. Return the "mutated" rules
        return {
            "concept_name": concept_name, "new_dimensions": dimensions,
            "payload_update": payload_update
        }

class ClimateLawSet:
    """Applies laws to Climate data."""
    def __init__(self):
        self.name = "CLIMATE"
        self.fingerprint_keys = {"sensor_id", "temp", "anomaly", "temp_delta"}
        logging.info("Climate Law Set initialized.")
        
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        logging.info(f"CLIMATE LAWSET: Analyzing {data.get('sensor_id')}...")
        
        # 1. Standard "ClimateLaw" logic
        concept_name = f"SENSOR_{data.get('sensor_id')}"
        dimensions = ["dim_theme:climate"]
        anomaly = data.get("anomaly", "none")
        if anomaly == "high": dimensions.append("dim_anomaly:high")
        payload_update = { "last_temp": data.get("temp"), "last_anomaly": anomaly }
        
        # --- PERFECTION: "Inherited Governance" (Mutation) Logic ---
        if parent_law:
            dimensions.append(f"dim_mutator:{parent_law.name}")
            if parent_law.name == "JSON":
                payload_update = {
                    "json_leaf_data": payload_update,
                    "structural_role": "climate_content"
                }
                
        return {
            "concept_name": concept_name, "new_dimensions": dimensions,
            "payload_update": payload_update
        }

class TextLawSet:
    """Applies laws to Unstructured Text."""
    def __init__(self):
        self.name = "TEXT"
        self.fingerprint_keys = {"text", "source_doc"}
        logging.info("Text Law Set initialized.")
        
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        text = data.get("text", "")
        logging.info(f"TEXT LAWSET: Analyzing '{text[:20]}...'")
        
        # 1. Standard logic
        sentiment = "positive" if "on track" in text else "negative" if "failed" in text else "neutral"

        if "concept" in data:
            concept_name = data["concept"]
        else:
            concept_name = f"TXT_{uuid.uuid4().hex[:6]}"

        dimensions = ["dim_theme:text", f"dim_sentiment:{sentiment}"]
        payload_update = { "raw_text": text, "char_count": len(text) }
        
        # --- PERFECTION: "Inherited Governance" (Mutation) Logic ---
        if parent_law:
            dimensions.append(f"dim_mutator:{parent_law.name}")
            if parent_law.name == "JSON":
                payload_update = {
                    "json_leaf_data": payload_update,
                    "structural_role": "text_content"
                }

        return {
            "concept_name": concept_name,
            "new_dimensions": dimensions,
            "payload_update": payload_update
        }

# (Other LawSets follow the same pattern... brevity for example)

class TabularLawSet:
    def __init__(self): self.name = "TABULAR"; self.fingerprint_keys = {"row", "schema_name"}
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        schema_name = data.get("schema_name", "unknown_schema")
        dimensions = ["dim_theme:tabular", f"dim_schema_link:{schema_name}"]
        payload_update = data.get("row", {})
        if parent_law: dimensions.append(f"dim_mutator:{parent_law.name}")
        return { "concept_name": f"ROW_{schema_name}_{uuid.uuid4().hex[:6]}",
                 "new_dimensions": dimensions, "payload_update": payload_update }

class JsonLawSet:
    def __init__(self): self.name = "JSON"; self.fingerprint_keys = {"json_data", "root_concept"}
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        root_concept = data.get("root_concept", f"JSON_{uuid.uuid4().hex[:6]}")
        dimensions = ["dim_theme:json", "dim_structural:container"]
        payload_update = data.get("json_data", {})
        if parent_law: dimensions.append(f"dim_mutator:{parent_law.name}")
        return { "concept_name": root_concept, "new_dimensions": dimensions,
                 "payload_update": payload_update }

class ImageLawSet:
    def __init__(self): self.name = "IMAGE"; self.fingerprint_keys = {"filepath", "width", "height"}
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        filepath = data.get("filepath", "unknown.img"); width, height = data.get("width", 0), data.get("height", 0)
        format = os.path.splitext(filepath)[1].lower().strip('.')
        dimensions = ["dim_theme:image", f"dim_format:{format}"]
        payload_update = { "filepath": filepath, "megapixels": (width * height) / 1_000_000 }
        if parent_law: dimensions.append(f"dim_mutator:{parent_law.name}")
        return { "concept_name": f"IMG_{os.path.basename(filepath)}",
                 "new_dimensions": dimensions, "payload_update": payload_update }

class AudioLawSet:
    def __init__(self): self.name = "AUDIO"; self.fingerprint_keys = {"filepath", "duration", "artist"}
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        filepath = data.get("filepath", "unknown.aud"); artist = data.get("artist", "Unknown").replace(' ', '_')
        dimensions = ["dim_theme:audio", f"dim_artist:{artist}"]
        payload_update = { "filepath": filepath, "duration_min": data.get("duration", 0) / 60.0 }
        if parent_law: dimensions.append(f"dim_mutator:{parent_law.name}")
        return { "concept_name": f"AUD_{os.path.basename(filepath)}",
                 "new_dimensions": dimensions, "payload_update": payload_update }

class BinaryLawSet:
    def __init__(self): self.name = "BINARY"; self.fingerprint_keys = {"filepath", "data_blob"}
    def analyze_data(self, data: dict, parent_law: Optional[Any] = None) -> dict:
        filepath = data.get("filepath", "unknown.bin")
        dimensions = ["dim_theme:binary", "dim_status:unprocessed"]
        payload_update = { "filepath": filepath, "size_bytes": data.get("size_bytes", 0) }
        if parent_law: dimensions.append(f"dim_mutator:{parent_law.name}")
        return { "concept_name": f"BIN_{os.path.basename(filepath)}",
                 "new_dimensions": dimensions, "payload_update": payload_update }


# ============================================================================
# 3. EVOLUTIONARY GOVERNANCE ENGINE (The "Conscious Mind")
# ============================================================================

class LawGenerator:
    """
    The "meta-conscious" part of the brain.
    Its job is to analyze unknown data and *write a new LawSet*
    by adapting laws from the closest "known" relative.
    """
    def __init__(self, known_law_sets: Dict[str, Any]):
        self.known_law_sets = known_law_sets
        logging.info("Law Generator (Meta-Brain) initialized.")

    def _fingerprint_data(self, data: dict) -> set:
        """Step 1: Get the 'fingerprint' (the set of keys) of the new data."""
        return set(data.keys())

    def _find_closest_law(self, data_fingerprint: set) -> Optional[Tuple[str, Any]]:
        """Step 2: Compare fingerprints to find the closest known LawSet."""
        best_match = None
        highest_score = 0.0
        
        for domain, law_set in self.known_law_sets.items():
            if not hasattr(law_set, 'fingerprint_keys'):
                continue
            known_keys = law_set.fingerprint_keys
            intersection = data_fingerprint.intersection(known_keys)
            union = data_fingerprint.union(known_keys)
            score = len(intersection) / len(union) if union else 0
            
            if score > highest_score and score > 0.2:
                highest_score = score
                best_match = (domain, law_set)
                
        if best_match:
            logging.info(f"LAW GENERATOR: Closest match is '{best_match[0]}' (Score: {highest_score:.2f}).")
        else:
            logging.warning("LAW GENERATOR: No close match found. Will use fallback.")
        return best_match

    def _adapt_law(self, data: dict, base_law_set: Any) -> Callable:
        """
        Step 3: Generate the new "analyze_data" function by *adapting*
        the logic from the base law set.
        """
        logging.info(f"LAW GENERATOR: Adapting laws from '{base_law_set.name}'...")
        
        data_keys = list(data.keys())
        # --- PERFECTION: Smarter concept naming ---
        concept_key_options = ["id", "concept", "name", "filepath", "ip"]
        concept_key = data_keys[0] # Fallback
        for key in concept_key_options:
            if key in data_keys:
                concept_key = key
                break
        new_theme = f"dyn_{concept_key}"
        
        # --- PERFECTION: Generated function must *also* accept parent_law ---
        def new_analyze_func(data_dict: dict, parent_law: Optional[Any] = None) -> dict:
            logging.info(f"DYNAMIC LAWSET ({new_theme}): Analyzing {data_dict.get(concept_key)}...")
            
            concept_name = f"DYN_{data_dict.get(concept_key)}"
            dimensions = [
                f"dim_theme:{new_theme}",
                f"dim_adapted_from:{base_law_set.name}"
            ]
            payload_update = data_dict # Save the whole payload
            
            # --- PERFECTION: The generated law also obeys mutation ---
            if parent_law:
                dimensions.append(f"dim_mutator:{parent_law.name}")
                if parent_law.name == "JSON":
                    payload_update = {
                        "json_leaf_data": payload_update,
                        "structural_role": "dynamic_content"
                    }

            return {
                "concept_name": concept_name,
                "new_dimensions": dimensions,
                "payload_update": payload_update
            }
            
        return new_analyze_func

    def generate_new_law(self, unknown_data: dict) -> Optional[Tuple[str, Any]]:
        """
        Executes your 4-step logic to create a new LawSet class *dynamically*.
        """
        data_fingerprint = self._fingerprint_data(unknown_data)
        match = self._find_closest_law(data_fingerprint)
        base_law = match[1] if match else self.known_law_sets["BINARY"]

        try:
            new_analyze_function = self._adapt_law(unknown_data, base_law)
            new_domain_name = f"DYN_{list(data_fingerprint)[0].upper()}"
            
            # --- PERFECTION: Dynamically created class must match new interface ---
            NewLawSetClass = type(
                f"Dynamic{new_domain_name}LawSet",
                (object,),
                {
                    "name": new_domain_name,
                    "fingerprint_keys": data_fingerprint,
                    # --- PERFECTION: Lambda now includes parent_law ---
                    "analyze_data": staticmethod(lambda data, parent_law=None: new_analyze_function(data, parent_law)),
                    "__init__": lambda self: setattr(self, 'name', new_domain_name)
                }
            )
            
            logging.info(f"LAW GENERATOR: Successfully generated new class '{NewLawSetClass.name}'.")
            return new_domain_name, NewLawSetClass()
            
        except Exception as e:
            logging.error(f"LAW GENERATOR: Failed to adapt law. Error: {e}")
            return None, None


class EvolutionaryGovernanceEngine:
    """
    The "Conscious Mind." Now fully recursive and generational.
    """
    
    def __init__(self, memory_system: DimensionalMemory):
        self.memory = memory_system
        self.assessment_log = []
        
        # Load all "known" Law Set plug-ins
        self.law_sets: Dict[str, Any] = {
            "SECURITY": SecurityLawSet(),
            "CLIMATE": ClimateLawSet(),
            "TEXT": TextLawSet(),
            "TABULAR": TabularLawSet(),
            "JSON": JsonLawSet(),
            "IMAGE": ImageLawSet(),
            "AUDIO": AudioLawSet(),
            "BINARY": BinaryLawSet()
        }
        
        self.law_generator = LawGenerator(self.law_sets)
        logging.info(f"Evolutionary Governor Online. Loaded {len(self.law_sets)} static Law Sets.")

    def _identify_domain(self, data: dict) -> Optional[str]:
        """Identifies the data's domain (static or dynamic)."""
        data_fingerprint = set(data.keys())
        for domain, law_set in self.law_sets.items():
            if hasattr(law_set, 'fingerprint_keys'):
                if data_fingerprint.issuperset(law_set.fingerprint_keys):
                    return domain
        
        logging.warning(f"DOMAIN ID: Could not identify domain for {data_fingerprint}")
        return "UNKNOWN"

    def _find_deeper_data(self, data: dict) -> List[dict]:
        """
        --- PERFECTION: New helper function ---
        Finds "deeper data" (nested dicts or lists of dicts) for recursion.
        """
        deeper_items = []
        if not isinstance(data, dict):
            return []
            
        for key, value in data.items():
            if isinstance(value, dict):
                deeper_items.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        deeper_items.append(item)
        return deeper_items

    # --- PERFECTION: `ingest_data` is now recursive (Generational) ---
    def ingest_data(self, data: dict, parent_node: Optional[DataNode] = None, parent_law_object: Optional[Any] = None):
        """
        The main entry point. Now fully recursive.
        """
        # 1. Identify Domain
        domain = self._identify_domain(data)
            
        # 2. Handle "UNKNOWN" domain
        if domain == "UNKNOWN":
            logging.info(f"GOVERNOR: Unknown data type. Engaging Law Generator...")
            new_domain, new_law_class = self.law_generator.generate_new_law(data)
            
            if new_domain and new_law_class:
                logging.info(f"GOVERNOR: New Law Set '{new_domain}' generated! Adding to library.")
                self.law_sets[new_domain] = new_law_class
                domain = new_domain
            else:
                logging.error(f"GOVERNOR: Law Generator failed. Discarding: {data}")
                return
            
        # 3. Apply domain-specific laws (with "mutation")
        law_set = self.law_sets.get(domain)
        try:
            # --- PERFECTION: Pass the parent_law_object for mutation ---
            node_rules = law_set.analyze_data(data, parent_law_object)
            
            # --- PERFECTION: Pass the parent_node for linking ---
            node_obj = self._auto_write_node(node_rules, parent_node)
            
            self.assess_law_application(domain, node_rules, node_obj)

            # --- PERFECTION: The "Generational" Recursive Call ---
            if node_obj: # Only recurse if the parent was successfully written
                deeper_data_items = self._find_deeper_data(data)
                if deeper_data_items:
                    logging.info(f"GOVERNOR: Found {len(deeper_data_items)} deeper items in '{node_obj.payload.get('concept')}'. Recursing...")
                    for item in deeper_data_items:
                        # This is the "Generational" call
                        self.ingest_data(
                            item, 
                            parent_node=node_obj, 
                            parent_law_object=law_set
                        )
            
        except Exception as e:
            logging.critical(f"GOVERNOR: Law Set '{domain}' failed! Error: {e}", exc_info=True)

    # --- PERFECTION: `_auto_write_node` now handles two-way linking ---
    def _auto_write_node(self, rules: dict, parent_node: Optional[DataNode] = None) -> Optional[DataNode]:
        """
        Finds or creates the node. Now returns the full DataNode object
        and performs two-way "Generational" linking.
        """
        concept = rules['concept_name']
        node_id = self.memory.find_node_id_by_concept(concept)
        node_to_return = None

        if node_id:
            # Modify existing node
            self.memory.modify_node(
                node_id, rules.get('payload_update'), rules.get('new_dimensions')
            )
            node_to_return = self.memory.get_node(node_id)
        else:
            # Create new node
            base_payload = {"concept": concept}
            if rules.get('payload_update'):
                base_payload.update(rules['payload_update'])
            
            new_node = DataNode(
                dimension_links=rules.get('new_dimensions', []),
                payload=base_payload
            )
            # Add to memory (this also triggers the first save)
            self.memory.add_node(new_node)
            node_to_return = new_node
        
        # --- PERFECTION: "Two-Way Street" Generational Linking ---
        if parent_node and node_to_return:
            # 1. Link Child to Parent
            node_to_return.modify(link_update=[f"dim_parent_link:{parent_node.id}"])
            # 2. Link Parent to Child
            parent_node.modify(link_update=[f"dim_child_link:{node_to_return.id}"])

        return node_to_return

    # --- PERFECTION: Updated signature ---
    def assess_law_application(self, domain: str, rules: dict, node_obj: Optional[DataNode]):
        """
        The "feedback loop." The Governor assesses its own work.
        """
        success = node_obj is not None
        self.assessment_log.append({
            "timestamp": time.time(), "domain": domain, "success": success,
        })
        logging.info(f"GOVERNOR: Assessed application of '{domain}'. Success: {success}")


# ============================================================================
# 4. AUTONOMIC SAVE SYSTEM THREADS
# ============================================================================

def continuous_save_thread():
    """Watches the queue and writes to the delta log."""
    logging.info("Save Thread started. Waiting for changes...")
    while _save_thread_active.is_set():
        try:
            node_to_save = SAVE_QUEUE.get(timeout=1.0)
            log_entry = json.dumps(node_to_save.to_dict())
            with open(DELTA_LOG_FILE, 'a') as f:
                f.write(log_entry + '\n')
            SAVE_QUEUE.task_done()
            logging.info(f"SAVETHREAD: Node {node_to_save.id} written to log.")
        except queue.Empty:
            continue
        except Exception as e:
            logging.error(f"SAVETHREAD: Error: {e}")
    logging.info("Save Thread shutting down.")

def background_merge():
    """Periodically merges the delta log into the base state file."""
    logging.info("Merge Thread started.")
    while _merge_thread_active.wait(MERGE_INTERVAL_SECONDS):
        if not _merge_thread_active.is_set(): break
        logging.info("MERGETHREAD: Merge process triggered...")
        if not os.path.exists(DELTA_LOG_FILE):
            logging.info("MERGETHREAD: No delta log found. Merge skipped.")
            continue
        try:
            temp_log_file = DELTA_LOG_FILE + ".merging"
            try: os.rename(DELTA_LOG_FILE, temp_log_file)
            except FileNotFoundError: continue

            current_state_nodes = {}
            base_timestamp = 0.0
            if os.path.exists(BASE_SAVE_FILE):
                with open(BASE_SAVE_FILE, 'r') as f:
                    base_data = json.load(f)
                    current_state_nodes = base_data.get('nodes', {})
                    base_timestamp = base_data.get('last_global_save_timestamp', 0.0)
            
            latest_timestamp = base_timestamp
            with open(temp_log_file, 'r') as f:
                for line in f:
                    try:
                        node_data = json.loads(line)
                        current_state_nodes[node_data['id']] = node_data
                        if node_data['last_modified_timestamp'] > latest_timestamp:
                            latest_timestamp = node_data['last_modified_timestamp']
                    except json.JSONDecodeError:
                        logging.warning(f"MERGETHREAD: Skipping corrupt line: {line}")
            
            merged_data = {
                "last_global_save_timestamp": latest_timestamp, "nodes": current_state_nodes
            }
            with open(TEMP_SAVE_FILE, 'w') as f:
                json.dump(merged_data, f, indent=2)
            
            os.replace(TEMP_SAVE_FILE, BASE_SAVE_FILE)
            os.remove(temp_log_file)
            logging.info(f"MERGETHREAD: Merge complete. {len(current_state_nodes)} nodes in new base state.")
        except Exception as e:
            logging.error(f"MERGETHREAD: Critical Error: {e}")
            if os.path.exists(temp_log_file):
                os.rename(temp_log_file, DELTA_LOG_FILE)
    logging.info("Merge Thread shutting down.")


# ============================================================================
# 5. SYSTEM CONTROL
# ============================================================================

def start_memory_system() -> Tuple[EvolutionaryGovernanceEngine, DimensionalMemory, threading.Thread, threading.Thread]:
    """Initializes the *entire* standalone system."""
    logging.info("--- Starting Dimensional Memory System ---")
    _save_thread_active.set()
    _merge_thread_active.set()
    memory = DimensionalMemory()
    governor = EvolutionaryGovernanceEngine(memory)
    save_thread = threading.Thread(target=continuous_save_thread, name="SaveThread")
    merge_thread = threading.Thread(target=background_merge, name="MergeThread")
    save_thread.start()
    merge_thread.start()
    return governor, memory, save_thread, merge_thread

def stop_memory_system(save_thread: threading.Thread, merge_thread: threading.Thread):
    """Safely shuts down the background threads."""
    logging.info("--- Shutting Down Dimensional Memory System ---")
    _merge_thread_active.clear()
    _save_thread_active.clear()
    merge_thread.join()
    save_thread.join()
    logging.info("Processing remaining save queue...")
    while not SAVE_QUEUE.empty():
        try:
            node_to_save = SAVE_QUEUE.get_nowait()
            with open(DELTA_LOG_FILE, 'a') as f:
                f.write(json.dumps(node_to_save.to_dict()) + '\n')
            SAVE_QUEUE.task_done()
        except Exception as e:
            logging.error(f"Shutdown save error: {e}")
    logging.info("System shutdown complete.")
