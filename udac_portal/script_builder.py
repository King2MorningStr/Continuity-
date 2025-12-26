"""
Portal Script Builder - JavaScript Generation
=============================================
Generates JavaScript code for DOM observation and message injection.

NOTE:
This module must remain Android-safe. We avoid Python f-strings in large JS
templates because unescaped braces can break parsing and crash the app.
"""

from typing import Optional
from udac_portal.platform_registry import AiWebPlatform


class PortalScriptBuilder:
    """Build JavaScript injection payloads for a specific AI web platform."""

    @staticmethod
    def build_bridge_script(platform: AiWebPlatform) -> str:
        """Return a JavaScript bridge script customized for the platform."""

        template = r"""
// UDAC Portal Bridge - __PLATFORM_NAME__
// =====================================

const CONFIG = {
    inputSelector: `__INPUT_SELECTOR__`,
    sendSelector: `__SEND_SELECTOR__`,
    userMessageSelector: `__USER_SELECTOR__`,
    aiMessageSelector: `__AI_SELECTOR__`,
    transcriptSelector: `__TRANSCRIPT_SELECTOR__`,
    liveIndicatorSelector: `__LIVE_INDICATOR_SELECTOR__`,
};

// Track seen messages to avoid duplicates
const seenMessages = new Set();

function splitSelectors(sel) {
    if (!sel) return [];
    return sel.split('||').map(s => s.trim()).filter(Boolean);
}

function queryAllWithFallback(selector) {
    const selectors = splitSelectors(selector);
    if (!selectors.length) return [];
    for (const s of selectors) {
        try {
            const els = Array.from(document.querySelectorAll(s));
            if (els && els.length) return els;
        } catch (e) {}
    }
    return [];
}

function msgHash(text) {
    // Tiny stable hash for dedupe
    let h = 0;
    for (let i = 0; i < text.length; i++) {
        h = ((h << 5) - h) + text.charCodeAt(i);
        h |= 0;
    }
    return String(h);
}

function emitUserMessage(text) {
    if (!text || text.length < 2) return;

    const hash = 'user_' + msgHash(text);
    if (seenMessages.has(hash)) return;
    seenMessages.add(hash);

    if (seenMessages.size > 500) {
        const arr = Array.from(seenMessages);
        seenMessages.clear();
        arr.slice(-250).forEach(h => seenMessages.add(h));
    }

    try {
        if (window.UDACBridge && window.UDACBridge.onPlatformUserMessageDetected) {
            window.UDACBridge.onPlatformUserMessageDetected(text);
        }
    } catch (e) {}
}

function emitAiMessage(text) {
    if (!text || text.length < 2) return;

    const hash = 'ai_' + msgHash(text);
    if (seenMessages.has(hash)) return;
    seenMessages.add(hash);

    if (seenMessages.size > 500) {
        const arr = Array.from(seenMessages);
        seenMessages.clear();
        arr.slice(-250).forEach(h => seenMessages.add(h));
    }

    try {
        if (window.UDACBridge && window.UDACBridge.onPlatformAiMessageDetected) {
            window.UDACBridge.onPlatformAiMessageDetected(text);
        }
    } catch (e) {}
}

function readText(el) {
    if (!el) return '';
    const t = (el.innerText || el.textContent || '').trim();
    return t;
}

function observeUserMessages() {
    const userEls = queryAllWithFallback(CONFIG.userMessageSelector);
    for (const el of userEls) {
        const text = readText(el);
        if (text) emitUserMessage(text);
    }
}

function observeAiMessages() {
    const aiEls = queryAllWithFallback(CONFIG.aiMessageSelector);
    for (const el of aiEls) {
        const text = readText(el);
        if (text) emitAiMessage(text);
    }
}

function scanMessages() {
    observeUserMessages();
    observeAiMessages();
}

// Observe DOM changes
const observer = new MutationObserver(() => {
    try { scanMessages(); } catch (e) {}
});

function start() {
    try {
        observer.observe(document.body, { childList: true, subtree: true });
    } catch (e) {}
    scanMessages();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
} else {
    start();
}
"""

        def esc(s: Optional[str]) -> str:
            return (s or "").replace("\\", "\\\\").replace("`", "\\`")

        replacements = {
            "__PLATFORM_NAME__": platform.name,
            "__INPUT_SELECTOR__": esc(platform.input_selector),
            "__SEND_SELECTOR__": esc(platform.send_selector or ""),
            "__USER_SELECTOR__": esc(platform.user_message_selector),
            "__AI_SELECTOR__": esc(platform.ai_message_selector),
            "__TRANSCRIPT_SELECTOR__": esc(platform.transcript_selector or ""),
            "__LIVE_INDICATOR_SELECTOR__": esc(platform.live_mode_indicator_selector or ""),
        }

        script = template
        for k, v in replacements.items():
            script = script.replace(k, v)
        return script

    @staticmethod
    def build(platform: AiWebPlatform) -> str:
        """Build the complete injection script for a platform."""
        return PortalScriptBuilder.build_bridge_script(platform)

    @staticmethod
    def build_send_prompt_script(platform: AiWebPlatform, text: str) -> str:
        """Build script to insert text into input field and send."""
        def esc(s: Optional[str]) -> str:
            return (s or "").replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

        safe_text = esc(text)
        input_sel = esc(platform.input_selector)
        send_sel = esc(platform.send_selector) if platform.send_selector else ""

        # Basic implementation: find input, set value, trigger events, click send
        script = f"""
(function() {{
    const inputEl = document.querySelector(`{input_sel}`);
    if (inputEl) {{
        inputEl.value = `{safe_text}`;
        inputEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
        inputEl.dispatchEvent(new Event('change', {{ bubbles: true }}));
        
        // Try to find textarea-autosize behavior updates if any
        
        setTimeout(() => {{
            const sendBtn = document.querySelector(`{send_sel}`);
            if (sendBtn) {{
                sendBtn.click();
            }} else {{
                // Fallback: try Enter key on input if no send button found
                inputEl.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }}));
            }}
        }}, 100);
    }}
}})();
"""
        return script
    
    @staticmethod
    def build_check_page_ready_script() -> str:
        """Build script to check if page is fully loaded."""
        return "(document.readyState === 'complete' || document.readyState === 'interactive') ? 'ready' : 'loading'"

    @staticmethod
    def build_clear_input_script(platform: AiWebPlatform) -> str:
        """Build script to clear the input field."""
        def esc(s: Optional[str]) -> str:
            return (s or "").replace("\\", "\\\\").replace("`", "\\`")
        input_sel = esc(platform.input_selector)
        return f"""
        var el = document.querySelector(`{input_sel}`);
        if(el) {{ el.value = ''; el.innerHTML = ''; }}
        """

    @staticmethod
    def build_get_input_content_script(platform: AiWebPlatform) -> str:
        """Build script to get current input content."""
        def esc(s: Optional[str]) -> str:
            return (s or "").replace("\\", "\\\\").replace("`", "\\`")
        input_sel = esc(platform.input_selector)
        return f"""
        (function(){{
            var el = document.querySelector(`{input_sel}`);
            return el ? el.value : '';
        }})();
        """
