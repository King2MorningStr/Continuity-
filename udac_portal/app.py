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
    
    def startup(self):
        """Initialize the application."""
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.on_exit = self.cleanup
        
        # State
        self.current_platform = None
        self.webview = None
        
        # Build UI
        self.create_home_screen()
        
        # Start with home
        self.main_window.content = self.home_box
        self.main_window.show()
    
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
            padding=10,
            background_color='#0f0c29'
        ))

        # Header
        header_box = toga.Box(style=Pack(direction=ROW, padding_bottom=15))
        title = toga.Label(
            '🧠 UDAC Portal',
            style=Pack(font_size=22, font_weight='bold', color='#667eea', flex=1)
        )
        settings_btn = toga.Button(
            '⚙️',
            on_press=self.go_to_settings,
            style=Pack(width=50)
        )
        header_box.add(title)
        header_box.add(settings_btn)
        self.home_box.add(header_box)

        # Tagline
        tagline = toga.Label(
            'AI Browser with Continuity',
            style=Pack(padding_bottom=20, font_size=12, color='#a0a0a0')
        )
        self.home_box.add(tagline)

        # Premium indicator (local entitlement for now)
        self.premium_indicator = toga.Label(
            f'Tier: {"PREMIUM" if ENTITLEMENTS.is_premium() else "FREE"}',
            style=Pack(padding_bottom=10, color='#f59e0b' if ENTITLEMENTS.is_premium() else '#666')
        )
        self.home_box.add(self.premium_indicator)

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
            self.premium_indicator.text = f'Tier: {"PREMIUM" if ENTITLEMENTS.is_premium() else "FREE"}'
            self.premium_indicator.style.color = '#f59e0b' if ENTITLEMENTS.is_premium() else '#666'

        self.upgrade_btn = toga.Button(
            '⭐ Toggle Premium (local)',
            on_press=toggle_tier,
            style=Pack(padding_bottom=15)
        )
        self.home_box.add(self.upgrade_btn)

        # Continuity indicator
        self.continuity_indicator = toga.Label(
            f'Continuity: {"ON" if ENGINE.settings.continuity_enabled else "OFF"} | Strength: {ENGINE.settings.injection_strength}/10',
            style=Pack(padding_bottom=15, color='#10a37f' if ENGINE.settings.continuity_enabled else '#ef4444')
        )
        self.home_box.add(self.continuity_indicator)

        # Platform grid
        platforms_label = toga.Label(
            'Select AI Platform',
            style=Pack(font_weight='bold', color='#e0e0e0', padding_bottom=10)
        )
        self.home_box.add(platforms_label)

        platforms = REGISTRY.get_all_platforms()
        for i in range(0, len(platforms), 2):
            row = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
            for j in range(2):
                if i + j < len(platforms):
                    platform = platforms[i + j]
                    card = self.create_platform_card(platform)
                    row.add(card)
            self.home_box.add(row)

        # Stats footer
        self.stats_label = toga.Label(
            'Sessions: 0 | Messages: 0',
            style=Pack(padding_top=20, color='#666', font_size=10)
        )
        self.home_box.add(self.stats_label)

        # Start stats refresh
        self.add_background_task(self.refresh_home_stats)

    def create_platform_card(self, platform: AiWebPlatform) -> toga.Box:
        """Create a clickable platform card."""
        card = toga.Box(style=Pack(
            direction=COLUMN, 
            padding=15, 
            background_color='#1f1d2e' if platform.enabled else '#151320',
            flex=1, 
            alignment=CENTER,
            margin=5
        ))
        
        icon = toga.Label(
            platform.icon, 
            style=Pack(font_size=32, padding_bottom=5)
        )
        name = toga.Label(
            platform.name, 
            style=Pack(
                font_weight='bold', 
                color='#e0e0e0' if platform.enabled else '#666',
                padding_bottom=5
            )
        )
        
        status_text = '✓ Enabled' if platform.enabled else '○ Disabled'
        status = toga.Label(
            status_text,
            style=Pack(font_size=10, color='#10a37f' if platform.enabled else '#666')
        )
        
        # Open button
        def open_platform(widget, p=platform):
            if p.enabled:
                self.open_portal_session(p)
        
        btn = toga.Button(
            'Open',
            on_press=open_platform,
            enabled=platform.enabled,
            style=Pack(padding_top=10)
        )
        
        card.add(icon)
        card.add(name)
        card.add(status)
        card.add(btn)
        
        return card
    
    async def refresh_home_stats(self, app):
        """Refresh home screen stats."""
        while True:
            if hasattr(self, 'stats_label') and self.main_window.content == self.home_box:
                stats = SESSION.get_session_stats()
                logger_stats = LOGGER.get_stats()
                self.stats_label.text = f'Sessions: {stats["active_sessions"]} | Messages: {logger_stats["total_events"]}'
                
                # Update continuity indicator
                if hasattr(self, 'premium_indicator'):
                    self.premium_indicator.text = f'Tier: {"PREMIUM" if ENTITLEMENTS.is_premium() else "FREE"}'
                    self.premium_indicator.style.color = '#f59e0b' if ENTITLEMENTS.is_premium() else '#666'
                self.continuity_indicator.text = f'Continuity: {"ON" if ENGINE.settings.continuity_enabled else "OFF"} | Strength: {ENGINE.settings.injection_strength}/10'
                self.continuity_indicator.style.color = '#10a37f' if ENGINE.settings.continuity_enabled else '#ef4444'
            
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
        """Create the portal session screen with WebView."""
        self.portal_box = toga.Box(style=Pack(
            direction=COLUMN, 
            background_color='#0f0c29',
            flex=1
        ))
        
        # Top bar
        top_bar = toga.Box(style=Pack(
            direction=ROW, 
            padding=8, 
            background_color='#1f1d2e'
        ))
        
        back_btn = toga.Button('←', on_press=self.go_home, style=Pack(width=40))
        
        platform_label = toga.Label(
            f'{platform.icon} {platform.name}',
            style=Pack(font_weight='bold', color='#e0e0e0', flex=1, padding_left=10)
        )
        
        self.continuity_badge = toga.Label(
            '● Continuity ON' if ENGINE.settings.continuity_enabled else '○ Continuity OFF',
            style=Pack(
                color='#10a37f' if ENGINE.settings.continuity_enabled else '#ef4444',
                padding_right=10
            )
        )
        
        log_btn = toga.Button('📋', on_press=self.show_session_log, style=Pack(width=40))
        
        top_bar.add(back_btn)
        top_bar.add(platform_label)
        top_bar.add(self.continuity_badge)
        top_bar.add(log_btn)
        self.portal_box.add(top_bar)
        
        # WebView - THE MAIN PORTAL
        self.webview = toga.WebView(
            url=platform.base_url,
            on_webview_load=self.on_webview_loaded,
            style=Pack(flex=1)
        )
        self.portal_box.add(self.webview)
        
        # UDAC Input Bar (Bottom)
        input_bar = toga.Box(style=Pack(
            direction=ROW, 
            padding=8, 
            background_color='#1f1d2e'
        ))
        
        self.input_field = toga.TextInput(
            placeholder='Type your prompt here...',
            style=Pack(flex=1, padding_right=5)
        )
        
        # Mic button (placeholder for speech recognition)
        mic_btn = toga.Button('🎤', on_press=self.on_mic_press, style=Pack(width=40))
        
        # Send button
        send_btn = toga.Button('Send', on_press=self.on_send_press, style=Pack(width=60))
        
        input_bar.add(self.input_field)
        input_bar.add(mic_btn)
        input_bar.add(send_btn)
        self.portal_box.add(input_bar)
        
        # Context info bar
        self.context_bar = toga.Label(
            '+0 tokens | Ready',
            style=Pack(
                padding=5, 
                background_color='#151320', 
                color='#666',
                font_size=10
            )
        )
        self.portal_box.add(self.context_bar)
        
        # Start session
        SESSION.start_session(platform.id)
    
    def on_webview_loaded(self, widget):
        """Called when WebView finishes loading a page."""
        if not (self.current_platform and self.webview):
            return

        @ivm_resilient(component="webview_injection", silent=False, use_circuit_breaker=True)
        def safe_inject():
            """IVM-protected script injection."""
            script = PortalScriptBuilder.build(self.current_platform)
            self.webview.evaluate_javascript(script)
            print(f"[UDAC] Injected scripts for {self.current_platform.name}")

        async def delayed_inject():
            await asyncio.sleep(0.5)
            safe_inject()

        # Use IVM async bridge for robust async/sync handling
        def sync_fallback():
            import time as _t
            _t.sleep(0.5)
            safe_inject()

        IVMAsyncBridge.safe_create_task(delayed_inject(), fallback_sync=sync_fallback)
    
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

            # Update context bar safely
            if payload:
                self.context_bar.text = f'+{payload.tokens_added} tokens | Sources: {", ".join(payload.context_sources) or "local"}'

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
        """Create the settings screen."""
        self.settings_box = toga.Box(style=Pack(
            direction=COLUMN, 
            padding=15, 
            background_color='#0f0c29'
        ))
        
        # Header
        header = toga.Box(style=Pack(direction=ROW, padding_bottom=20))
        back_btn = toga.Button('← Back', on_press=self.settings_go_home)
        title = toga.Label(
            '⚙️ Settings',
            style=Pack(font_size=18, font_weight='bold', color='#667eea', padding_left=10)
        )
        header.add(back_btn)
        header.add(title)
        self.settings_box.add(header)
        
        # Continuity Toggle
        continuity_section = toga.Box(style=Pack(
            direction=COLUMN, 
            padding=10, 
            background_color='#1f1d2e',
            margin_bottom=15
        ))
        
        cont_label = toga.Label(
            'Continuity Engine',
            style=Pack(font_weight='bold', color='#e0e0e0', padding_bottom=10)
        )
        continuity_section.add(cont_label)
        
        self.continuity_switch = toga.Switch(
            'Enable Continuity',
            value=ENGINE.settings.continuity_enabled,
            on_change=self.on_continuity_toggle
        )
        continuity_section.add(self.continuity_switch)
        
        # Injection strength slider info
        strength_label = toga.Label(
            f'Injection Strength: {ENGINE.settings.injection_strength}/10',
            style=Pack(color='#a0a0a0', padding_top=10)
        )
        continuity_section.add(strength_label)
        
        # Strength buttons (since Toga doesn't have slider on all platforms)
        strength_row = toga.Box(style=Pack(direction=ROW, padding_top=5))
        dec_btn = toga.Button('-', on_press=self.decrease_strength, style=Pack(width=40))
        inc_btn = toga.Button('+', on_press=self.increase_strength, style=Pack(width=40))
        self.strength_display = toga.Label(
            str(ENGINE.settings.injection_strength),
            style=Pack(padding_left=20, padding_right=20, font_size=18, color='#667eea')
        )
        strength_row.add(dec_btn)
        strength_row.add(self.strength_display)
        strength_row.add(inc_btn)
        continuity_section.add(strength_row)
        
        self.settings_box.add(continuity_section)
        
        # Platform Isolation (Premium)
        isolation_section = toga.Box(style=Pack(
            direction=COLUMN, 
            padding=10, 
            background_color='#1f1d2e',
            margin_bottom=15
        ))
        
        iso_label = toga.Label(
            'Continuity Mode',
            style=Pack(font_weight='bold', color='#e0e0e0', padding_bottom=10)
        )
        isolation_section.add(iso_label)
        
        self.isolation_switch = toga.Switch(
            'Platform Isolation (Premium)',
            value=ENGINE.settings.platform_isolation_mode,
            on_change=self.on_isolation_toggle
        )
        isolation_section.add(self.isolation_switch)
        
        iso_desc = toga.Label(
            'Each platform gets its own memory',
            style=Pack(font_size=10, color='#666', padding_top=5)
        )
        isolation_section.add(iso_desc)
        
        self.settings_box.add(isolation_section)
        
        # Data Trading Section
        trading_section = toga.Box(style=Pack(
            direction=COLUMN, 
            padding=10, 
            background_color='#1f1d2e',
            margin_bottom=15
        ))
        
        trade_label = toga.Label(
            '💎 Data Trading',
            style=Pack(font_weight='bold', color='#e0e0e0', padding_bottom=10)
        )
        trading_section.add(trade_label)
        
        self.trading_switch = toga.Switch(
            'Enable Pattern Trading',
            value=LOGGER.trading_settings.trading_enabled,
            on_change=self.on_trading_toggle
        )
        trading_section.add(self.trading_switch)
        
        credits_label = toga.Label(
            f'Storage Credits: {LOGGER.storage_credits}',
            style=Pack(color='#10a37f', padding_top=10)
        )
        trading_section.add(credits_label)
        
        trade_btn = toga.Button(
            'Export Patterns (+500 credits)',
            on_press=self.execute_trade,
            style=Pack(padding_top=10)
        )
        trading_section.add(trade_btn)
        
        self.settings_box.add(trading_section)
        
        # Platform Management
        platforms_section = toga.Box(style=Pack(
            direction=COLUMN, 
            padding=10, 
            background_color='#1f1d2e'
        ))
        
        plat_label = toga.Label(
            'Platform Toggles',
            style=Pack(font_weight='bold', color='#e0e0e0', padding_bottom=10)
        )
        platforms_section.add(plat_label)
        
        for platform in REGISTRY.get_all_platforms():
            row = toga.Box(style=Pack(direction=ROW, padding_bottom=5))
            
            def toggle_platform(widget, p=platform):
                REGISTRY.toggle_platform(p.id, widget.value)
            
            switch = toga.Switch(
                f'{platform.icon} {platform.name}',
                value=platform.enabled,
                on_change=toggle_platform
            )
            row.add(switch)
            platforms_section.add(row)
        
        self.settings_box.add(platforms_section)
        
        # Clear Data Button
        clear_section = toga.Box(style=Pack(padding_top=20))
        clear_btn = toga.Button(
            '🗑️ Clear All Continuity Data',
            on_press=self.confirm_clear_data,
            style=Pack(background_color='#ef4444')
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
