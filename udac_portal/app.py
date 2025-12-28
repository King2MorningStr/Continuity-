"""
UDAC Portal - Main Application
==============================
A browser with a brain for AI platforms.
"""


# Install global crash logging (Android-friendly)
from . import crashlog as _udac_crashlog
_UDAC_CRASH_LOG_PATH = _udac_crashlog.install()
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, LEFT, RIGHT
# WebView is accessed via toga.WebView (backend implementation)
import asyncio
import threading

from udac_portal.platform_registry import REGISTRY, AiWebPlatform
from udac_portal.continuity_engine import ENGINE
from udac_portal.interaction_logger import LOGGER
from udac_portal.session_manager import SESSION
from udac_portal.entitlement_engine import ENTITLEMENTS
from udac_portal.script_builder import PortalScriptBuilder
from udac_portal.ivm_resilience import ivm_resilient, ivm_safe_call, IVMAsyncBridge, RESILIENCE


class UDACPortalApp(toga.App):
    """
    UDAC Portal - Universal AI Continuity Browser

    A WebView-based browser that wraps AI platforms and provides:
    - Cross-platform continuity
    - Message interception and enrichment
    - Data logging and trading
    """

    # Design System - Professional Color Palette
    COLORS = {
        # Backgrounds
        'bg_primary': '#0a0a1e',           # Deep space blue
        'bg_secondary': '#151428',         # Elevated surface
        'bg_tertiary': '#1e1c3a',          # Card background
        'bg_accent': '#252347',            # Hover/active states

        # Accents & Branding
        'accent_primary': '#6366f1',       # Indigo - primary brand
        'accent_secondary': '#8b5cf6',     # Purple - secondary
        'accent_success': '#10b981',       # Green - success states
        'accent_warning': '#f59e0b',       # Amber - warnings/premium
        'accent_error': '#ef4444',         # Red - errors

        # Text
        'text_primary': '#f3f4f6',         # High emphasis text
        'text_secondary': '#9ca3af',       # Medium emphasis
        'text_tertiary': '#6b7280',        # Low emphasis
        'text_disabled': '#4b5563',        # Disabled states

        # Special
        'gradient_start': '#1e1c3a',       # Card gradient start
        'gradient_end': '#2d2a54',         # Card gradient end
        'border_subtle': '#2d2a54',        # Subtle borders
        'shadow': '#000000',               # Shadows (not used in Toga but for reference)
    }

    def startup(self):
        """Initialize the application."""
        print("[UDAC] 🚀 Starting app initialization...")
        print(f"[UDAC] Crash log location: {_UDAC_CRASH_LOG_PATH}")

        print("[UDAC] Creating main window...")
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.on_exit = self.cleanup

        # State
        self.current_platform = None
        self.webview = None

        print("[UDAC] Building home screen...")
        # Build UI
        self.create_home_screen()

        print("[UDAC] Setting window content...")
        # Start with home
        self.main_window.content = self.home_box

        print("[UDAC] Showing window...")
        self.main_window.show()

        print("[UDAC] ✅ App started successfully!")
    
    def cleanup(self, app):
        """Cleanup on exit."""
        SESSION.shutdown()
        return True
    
    # ========================================================================
    # HOME SCREEN
    # ========================================================================
    
    def create_home_screen(self):
        """Create the home/platform selection screen."""
        self.home_box = toga.Box(style=Pack(
            direction=COLUMN,
            padding=20,
            background_color=self.COLORS['bg_primary']
        ))

        # Header Section - Enhanced with better spacing
        header_box = toga.Box(style=Pack(
            direction=ROW,
            padding_bottom=8,
            alignment=CENTER
        ))
        title = toga.Label(
            '🧠 UDAC Portal',
            style=Pack(
                font_size=28,
                font_weight='bold',
                color=self.COLORS['accent_primary'],
                flex=1
            )
        )
        settings_btn = toga.Button(
            '⚙️',
            on_press=self.go_to_settings,
            style=Pack(width=50, height=50)
        )
        header_box.add(title)
        header_box.add(settings_btn)
        self.home_box.add(header_box)

        # Tagline - More elegant
        tagline = toga.Label(
            'The AI Browser with Memory',
            style=Pack(
                padding_bottom=24,
                font_size=13,
                color=self.COLORS['text_secondary']
            )
        )
        self.home_box.add(tagline)

        # Status Bar - Premium & Continuity in elegant card
        status_card = toga.Box(style=Pack(
            direction=COLUMN,
            padding=16,
            background_color=self.COLORS['bg_secondary'],
            margin_bottom=20
        ))

        # Premium indicator with refined styling
        is_premium = ENTITLEMENTS.is_premium()
        premium_row = toga.Box(style=Pack(direction=ROW, padding_bottom=8))
        premium_icon = toga.Label(
            '⭐' if is_premium else '○',
            style=Pack(padding_right=8, font_size=16)
        )
        self.premium_indicator = toga.Label(
            f'{"PREMIUM" if is_premium else "FREE"} Tier',
            style=Pack(
                flex=1,
                font_size=14,
                font_weight='bold',
                color=self.COLORS['accent_warning'] if is_premium else self.COLORS['text_tertiary']
            )
        )
        premium_row.add(premium_icon)
        premium_row.add(self.premium_indicator)
        status_card.add(premium_row)

        # Continuity status with better visual design
        cont_row = toga.Box(style=Pack(direction=ROW, padding_bottom=12))
        cont_icon = toga.Label(
            '●' if ENGINE.settings.continuity_enabled else '○',
            style=Pack(padding_right=8, font_size=16,
                      color=self.COLORS['accent_success'] if ENGINE.settings.continuity_enabled else self.COLORS['text_disabled'])
        )
        self.continuity_indicator = toga.Label(
            f'Continuity {"Enabled" if ENGINE.settings.continuity_enabled else "Disabled"} • Strength {ENGINE.settings.injection_strength}/10',
            style=Pack(
                flex=1,
                font_size=13,
                color=self.COLORS['text_secondary']
            )
        )
        cont_row.add(cont_icon)
        cont_row.add(self.continuity_indicator)
        status_card.add(cont_row)

        def toggle_tier(widget):
            # Local-only tier toggle (future: replace with provider verification)
            ENTITLEMENTS.set_tier("PREMIUM" if not ENTITLEMENTS.is_premium() else "FREE")
            # Clamp engine settings immediately
            ENGINE.update_settings(
                injection_strength=min(ENGINE.settings.injection_strength, 10 if ENTITLEMENTS.is_premium() else 5),
                cross_platform_insights=ENGINE.settings.cross_platform_insights and ENTITLEMENTS.is_premium(),
                platform_isolation_mode=ENGINE.settings.platform_isolation_mode and ENTITLEMENTS.is_premium(),
                max_context_tokens=min(ENGINE.settings.max_context_tokens, 3000 if ENTITLEMENTS.is_premium() else 1200)
            )
            is_prem = ENTITLEMENTS.is_premium()
            self.premium_indicator.text = f'{"PREMIUM" if is_prem else "FREE"} Tier'
            self.premium_indicator.style.color = self.COLORS['accent_warning'] if is_prem else self.COLORS['text_tertiary']

        # Upgrade button with better styling
        self.upgrade_btn = toga.Button(
            '⭐ Toggle Premium (Local Demo)',
            on_press=toggle_tier,
            style=Pack(padding=10, font_size=12)
        )
        status_card.add(self.upgrade_btn)
        self.home_box.add(status_card)

        # Platform Selection Section
        platforms_header = toga.Label(
            'AI Platforms',
            style=Pack(
                font_weight='bold',
                font_size=16,
                color=self.COLORS['text_primary'],
                padding_bottom=12,
                padding_top=4
            )
        )
        self.home_box.add(platforms_header)

        # Platform grid with better spacing
        platforms = REGISTRY.get_all_platforms()
        for i in range(0, len(platforms), 2):
            row = toga.Box(style=Pack(direction=ROW, padding_bottom=12))
            for j in range(2):
                if i + j < len(platforms):
                    platform = platforms[i + j]
                    card = self.create_platform_card(platform)
                    row.add(card)
                else:
                    # Add spacer for even layout
                    spacer = toga.Box(style=Pack(flex=1, padding=5))
                    row.add(spacer)
            self.home_box.add(row)

        # Stats footer with refined styling
        self.stats_label = toga.Label(
            'Active Sessions: 0  •  Total Messages: 0',
            style=Pack(
                padding_top=24,
                color=self.COLORS['text_tertiary'],
                font_size=11
            )
        )
        self.home_box.add(self.stats_label)

        # Start stats refresh
        self.add_background_task(self.refresh_home_stats)

    def create_platform_card(self, platform: AiWebPlatform) -> toga.Box:
        """Create a polished, production-ready platform card."""
        # Card container with refined styling
        card = toga.Box(style=Pack(
            direction=COLUMN,
            padding=18,
            background_color=self.COLORS['bg_tertiary'] if platform.enabled else self.COLORS['bg_secondary'],
            flex=1,
            alignment=CENTER,
            margin_right=6 if platform.id != 'copilot' else 0  # Better spacing
        ))

        # Platform icon - larger and more prominent
        icon = toga.Label(
            platform.icon,
            style=Pack(font_size=42, padding_bottom=10)
        )
        card.add(icon)

        # Platform name with better typography
        name = toga.Label(
            platform.name,
            style=Pack(
                font_weight='bold',
                font_size=15,
                color=self.COLORS['text_primary'] if platform.enabled else self.COLORS['text_disabled'],
                padding_bottom=6
            )
        )
        card.add(name)

        # Status indicator with refined design
        status_row = toga.Box(style=Pack(
            direction=ROW,
            padding_bottom=12,
            alignment=CENTER
        ))
        status_icon = toga.Label(
            '●' if platform.enabled else '○',
            style=Pack(
                font_size=10,
                padding_right=4,
                color=self.COLORS['accent_success'] if platform.enabled else self.COLORS['text_disabled']
            )
        )
        status_text = toga.Label(
            'Ready' if platform.enabled else 'Disabled',
            style=Pack(
                font_size=11,
                color=self.COLORS['text_secondary'] if platform.enabled else self.COLORS['text_disabled']
            )
        )
        status_row.add(status_icon)
        status_row.add(status_text)
        card.add(status_row)

        # Action button with enhanced styling
        def open_platform(widget, p=platform):
            if p.enabled:
                self.open_portal_session(p)

        btn = toga.Button(
            'Launch',
            on_press=open_platform,
            enabled=platform.enabled,
            style=Pack(
                padding_top=8,
                padding_bottom=8,
                padding_left=24,
                padding_right=24,
                font_size=13
            )
        )
        card.add(btn)

        return card
    
    async def refresh_home_stats(self, app):
        """Refresh home screen stats with polished formatting."""
        while True:
            if hasattr(self, 'stats_label') and self.main_window.content == self.home_box:
                stats = SESSION.get_session_stats()
                logger_stats = LOGGER.get_stats()
                self.stats_label.text = f'Active Sessions: {stats["active_sessions"]}  •  Total Messages: {logger_stats["total_events"]}'

                # Update premium and continuity indicators
                if hasattr(self, 'premium_indicator'):
                    is_prem = ENTITLEMENTS.is_premium()
                    self.premium_indicator.text = f'{"PREMIUM" if is_prem else "FREE"} Tier'
                    self.premium_indicator.style.color = self.COLORS['accent_warning'] if is_prem else self.COLORS['text_tertiary']

                if hasattr(self, 'continuity_indicator'):
                    self.continuity_indicator.text = f'Continuity {"Enabled" if ENGINE.settings.continuity_enabled else "Disabled"} • Strength {ENGINE.settings.injection_strength}/10'

            await asyncio.sleep(2)
    
    # ========================================================================
    # PORTAL SESSION SCREEN (WebView + UDAC Input)
    # ========================================================================
    
    def open_portal_session(self, platform: AiWebPlatform):
        """Open the portal session screen for a platform."""
        self.current_platform = platform
        self.create_portal_session_screen(platform)
        self.main_window.content = self.portal_box
    
    def create_portal_session_screen(self, platform: AiWebPlatform):
        """Create a polished portal session screen with WebView."""
        self.portal_box = toga.Box(style=Pack(
            direction=COLUMN,
            background_color=self.COLORS['bg_primary'],
            flex=1
        ))

        # Enhanced top navigation bar
        top_bar = toga.Box(style=Pack(
            direction=ROW,
            padding=12,
            background_color=self.COLORS['bg_secondary'],
            alignment=CENTER
        ))

        # Back button with better sizing
        back_btn = toga.Button(
            '←',
            on_press=self.go_home,
            style=Pack(width=44, height=44)
        )
        top_bar.add(back_btn)

        # Platform identity with refined typography
        platform_label = toga.Label(
            f'{platform.icon}  {platform.name}',
            style=Pack(
                font_weight='bold',
                font_size=16,
                color=self.COLORS['text_primary'],
                flex=1,
                padding_left=12
            )
        )
        top_bar.add(platform_label)

        # Continuity status badge with better design
        cont_enabled = ENGINE.settings.continuity_enabled
        self.continuity_badge = toga.Label(
            f'{"●" if cont_enabled else "○"} Continuity',
            style=Pack(
                font_size=12,
                color=self.COLORS['accent_success'] if cont_enabled else self.COLORS['text_disabled'],
                padding_right=12
            )
        )
        top_bar.add(self.continuity_badge)

        # Log button with consistent sizing
        log_btn = toga.Button(
            '📋',
            on_press=self.show_session_log,
            style=Pack(width=44, height=44)
        )
        top_bar.add(log_btn)

        self.portal_box.add(top_bar)
        
        # WebView - THE MAIN PORTAL
        # NOTE: on_webview_load is NOT supported on Android, so we use delayed injection
        self.webview = toga.WebView(
            url=platform.base_url,
            style=Pack(flex=1)
        )
        self.portal_box.add(self.webview)

        # Inject JavaScript after a delay (Android workaround)
        self.add_background_task(self.delayed_webview_setup)
        
        # Polished UDAC Input Bar
        input_bar = toga.Box(style=Pack(
            direction=ROW,
            padding=12,
            background_color=self.COLORS['bg_secondary'],
            alignment=CENTER
        ))

        # Input field with enhanced styling
        self.input_field = toga.TextInput(
            placeholder='Enhance with continuity context...',
            style=Pack(
                flex=1,
                padding_right=8,
                padding_top=8,
                padding_bottom=8,
                font_size=14
            )
        )
        input_bar.add(self.input_field)

        # Voice input button
        mic_btn = toga.Button(
            '🎤',
            on_press=self.on_mic_press,
            style=Pack(width=48, height=48, padding_right=6)
        )
        input_bar.add(mic_btn)

        # Send button with better prominence
        send_btn = toga.Button(
            'Send',
            on_press=self.on_send_press,
            style=Pack(
                width=70,
                height=48,
                font_size=14,
                font_weight='bold'
            )
        )
        input_bar.add(send_btn)

        self.portal_box.add(input_bar)

        # Refined context information bar
        self.context_bar = toga.Label(
            'Ready  •  +0 tokens',
            style=Pack(
                padding=8,
                background_color=self.COLORS['bg_accent'],
                color=self.COLORS['text_tertiary'],
                font_size=11,
                alignment=CENTER
            )
        )
        self.portal_box.add(self.context_bar)
        
        # Start session
        SESSION.start_session(platform.id)
    
    async def delayed_webview_setup(self, app):
        """
        Android-compatible delayed JavaScript injection.

        Since on_webview_load is not supported on Android, we inject JavaScript
        after a delay to give the page time to load.
        """
        # Wait for page to load (increased delay for reliability)
        await asyncio.sleep(2.0)

        if not (self.current_platform and self.webview):
            return

        @ivm_resilient(component="webview_injection", silent=False, use_circuit_breaker=True)
        def safe_inject():
            """IVM-protected script injection."""
            try:
                script = PortalScriptBuilder.build(self.current_platform)
                self.webview.evaluate_javascript(script)
                print(f"[UDAC] ✓ Injected scripts for {self.current_platform.name}")
            except Exception as e:
                print(f"[UDAC] Warning: JavaScript injection failed (expected on some platforms): {e}")

        safe_inject()
    
    @ivm_resilient(component="send_press_handler", silent=False, use_circuit_breaker=True)
    def on_send_press(self, widget):
        """User pressed send button."""
        if not self.current_platform or not self.webview:
            return

        raw_text = self.input_field.value.strip()
        if not raw_text:
            return

        try:
            # Get enriched prompt from session manager (with IVM protection)
            payload = ivm_safe_call(
                SESSION.on_user_submit_from_udac,
                self.current_platform.id,
                raw_text,
                fallback=type('Payload', (), {
                    'final_prompt_text': raw_text,
                    'tokens_added': 0,
                    'context_sources': []
                })(),
                component="session_manager"
            )

            # Update context bar with refined formatting
            if payload:
                sources = ", ".join(payload.context_sources) if payload.context_sources else "local"
                self.context_bar.text = f'Sent  •  +{payload.tokens_added} tokens  •  {sources}'

            # Inject into WebView with protection
            inject_script = PortalScriptBuilder.build_send_prompt_script(
                self.current_platform,
                payload.final_prompt_text
            )

            # Safe JavaScript evaluation
            try:
                self.webview.evaluate_javascript(inject_script)
            except Exception as e:
                print(f"[UDAC] Warning: JavaScript injection failed: {e}")
                # Still clear input even if injection fails

            # Clear input
            self.input_field.value = ''

        except Exception as e:
            print(f"[UDAC] Error in send_press: {e}")
            # Always try to clear input
            try:
                self.input_field.value = ''
            except:
                pass
    
    def on_mic_press(self, widget):
        """User pressed mic button - placeholder for speech recognition."""
        # In a full implementation, this would:
        # 1. Start Android SpeechRecognizer
        # 2. Transcribe speech to text
        # 3. Put result in input_field
        # 4. User can then review and send
        self.main_window.info_dialog(
            'Voice Input',
            'Voice input coming soon! For now, use the platform\'s built-in voice features.'
        )
    
    def show_session_log(self, widget):
        """Show session log dialog."""
        if self.current_platform:
            stats = SESSION.get_continuity_info(self.current_platform.id)
            summary = LOGGER.get_session_summary()
            
            info = f"""
Session: {self.current_platform.name}
Messages: {stats['session_messages']}
Continuity: {'Enabled' if stats['enabled'] else 'Disabled'}
Strength: {stats['injection_strength']}/10
Cross-platform memories: {stats['cross_platform_memories']}

This Session:
Duration: {summary['session_duration_minutes']} min
User inputs: {summary['user_inputs']}
AI responses: {summary['ai_responses']}
Live transcripts: {summary['live_transcripts']}
            """
            self.main_window.info_dialog('Session Info', info.strip())
    
    def go_home(self, widget):
        """Return to home screen."""
        self.current_platform = None
        self.webview = None
        self.main_window.content = self.home_box
    
    # ========================================================================
    # SETTINGS SCREEN
    # ========================================================================
    
    def go_to_settings(self, widget):
        """Open settings screen."""
        self.create_settings_screen()
        self.main_window.content = self.settings_box
    
    def create_settings_screen(self):
        """Create a polished settings screen."""
        self.settings_box = toga.Box(style=Pack(
            direction=COLUMN,
            padding=20,
            background_color=self.COLORS['bg_primary']
        ))

        # Enhanced header
        header = toga.Box(style=Pack(
            direction=ROW,
            padding_bottom=24,
            alignment=CENTER
        ))
        back_btn = toga.Button(
            '← Back',
            on_press=self.settings_go_home,
            style=Pack(height=44, padding_right=12)
        )
        title = toga.Label(
            '⚙️  Settings',
            style=Pack(
                font_size=24,
                font_weight='bold',
                color=self.COLORS['accent_primary'],
                flex=1
            )
        )
        header.add(back_btn)
        header.add(title)
        self.settings_box.add(header)
        
        # Continuity Engine Section - Enhanced
        continuity_section = toga.Box(style=Pack(
            direction=COLUMN,
            padding=16,
            background_color=self.COLORS['bg_secondary'],
            margin_bottom=16
        ))

        # Section header
        cont_label = toga.Label(
            'Continuity Engine',
            style=Pack(
                font_weight='bold',
                font_size=16,
                color=self.COLORS['text_primary'],
                padding_bottom=12
            )
        )
        continuity_section.add(cont_label)

        # Toggle switch
        self.continuity_switch = toga.Switch(
            'Enable cross-conversation memory',
            value=ENGINE.settings.continuity_enabled,
            on_change=self.on_continuity_toggle,
            style=Pack(padding_bottom=16)
        )
        continuity_section.add(self.continuity_switch)

        # Strength control with better design
        strength_label = toga.Label(
            f'Context Injection Strength',
            style=Pack(
                color=self.COLORS['text_secondary'],
                font_size=13,
                padding_bottom=8
            )
        )
        continuity_section.add(strength_label)

        # Strength adjustment row
        strength_row = toga.Box(style=Pack(
            direction=ROW,
            padding_top=4,
            alignment=CENTER
        ))
        dec_btn = toga.Button(
            '−',
            on_press=self.decrease_strength,
            style=Pack(width=48, height=48, font_size=18)
        )
        self.strength_display = toga.Label(
            str(ENGINE.settings.injection_strength),
            style=Pack(
                padding_left=24,
                padding_right=24,
                font_size=22,
                font_weight='bold',
                color=self.COLORS['accent_primary']
            )
        )
        inc_btn = toga.Button(
            '+',
            on_press=self.increase_strength,
            style=Pack(width=48, height=48, font_size=18)
        )
        strength_info = toga.Label(
            '/10',
            style=Pack(
                font_size=16,
                color=self.COLORS['text_tertiary'],
                padding_left=4
            )
        )
        strength_row.add(dec_btn)
        strength_row.add(self.strength_display)
        strength_row.add(strength_info)
        strength_row.add(inc_btn)
        continuity_section.add(strength_row)

        self.settings_box.add(continuity_section)
        
        # Platform Isolation Section - Enhanced
        isolation_section = toga.Box(style=Pack(
            direction=COLUMN,
            padding=16,
            background_color=self.COLORS['bg_secondary'],
            margin_bottom=16
        ))

        iso_header = toga.Box(style=Pack(direction=ROW, padding_bottom=8))
        iso_label = toga.Label(
            'Continuity Mode',
            style=Pack(
                font_weight='bold',
                font_size=16,
                color=self.COLORS['text_primary'],
                flex=1
            )
        )
        premium_badge = toga.Label(
            '⭐ PREMIUM',
            style=Pack(
                font_size=11,
                font_weight='bold',
                color=self.COLORS['accent_warning']
            )
        )
        iso_header.add(iso_label)
        iso_header.add(premium_badge)
        isolation_section.add(iso_header)

        self.isolation_switch = toga.Switch(
            'Platform Isolation Mode',
            value=ENGINE.settings.platform_isolation_mode,
            on_change=self.on_isolation_toggle,
            style=Pack(padding_bottom=8)
        )
        isolation_section.add(self.isolation_switch)

        iso_desc = toga.Label(
            'Keep each AI platform\'s memory separate',
            style=Pack(
                font_size=12,
                color=self.COLORS['text_tertiary']
            )
        )
        isolation_section.add(iso_desc)

        self.settings_box.add(isolation_section)
        
        # Data Trading Section - Enhanced
        trading_section = toga.Box(style=Pack(
            direction=COLUMN,
            padding=16,
            background_color=self.COLORS['bg_secondary'],
            margin_bottom=16
        ))

        trade_header = toga.Box(style=Pack(direction=ROW, padding_bottom=8))
        trade_label = toga.Label(
            '💎  Data Trading',
            style=Pack(
                font_weight='bold',
                font_size=16,
                color=self.COLORS['text_primary'],
                flex=1
            )
        )
        trade_premium = toga.Label(
            '⭐ PREMIUM',
            style=Pack(
                font_size=11,
                font_weight='bold',
                color=self.COLORS['accent_warning']
            )
        )
        trade_header.add(trade_label)
        trade_header.add(trade_premium)
        trading_section.add(trade_header)

        self.trading_switch = toga.Switch(
            'Enable Pattern Export',
            value=LOGGER.trading_settings.trading_enabled,
            on_change=self.on_trading_toggle,
            style=Pack(padding_bottom=12)
        )
        trading_section.add(self.trading_switch)

        credits_label = toga.Label(
            f'Credits Available: {LOGGER.storage_credits}',
            style=Pack(
                color=self.COLORS['accent_success'],
                font_size=14,
                font_weight='bold',
                padding_bottom=10
            )
        )
        trading_section.add(credits_label)

        trade_btn = toga.Button(
            'Export Patterns  (+500)',
            on_press=self.execute_trade,
            style=Pack(
                padding_top=10,
                padding_bottom=10,
                font_size=13
            )
        )
        trading_section.add(trade_btn)

        self.settings_box.add(trading_section)

        # Platform Management Section - Enhanced
        platforms_section = toga.Box(style=Pack(
            direction=COLUMN,
            padding=16,
            background_color=self.COLORS['bg_secondary'],
            margin_bottom=16
        ))

        plat_label = toga.Label(
            'Platform Availability',
            style=Pack(
                font_weight='bold',
                font_size=16,
                color=self.COLORS['text_primary'],
                padding_bottom=12
            )
        )
        platforms_section.add(plat_label)

        for platform in REGISTRY.get_all_platforms():
            row = toga.Box(style=Pack(
                direction=ROW,
                padding_bottom=8
            ))

            def toggle_platform(widget, p=platform):
                REGISTRY.toggle_platform(p.id, widget.value)

            switch = toga.Switch(
                f'{platform.icon}  {platform.name}',
                value=platform.enabled,
                on_change=toggle_platform,
                style=Pack(font_size=14)
            )
            row.add(switch)
            platforms_section.add(row)

        self.settings_box.add(platforms_section)

        # Danger Zone - Clear Data
        clear_section = toga.Box(style=Pack(
            direction=COLUMN,
            padding=16,
            background_color=self.COLORS['bg_secondary'],
            margin_top=8
        ))

        danger_label = toga.Label(
            '⚠️  Danger Zone',
            style=Pack(
                font_weight='bold',
                font_size=16,
                color=self.COLORS['accent_error'],
                padding_bottom=8
            )
        )
        clear_section.add(danger_label)

        danger_desc = toga.Label(
            'Permanently delete all continuity data and memories',
            style=Pack(
                font_size=12,
                color=self.COLORS['text_tertiary'],
                padding_bottom=12
            )
        )
        clear_section.add(danger_desc)

        clear_btn = toga.Button(
            '🗑️  Clear All Data',
            on_press=self.confirm_clear_data,
            style=Pack(
                padding_top=10,
                padding_bottom=10,
                font_size=13
            )
        )
        clear_section.add(clear_btn)
        self.settings_box.add(clear_section)
    
    def settings_go_home(self, widget):
        """Return to home from settings."""
        self.create_home_screen()  # Rebuild to reflect changes
        self.main_window.content = self.home_box
    
    def on_continuity_toggle(self, widget):
        """Toggle continuity on/off."""
        ENGINE.update_settings(continuity_enabled=widget.value)
    
    def on_isolation_toggle(self, widget):
        """Toggle platform isolation mode (Premium)."""
        if widget.value and not ENTITLEMENTS.is_premium():
            widget.value = False
            self.main_window.info_dialog('Premium Required', 'Platform Isolation is a Premium feature.')
            return
        ENGINE.update_settings(platform_isolation_mode=widget.value)
    
    def on_trading_toggle(self, widget):
        """Toggle data trading (Premium)."""
        if widget.value and not ENTITLEMENTS.is_premium():
            widget.value = False
            self.main_window.info_dialog('Premium Required', 'Data Trading is a Premium feature.')
            return
        LOGGER.enable_trading(widget.value)
    
    def decrease_strength(self, widget):
        """Decrease injection strength."""
        new_val = max(0, ENGINE.settings.injection_strength - 1)
        ENGINE.update_settings(injection_strength=new_val)
        self.strength_display.text = str(new_val)
    
    def increase_strength(self, widget):
        """Increase injection strength."""
        new_val = min(10, ENGINE.settings.injection_strength + 1)
        ENGINE.update_settings(injection_strength=new_val)
        self.strength_display.text = str(new_val)
    
    def execute_trade(self, widget):
        """Execute pattern trade."""
        result = LOGGER.export_patterns_for_trading(100)
        if result.get('success'):
            self.main_window.info_dialog(
                'Trade Successful! 💎',
                f'Exported {result["patterns_exported"]} patterns\n'
                f'Earned {result["credits_earned"]} credits\n'
                f'Total: {result["total_credits"]} credits'
            )
        else:
            self.main_window.info_dialog(
                'Trade Failed',
                result.get('error', 'Unknown error')
            )
    
    async def confirm_clear_data(self, widget):
        """Confirm and clear all data."""
        confirmed = await self.main_window.confirm_dialog(
            'Clear All Data?',
            'This will delete all continuity data, memories, and conversation history. This cannot be undone.'
        )
        if confirmed:
            ENGINE.clear_all_data()
            self.main_window.info_dialog('Data Cleared', 'All continuity data has been cleared.')


def main():
    return UDACPortalApp(
        'UDAC Portal',
        'com.udacportal.app',
        formal_name='UDAC Portal'
    )


if __name__ == '__main__':
    main().main_loop()
