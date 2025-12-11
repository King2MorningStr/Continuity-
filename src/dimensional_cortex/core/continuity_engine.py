from dataclasses import dataclass
from .energy_regulator import DimensionalEnergyRegulator
from .memory_constant import DimensionalMemory, EvolutionaryGovernanceEngine
from .processing_system import CrystalMemorySystem, GovernanceEngine

@dataclass
class ContinuityPayload:
    final_prompt_text: str
    continuity_summary: str
    tokens_added: int

class ContinuityEngine:
    def __init__(self):
        self.history = {} # platform_id -> list of messages

        # Initialize Dimensional Systems
        self.energy_regulator = DimensionalEnergyRegulator()

        # Initialize Memory & Governance
        self.dim_memory = DimensionalMemory()
        self.evo_governor = EvolutionaryGovernanceEngine(self.dim_memory)

        # Initialize Crystal Processing
        # We need a theme for the governance engine, defaulting to 'general'
        self.crystal_governance = GovernanceEngine(data_theme="general")
        self.crystal_system = CrystalMemorySystem(self.crystal_governance)

    def enrich_input(self, platform_id: str, raw_user_text: str) -> ContinuityPayload:
        """
        Enriches user input by:
        1. Checking dimensional energy state.
        2. Retrieving context from DimensionalMemory.
        3. Evolving crystals based on the input concept.
        """

        # 1. Update Energy State
        # We treat the input as a facet of interaction
        # For simplicity, we use platform_id as a proxy for a facet ID here
        self.energy_regulator.inject_energy(platform_id, amount=1.0)
        self.energy_regulator.step(dt=0.1) # Advance physics

        presence_scale = self.energy_regulator.current_presence_scale

        # 2. Ingest into Evolutionary Memory
        # We treat the input as a 'TEXT' data object
        data_packet = {
            "text": raw_user_text,
            "source_doc": f"platform:{platform_id}",
            "concept": f"USER_INPUT_{platform_id}"
        }
        self.evo_governor.ingest_data(data_packet)

        # 3. Crystal Evolution
        # Use the first few words as a potential concept key
        concept_key = raw_user_text.split()[0][:20] if raw_user_text else "EMPTY"
        crystal = self.crystal_system.use_crystal(concept_key, {"role": "user_input", "content": raw_user_text})

        # 4. Construct Summary
        # Retrieve relevant context from memory
        # (This is a simplified retrieval simulation)
        node_id = self.dim_memory.find_node_id_by_concept(f"USER_INPUT_{platform_id}")
        context_str = ""
        if node_id:
            node = self.dim_memory.get_node(node_id)
            if node:
                context_str = f"[Memory: {len(node.dimension_links)} links]"

        crystal_status = ""
        if crystal:
            crystal_status = f"[Crystal: {crystal.level.name}]"

        summary = f"Presence: {presence_scale:.2f} | {context_str} {crystal_status}"

        # Ideally, we would append retrieved relevant history here
        # For now, we just pass the text through
        enriched_text = raw_user_text

        return ContinuityPayload(
            final_prompt_text=enriched_text,
            continuity_summary=summary,
            tokens_added=0
        )

    def record_output(self, platform_id: str, output_text: str):
        if platform_id not in self.history:
            self.history[platform_id] = []
        self.history[platform_id].append({"role": "ai", "content": output_text})

        # Feed back into the system
        # 1. Energy
        self.energy_regulator.inject_energy(platform_id, amount=0.5)

        # 2. Memory
        data_packet = {
            "text": output_text,
            "source_doc": f"platform:{platform_id}",
            "concept": f"AI_OUTPUT_{platform_id}"
        }
        self.evo_governor.ingest_data(data_packet)

        print(f"[ContinuityEngine] Recorded output for {platform_id} and updated dimensional state.")
