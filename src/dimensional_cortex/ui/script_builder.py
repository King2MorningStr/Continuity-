from ..core.platform_registry import AiWebPlatform

class PortalScriptBuilder:
    @staticmethod
    def build_platform_setup_script(platform: AiWebPlatform) -> str:
        """
        Builds the JavaScript code to be injected into the platform's web page
        to set up observers and bridges.
        """
        # Note: This is a conceptual implementation of the JS logic described in the architecture.
        # In a real deployment, this would be robust JS code.
        return f"""
        (function() {{
            console.log("Initializing UDAC Bridge for {platform.name}");

            const config = {{
                inputSelector: '{platform.input_selector}',
                userMessageSelector: '{platform.user_message_selector}',
                aiMessageSelector: '{platform.ai_message_selector}',
                transcriptSelector: '{platform.transcript_selector or ""}',
                liveIndicatorSelector: '{platform.live_mode_indicator_selector or ""}'
            }};

            // 1. Detect user messages & AI responses
            const observer = new MutationObserver((mutations) => {{
                // Logic to scan DOM and call window.UDACBridge.onPlatform...
            }});
            observer.observe(document.body, {{ childList: true, subtree: true }});

            // 2. Detect Live transcript (if applicable)
            if (config.transcriptSelector) {{
                // Logic for transcript observation
            }}

        }})();
        """

    @staticmethod
    def build_send_prompt_script(platform: AiWebPlatform, enriched_text: str) -> str:
        """
        Builds the JavaScript to inject enriched text into the input field and send it.
        """
        import json
        safe_text = json.dumps(enriched_text)

        return f"""
        (function() {{
            const input = document.querySelector('{platform.input_selector}');
            if (input) {{
                input.value = {safe_text};
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));

                // Optional: Trigger send if a send selector is defined
                // const sendBtn = document.querySelector('{platform.send_selector}');
                // if (sendBtn) sendBtn.click();

                // Or simulate Enter key
                input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter' }}));
            }} else {{
                console.error("UDAC: Input field not found for selector: {platform.input_selector}");
            }}
        }})();
        """
