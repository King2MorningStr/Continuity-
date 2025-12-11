from ..core.platform_registry import AiWebPlatform

class PortalScriptBuilder:
    @staticmethod
    def build_platform_setup_script(platform: AiWebPlatform) -> str:
        """
        Builds the JavaScript code to be injected into the platform's web page
        to set up observers and bridges.
        """
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

            // Helper to send message back to Python/Native
            function notifyBridge(method, data) {{
                // Toga WebView doesn't have a direct 'window.bridge.method' standard across all platforms.
                // A common pattern is changing window.location or console.log if intercepted.
                // Here we assume a console.log interface for the 'js_bridge.py' to pick up via stdout capture
                // or a specific bound object if supported.
                // For this implementation, we will log a structured JSON string.

                const payload = JSON.stringify({{method: method, data: data}});
                console.log("UDAC_BRIDGE:" + payload);
            }}

            // 1. Detect user messages & AI responses
            const observer = new MutationObserver((mutations) => {{
                mutations.forEach((mutation) => {{
                    if (mutation.type === 'childList') {{
                        mutation.addedNodes.forEach((node) => {{
                            if (node.nodeType === Node.ELEMENT_NODE) {{
                                // Check for User Message
                                if (node.matches(config.userMessageSelector) || node.querySelector(config.userMessageSelector)) {{
                                    const text = node.innerText || "";
                                    notifyBridge('on_platform_user_message_detected', text);
                                }}
                                // Check for AI Message
                                if (node.matches(config.aiMessageSelector) || node.querySelector(config.aiMessageSelector)) {{
                                    const text = node.innerText || "";
                                    notifyBridge('on_platform_ai_message_detected', text);
                                }}
                            }}
                        }});
                    }}
                }});
            }});

            // Observe the document body for changes
            observer.observe(document.body, {{ childList: true, subtree: true }});

            // 2. Detect Live transcript (if applicable)
            if (config.transcriptSelector) {{
                 const transcriptObserver = new MutationObserver((mutations) => {{
                    mutations.forEach((mutation) => {{
                        if (mutation.type === 'childList' || mutation.type === 'characterData') {{
                            const target = document.querySelector(config.transcriptSelector);
                            if (target) {{
                                notifyBridge('on_live_transcript_chunk_detected', target.innerText);
                            }}
                        }}
                    }});
                 }});
                 const target = document.querySelector(config.transcriptSelector);
                 if (target) {{
                     transcriptObserver.observe(target, {{ childList: true, characterData: true, subtree: true }});
                 }} else {{
                     // Retry later if not found immediately?
                 }}
            }}

            console.log("UDAC Bridge initialized.");

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
                // Set the value
                input.value = {safe_text};
                // Dispatch events to simulate user typing so frameworks like React pick it up
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));

                // Trigger send
                setTimeout(() => {{
                     const sendBtn = document.querySelector('{platform.send_selector}');
                     if (sendBtn) {{
                         sendBtn.click();
                     }} else {{
                         // Fallback: simulate Enter key
                         input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                     }}
                }}, 100);

            }} else {{
                console.error("UDAC: Input field not found for selector: {platform.input_selector}");
            }}
        }})();
        """
