"""
UDAC Portal - Kivy Version
==========================
Entry point for Kivy/Buildozer build.
"""

# Install crash logging first
from udac_portal import crashlog as _udac_crashlog
_UDAC_CRASH_LOG_PATH = _udac_crashlog.install()

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.core.window import Window
from kivy.clock import Clock

# Import our logic modules (unchanged from Toga version)
from udac_portal.platform_registry import REGISTRY, AiWebPlatform
from udac_portal.continuity_engine import ENGINE
from udac_portal.interaction_logger import LOGGER
from udac_portal.session_manager import SESSION
from udac_portal.entitlement_engine import ENTITLEMENTS
from udac_portal.script_builder import PortalScriptBuilder
from udac_portal.ivm_resilience import ivm_resilient, ivm_safe_call, RESILIENCE

print(f"[UDAC] Crash log location: {_UDAC_CRASH_LOG_PATH}")
print("[UDAC] 🚀 Starting UDAC Portal (Kivy version)...")


class HomeScreen(Screen):
    """Home screen with platform selection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        """Build the home screen UI."""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header
        header = Label(
            text='🧠 UDAC Portal',
            size_hint=(1, 0.1),
            font_size='24sp',
            bold=True
        )
        layout.add_widget(header)

        # Tagline
        tagline = Label(
            text='AI Browser with Continuity',
            size_hint=(1, 0.05),
            font_size='12sp'
        )
        layout.add_widget(tagline)

        # Premium indicator
        tier_text = "PREMIUM" if ENTITLEMENTS.is_premium() else "FREE"
        self.premium_label = Label(
            text=f'Tier: {tier_text}',
            size_hint=(1, 0.05),
            font_size='14sp'
        )
        layout.add_widget(self.premium_label)

        # Toggle premium button
        toggle_btn = Button(
            text='⭐ Toggle Premium (local)',
            size_hint=(1, 0.08),
            on_press=self.toggle_tier
        )
        layout.add_widget(toggle_btn)

        # Continuity indicator
        cont_status = "ON" if ENGINE.settings.continuity_enabled else "OFF"
        self.continuity_label = Label(
            text=f'Continuity: {cont_status} | Strength: {ENGINE.settings.injection_strength}/10',
            size_hint=(1, 0.05),
            font_size='12sp'
        )
        layout.add_widget(self.continuity_label)

        # Settings button
        settings_btn = Button(
            text='⚙️ Settings',
            size_hint=(1, 0.08),
            on_press=self.go_to_settings
        )
        layout.add_widget(settings_btn)

        # Platform grid
        platforms_label = Label(
            text='Select AI Platform',
            size_hint=(1, 0.05),
            font_size='14sp',
            bold=True
        )
        layout.add_widget(platforms_label)

        # Platform buttons (scrollable)
        scroll = ScrollView(size_hint=(1, 0.54))
        platform_grid = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
        platform_grid.bind(minimum_height=platform_grid.setter('height'))

        platforms = REGISTRY.get_all_platforms()
        for platform in platforms:
            btn = Button(
                text=f'{platform.icon}\n{platform.name}',
                size_hint=(None, None),
                size=(150, 120),
                disabled=not platform.enabled,
                on_press=lambda x, p=platform: self.open_platform(p)
            )
            platform_grid.add_widget(btn)

        scroll.add_widget(platform_grid)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def toggle_tier(self, instance):
        """Toggle between FREE and PREMIUM."""
        ENTITLEMENTS.set_tier("PREMIUM" if not ENTITLEMENTS.is_premium() else "FREE")
        ENGINE.update_settings(
            injection_strength=min(ENGINE.settings.injection_strength, 10 if ENTITLEMENTS.is_premium() else 5),
            cross_platform_insights=ENGINE.settings.cross_platform_insights and ENTITLEMENTS.is_premium(),
            platform_isolation_mode=ENGINE.settings.platform_isolation_mode and ENTITLEMENTS.is_premium(),
            max_context_tokens=min(ENGINE.settings.max_context_tokens, 3000 if ENTITLEMENTS.is_premium() else 1200)
        )
        tier_text = "PREMIUM" if ENTITLEMENTS.is_premium() else "FREE"
        self.premium_label.text = f'Tier: {tier_text}'

    def go_to_settings(self, instance):
        """Navigate to settings screen."""
        self.manager.current = 'settings'

    def open_platform(self, platform):
        """Open a platform in the portal."""
        print(f"[UDAC] Opening platform: {platform.name}")
        portal_screen = self.manager.get_screen('portal')
        portal_screen.load_platform(platform)
        self.manager.current = 'portal'


class PortalScreen(Screen):
    """Portal screen with WebView and input."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_platform = None
        self.webview = None
        self.build_ui()

    def build_ui(self):
        """Build the portal screen UI."""
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5)

        # Top bar with back button and platform name
        top_bar = BoxLayout(size_hint=(1, 0.08), spacing=10)

        back_btn = Button(
            text='← Home',
            size_hint=(0.3, 1),
            on_press=self.go_home
        )
        top_bar.add_widget(back_btn)

        self.platform_label = Label(
            text='Select a platform',
            size_hint=(0.7, 1),
            font_size='16sp',
            bold=True
        )
        top_bar.add_widget(self.platform_label)

        layout.add_widget(top_bar)

        # WebView placeholder
        self.webview_container = BoxLayout(size_hint=(1, 0.77))
        self.webview_placeholder = Label(
            text='WebView will load here\n(Android WebView integration)',
            font_size='14sp'
        )
        self.webview_container.add_widget(self.webview_placeholder)
        layout.add_widget(self.webview_container)

        # Context indicator
        self.context_label = Label(
            text='Continuity: Ready',
            size_hint=(1, 0.04),
            font_size='10sp'
        )
        layout.add_widget(self.context_label)

        # Input bar
        input_bar = BoxLayout(size_hint=(1, 0.11), spacing=5)

        self.input_field = TextInput(
            hint_text='Type your message...',
            multiline=False,
            size_hint=(0.8, 1)
        )
        self.input_field.bind(on_text_validate=self.send_message)
        input_bar.add_widget(self.input_field)

        send_btn = Button(
            text='Send',
            size_hint=(0.2, 1),
            on_press=self.send_message
        )
        input_bar.add_widget(send_btn)

        layout.add_widget(input_bar)

        self.add_widget(layout)

    def load_platform(self, platform):
        """Load a platform into the WebView."""
        self.current_platform = platform
        self.platform_label.text = f'{platform.icon} {platform.name}'

        # Start session
        SESSION.start_session(platform.id)

        # Load WebView (Android-specific)
        self.load_webview(platform.base_url)

    def load_webview(self, url):
        """Load URL in WebView (Android WebView)."""
        # Try to import jnius - may not be available in initial builds
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            JNIUS_AVAILABLE = True
        except ImportError:
            JNIUS_AVAILABLE = False
            print("[UDAC] Warning: jnius not available - WebView disabled")
            self.webview_placeholder.text = f'WebView not available\n\nOpening: {url}\n\nUse mobile browser to access AI platforms'
            return

        try:
            # Get Android classes
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            WebChromeClient = autoclass('android.webkit.WebChromeClient')
            LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
            LinearLayout = autoclass('android.widget.LinearLayout')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity

            # JavaScript interface for message bridge
            class UDACBridge(PythonJavaClass):
                __javainterfaces__ = ['android/webkit/JavascriptInterface']
                __javacontext__ = 'app'

                def __init__(self, portal_screen):
                    super().__init__()
                    self.portal_screen = portal_screen

                @java_method('(Ljava/lang/String;)V')
                def onPlatformUserMessageDetected(self, message):
                    """Called when user message is detected on platform."""
                    print(f"[UDAC] User message detected: {message[:100]}...")
                    # Log the message
                    if self.portal_screen.current_platform:
                        LOGGER.log_user_prompt(
                            self.portal_screen.current_platform.id,
                            message
                        )

                @java_method('(Ljava/lang/String;)V')
                def onPlatformAiMessageDetected(self, message):
                    """Called when AI message is detected on platform."""
                    print(f"[UDAC] AI message detected: {message[:100]}...")
                    # Feed to session manager for continuity learning
                    if self.portal_screen.current_platform:
                        SESSION.on_platform_ai_message(
                            self.portal_screen.current_platform.id,
                            message
                        )

            # Custom WebViewClient to inject scripts on page load
            class UDACWebViewClient(PythonJavaClass):
                __javainterfaces__ = ['android/webkit/WebViewClient']
                __javacontext__ = 'app'

                def __init__(self, portal_screen):
                    super().__init__()
                    self.portal_screen = portal_screen

                @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)V')
                def onPageFinished(self, view, url):
                    """Inject bridge script when page finishes loading."""
                    print(f"[UDAC] Page loaded: {url}")
                    if self.portal_screen.current_platform:
                        # Inject the bridge script
                        bridge_script = PortalScriptBuilder.build(
                            self.portal_screen.current_platform
                        )
                        view.evaluateJavascript(bridge_script, None)
                        print("[UDAC] Bridge script injected")

            # Create WebView on UI thread
            def create_webview(dt):
                # Create WebView
                self.webview = WebView(activity)
                settings = self.webview.getSettings()
                settings.setJavaScriptEnabled(True)
                settings.setDomStorageEnabled(True)
                settings.setDatabaseEnabled(True)
                settings.setAllowFileAccess(False)
                settings.setAllowContentAccess(True)
                settings.setMediaPlaybackRequiresUserGesture(False)

                # Set up JavaScript bridge
                self.bridge = UDACBridge(self)
                self.webview.addJavascriptInterface(self.bridge, 'UDACBridge')

                # Set custom WebViewClient
                self.webview_client = UDACWebViewClient(self)
                self.webview.setWebViewClient(self.webview_client)

                # Set WebChromeClient for better JS support
                self.webview.setWebChromeClient(WebChromeClient())

                # Get the Android layout
                layout = activity.findViewById(0x01020002)  # android.R.id.content
                if layout:
                    # Add WebView to Android layout
                    params = LayoutParams(
                        LayoutParams.MATCH_PARENT,
                        LayoutParams.MATCH_PARENT
                    )
                    layout.addView(self.webview, params)

                    # Load URL
                    self.webview.loadUrl(url)
                    print(f"[UDAC] WebView created and loading: {url}")

                    # Update placeholder
                    self.webview_placeholder.text = f'Loading {self.current_platform.name}...\n(WebView active)'
                else:
                    print("[UDAC] Could not get Android layout")
                    self.webview_placeholder.text = 'WebView initialization error'

            Clock.schedule_once(create_webview, 0.1)

        except Exception as e:
            import traceback
            print(f"[UDAC] WebView error: {e}")
            print(traceback.format_exc())
            self.webview_placeholder.text = f'WebView unavailable\nError: {e}\n\n(Use mobile browser to access AI platforms)'

    def send_message(self, instance):
        """Send message with continuity enrichment."""
        if not self.current_platform:
            return

        raw_text = self.input_field.text.strip()
        if not raw_text:
            return

        # Get enriched prompt
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

        # Update context label
        sources = ", ".join(payload.context_sources) if payload.context_sources else "local"
        self.context_label.text = f'+{payload.tokens_added} tokens | Sources: {sources}'

        # Inject into WebView via JavaScript
        if self.webview:
            try:
                injection_script = PortalScriptBuilder.build_send_prompt_script(
                    self.current_platform,
                    payload.final_prompt_text
                )
                self.webview.evaluateJavascript(injection_script, None)
                print(f"[UDAC] Message injected: +{payload.tokens_added} tokens from {sources}")
            except Exception as e:
                print(f"[UDAC] Injection error: {e}")
                # Fallback: just log
                LOGGER.log_user_prompt(self.current_platform.id, raw_text)
        else:
            print(f"[UDAC] WebView not ready, logging only: {payload.final_prompt_text[:100]}...")
            LOGGER.log_user_prompt(self.current_platform.id, raw_text)

        # Clear input
        self.input_field.text = ''

    def go_home(self, instance):
        """Return to home screen."""
        # Clean up WebView
        if self.webview:
            try:
                from jnius import autoclass
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                layout = activity.findViewById(0x01020002)
                if layout:
                    layout.removeView(self.webview)
                self.webview.destroy()
                self.webview = None
                print("[UDAC] WebView cleaned up")
            except Exception as e:
                print(f"[UDAC] WebView cleanup error: {e}")

        # End session
        if self.current_platform:
            SESSION.shutdown()

        self.current_platform = None
        self.manager.current = 'home'


