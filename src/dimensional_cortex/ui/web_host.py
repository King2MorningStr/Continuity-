import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from ..core.platform_registry import AiWebPlatform
from ..core.session_manager import SessionManager

class PortalWebHost:
    def __init__(self, platform: AiWebPlatform, session_manager: SessionManager):
        self.platform = platform
        self.session_manager = session_manager
        self.webview = None

    def create_widget(self):
        self.webview = toga.WebView(
            url=self.platform.base_url,
            style=Pack(flex=1),
            on_webview_load=self.on_load
        )
        return self.webview

    def on_load(self, widget):
        print(f"Loaded {self.platform.name}")
        self.inject_scripts()

    def inject_scripts(self):
        # In a real Toga Android app, we might need platform specific code to inject
        # complex bridges. For now, we simulate the JS injection logic.
        js = self.build_platform_script()
        self.webview.evaluate_javascript(js)

    def build_platform_script(self):
        # Conceptual JS injection
        return f"""
        console.log("Injecting UDAC scripts for {self.platform.name}");
        // Here we would set up MutationObservers as described in architecture
        """

    def inject_enriched_prompt(self, enriched_text: str):
        import json
        safe_text = json.dumps(enriched_text)
        # Conceptual JS to inject text
        js = f"""
        (function() {{
            const input = document.querySelector('{self.platform.input_selector}');
            if (input) {{
                input.value = {safe_text}; # Basic injection
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }})();
        """
        if self.webview:
            self.webview.evaluate_javascript(js)
