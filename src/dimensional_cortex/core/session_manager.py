from .continuity_engine import ContinuityEngine
from .logger import InteractionLogger

class SessionManager:
    def __init__(self, continuity_engine: ContinuityEngine, logger: InteractionLogger):
        self.continuity_engine = continuity_engine
        self.logger = logger
        self.current_platform_id = None

    def on_user_submit_from_udac(self, platform_id: str, raw_user_text: str, web_host):
        enriched = self.continuity_engine.enrich_input(
            platform_id=platform_id,
            raw_user_text=raw_user_text
        )

        self.logger.log_user_input(
            platform_id=platform_id,
            raw=raw_user_text,
            enriched=enriched.final_prompt_text,
            continuity_summary=enriched.continuity_summary
        )

        web_host.inject_enriched_prompt(enriched.final_prompt_text)

    def on_platform_user_message(self, platform_id: str, text: str):
        self.logger.log_platform_user_echo(platform_id, text)

    def on_platform_ai_message(self, platform_id: str, text: str):
        self.logger.log_ai_output(platform_id, text)
        self.continuity_engine.record_output(platform_id, text)

    def on_live_transcript_chunk(self, platform_id: str, text: str):
        self.logger.log_live_transcript_chunk(platform_id, text)
        self.continuity_engine.record_output(platform_id, text)

    def on_live_mode_changed(self, platform_id: str, active: bool):
        self.logger.log_live_mode_state(platform_id, active)