class SettingsScreen(Screen):
    """Settings screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        """Build settings UI."""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(
            text='← Back',
            size_hint=(0.3, 1),
            on_press=self.go_back
        )
        header.add_widget(back_btn)

        title = Label(
            text='⚙️ Settings',
            size_hint=(0.7, 1),
            font_size='20sp',
            bold=True
        )
        header.add_widget(title)
        layout.add_widget(header)

        # Scrollable settings
        scroll = ScrollView(size_hint=(1, 0.9))
        settings_box = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=10)
        settings_box.bind(minimum_height=settings_box.setter('height'))

        # Continuity toggle
        cont_label = Label(
            text=f'Continuity: {"ON" if ENGINE.settings.continuity_enabled else "OFF"}',
            size_hint=(1, None),
            height=40,
            font_size='16sp'
        )
        settings_box.add_widget(cont_label)

        toggle_cont_btn = Button(
            text='Toggle Continuity',
            size_hint=(1, None),
            height=50,
            on_press=lambda x: self.toggle_continuity(cont_label)
        )
        settings_box.add_widget(toggle_cont_btn)

        # Injection strength slider
        strength_label = Label(
            text=f'Injection Strength: {ENGINE.settings.injection_strength}/10',
            size_hint=(1, None),
            height=40,
            font_size='16sp'
        )
        settings_box.add_widget(strength_label)

        strength_slider = Slider(
            min=0,
            max=10 if ENTITLEMENTS.is_premium() else 5,
            value=ENGINE.settings.injection_strength,
            size_hint=(1, None),
            height=50
        )
        strength_slider.bind(value=lambda instance, value: self.update_strength(value, strength_label))
        settings_box.add_widget(strength_slider)

        # Platform isolation (premium)
        iso_text = 'Platform Isolation: ' + ('ON' if ENGINE.settings.platform_isolation_mode else 'OFF')
        if not ENTITLEMENTS.is_premium():
            iso_text += ' (Premium only)'

        iso_label = Label(
            text=iso_text,
            size_hint=(1, None),
            height=40,
            font_size='16sp'
        )
        settings_box.add_widget(iso_label)

        toggle_iso_btn = Button(
            text='Toggle Platform Isolation',
            size_hint=(1, None),
            height=50,
            disabled=not ENTITLEMENTS.is_premium(),
            on_press=lambda x: self.toggle_isolation(iso_label)
        )
        settings_box.add_widget(toggle_iso_btn)

        # Clear data button
        clear_btn = Button(
            text='🗑️ Clear All Data',
            size_hint=(1, None),
            height=50,
            background_color=(0.9, 0.3, 0.3, 1),
            on_press=self.clear_data
        )
        settings_box.add_widget(clear_btn)

        # Stats
        stats = ENGINE.get_stats()
        stats_text = f"""
