import datetime

class InteractionLogger:
    def log_user_input(self, platform_id: str, raw: str, enriched: str, continuity_summary: str):
        print(f"[{datetime.datetime.now()}] USER_INPUT({platform_id}): raw='{raw}', enriched='{enriched}', summary='{continuity_summary}'")

    def log_platform_user_echo(self, platform_id: str, text: str):
        print(f"[{datetime.datetime.now()}] USER_ECHO({platform_id}): {text}")

    def log_ai_output(self, platform_id: str, text: str):
        print(f"[{datetime.datetime.now()}] AI_OUTPUT({platform_id}): {text}")

    def log_live_transcript_chunk(self, platform_id: str, text: str):
        print(f"[{datetime.datetime.now()}] LIVE_CHUNK({platform_id}): {text}")

    def log_live_mode_state(self, platform_id: str, active: bool):
        print(f"[{datetime.datetime.now()}] LIVE_MODE({platform_id}): {'Active' if active else 'Inactive'}")