Stats:
• Continuity: {"Enabled" if stats['enabled'] else "Disabled"}
• Injection Strength: {stats['injection_strength']}/10
• Cross-platform memories: {stats['cross_platform_memories']}
• Platform isolation: {"Yes" if stats['platform_isolation'] else "No"}
        """
        stats_label = Label(
            text=stats_text.strip(),
            size_hint=(1, None),
            height=150,
            font_size='12sp'
        )
        settings_box.add_widget(stats_label)

        scroll.add_widget(settings_box)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def go_back(self, instance):
        """Go back to home."""
        self.manager.current = 'home'

    def toggle_continuity(self, label):
        """Toggle continuity on/off."""
        new_value = not ENGINE.settings.continuity_enabled
        ENGINE.update_settings(continuity_enabled=new_value)
        label.text = f'Continuity: {"ON" if new_value else "OFF"}'

    def update_strength(self, value, label):
        """Update injection strength."""
        strength = int(value)
        ENGINE.update_settings(injection_strength=strength)
        label.text = f'Injection Strength: {strength}/10'

    def toggle_isolation(self, label):
        """Toggle platform isolation."""
        if ENTITLEMENTS.is_premium():
            new_value = not ENGINE.settings.platform_isolation_mode
            ENGINE.update_settings(platform_isolation_mode=new_value)
            label.text = f'Platform Isolation: {"ON" if new_value else "OFF"}'

    def clear_data(self, instance):
        """Clear all continuity data."""
        ENGINE.clear_all_data()
        print("[UDAC] All data cleared!")


class UDACPortalApp(App):
    """Main Kivy app."""

    def build(self):
        """Build the app."""
        print("[UDAC] Building Kivy UI...")

        # Create screen manager
        sm = ScreenManager()

        # Add screens
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(PortalScreen(name='portal'))
        sm.add_widget(SettingsScreen(name='settings'))

        print("[UDAC] ✅ UI built successfully!")
        return sm

    def on_stop(self):
        """Cleanup on exit."""
        SESSION.shutdown()


if __name__ == '__main__':
    UDACPortalApp().run()
