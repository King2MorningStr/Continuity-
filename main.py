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
import json
import os
import platform
import sys
from datetime import datetime

print(f"[UDAC] Crash log location: {_UDAC_CRASH_LOG_PATH}")
print("[UDAC] 🚀 Starting UDAC Portal (Kivy version)...")

# Check if jnius is available (Android-only)
JNIUS_AVAILABLE = False
try:
    from jnius import autoclass
    JNIUS_AVAILABLE = True
    print("[UDAC] ✅ jnius available - WebView enabled")
except ImportError:
    print("[UDAC] ⚠️ jnius not available - WebView disabled")
except Exception as e:
    print(f"[UDAC] ⚠️ jnius import error: {e} - WebView disabled")


def run_diagnostics():
    """Run comprehensive diagnostics and return JSON report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": {},
        "summary": {"passed": 0, "failed": 0, "warnings": 0}
    }

    # Test 1: Python Environment
    try:
        report["test_results"]["python_environment"] = {
            "status": "PASS",
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.machine(),
        }
        report["summary"]["passed"] += 1
    except Exception as e:
        report["test_results"]["python_environment"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 2: jnius Availability
    try:
        if JNIUS_AVAILABLE:
            from jnius import autoclass
            report["test_results"]["jnius"] = {
                "status": "PASS",
                "available": True,
                "can_import": True
            }
            report["summary"]["passed"] += 1
        else:
            report["test_results"]["jnius"] = {
                "status": "WARN",
                "available": False,
                "message": "jnius not available - WebView disabled"
            }
            report["summary"]["warnings"] += 1
    except Exception as e:
        report["test_results"]["jnius"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 3: Android Classes (if jnius available)
    if JNIUS_AVAILABLE:
        try:
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity')
            webview_class = autoclass('android.webkit.WebView')
            report["test_results"]["android_classes"] = {
                "status": "PASS",
                "activity_class": "accessible",
                "webview_class": "accessible"
            }
            report["summary"]["passed"] += 1
        except Exception as e:
            report["test_results"]["android_classes"] = {
                "status": "FAIL",
                "error": str(e)
            }
            report["summary"]["failed"] += 1
    else:
        report["test_results"]["android_classes"] = {
            "status": "SKIP",
            "message": "jnius not available"
        }

    # Test 4: Platform Registry
    try:
        platforms = REGISTRY.get_all_platforms()
        platform_list = [{"name": p.name, "enabled": p.enabled, "id": p.id} for p in platforms]
        report["test_results"]["platform_registry"] = {
            "status": "PASS",
            "total_platforms": len(platforms),
            "enabled_platforms": sum(1 for p in platforms if p.enabled),
            "platforms": platform_list
        }
        report["summary"]["passed"] += 1
    except Exception as e:
        report["test_results"]["platform_registry"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 5: Session Manager
    try:
        session_active = hasattr(SESSION, 'start_session')
        report["test_results"]["session_manager"] = {
            "status": "PASS",
            "methods_available": session_active
        }
        report["summary"]["passed"] += 1
    except Exception as e:
        report["test_results"]["session_manager"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 6: Continuity Engine
    try:
        engine_status = ENGINE.get_stats()
        report["test_results"]["continuity_engine"] = {
            "status": "PASS",
            "enabled": engine_status.get("enabled", False),
            "injection_strength": engine_status.get("injection_strength", 0),
            "cross_platform_memories": engine_status.get("cross_platform_memories", 0),
            "platform_isolation": engine_status.get("platform_isolation", False)
        }
        report["summary"]["passed"] += 1
    except Exception as e:
        report["test_results"]["continuity_engine"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 7: Entitlements
    try:
        is_premium = ENTITLEMENTS.is_premium()
        report["test_results"]["entitlements"] = {
            "status": "PASS",
            "tier": "PREMIUM" if is_premium else "FREE"
        }
        report["summary"]["passed"] += 1
    except Exception as e:
        report["test_results"]["entitlements"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 8: File System Access
    try:
        # Try to get storage directory
        try:
            from platformdirs import user_data_dir
            storage_dir = user_data_dir("UDAC Portal", "Sunni")
            storage_available = True
        except ImportError:
            import tempfile
            storage_dir = os.path.join(tempfile.gettempdir(), "udac_portal")
            storage_available = False

        # Check if directory exists or can be created
        os.makedirs(storage_dir, exist_ok=True)
        can_write = os.access(storage_dir, os.W_OK)

        report["test_results"]["file_system"] = {
            "status": "PASS" if can_write else "WARN",
            "storage_dir": storage_dir,
            "platformdirs_available": storage_available,
            "can_write": can_write,
            "exists": os.path.exists(storage_dir)
        }
        if can_write:
            report["summary"]["passed"] += 1
        else:
            report["summary"]["warnings"] += 1
    except Exception as e:
        report["test_results"]["file_system"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 9: Kivy Components
    try:
        from kivy import __version__ as kivy_version
        report["test_results"]["kivy"] = {
            "status": "PASS",
            "version": kivy_version,
            "components": ["App", "ScreenManager", "BoxLayout", "Button", "Label"]
        }
        report["summary"]["passed"] += 1
    except Exception as e:
        report["test_results"]["kivy"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Test 10: Crash Logging
    try:
        crash_log_available = _UDAC_CRASH_LOG_PATH is not None
        report["test_results"]["crash_logging"] = {
            "status": "PASS" if crash_log_available else "WARN",
            "crash_log_path": _UDAC_CRASH_LOG_PATH,
            "available": crash_log_available
        }
        if crash_log_available:
            report["summary"]["passed"] += 1
        else:
            report["summary"]["warnings"] += 1
    except Exception as e:
        report["test_results"]["crash_logging"] = {
            "status": "FAIL",
            "error": str(e)
        }
        report["summary"]["failed"] += 1

    # Calculate overall status
    total_tests = report["summary"]["passed"] + report["summary"]["failed"] + report["summary"]["warnings"]
    report["summary"]["total_tests"] = total_tests
    report["summary"]["pass_rate"] = f"{(report['summary']['passed'] / total_tests * 100):.1f}%" if total_tests > 0 else "0%"

    if report["summary"]["failed"] == 0:
        report["overall_status"] = "HEALTHY" if report["summary"]["warnings"] == 0 else "DEGRADED"
    else:
        report["overall_status"] = "CRITICAL"

    return report


# Color palette for modern UI
COLORS = {
    'bg_primary': (0.04, 0.04, 0.12, 1),      # Deep space blue
    'bg_secondary': (0.08, 0.08, 0.16, 1),    # Elevated surface
    'bg_tertiary': (0.12, 0.11, 0.23, 1),     # Card background
    'accent_primary': (0.39, 0.40, 0.95, 1),  # Indigo
    'accent_success': (0.06, 0.73, 0.51, 1),  # Green
    'accent_warning': (0.96, 0.62, 0.04, 1),  # Amber
    'text_primary': (0.95, 0.96, 0.97, 1),    # High emphasis
    'text_secondary': (0.61, 0.64, 0.69, 1),  # Medium emphasis
    'text_tertiary': (0.42, 0.45, 0.50, 1),   # Low emphasis
}


class HomeScreen(Screen):
    """Home screen with platform selection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rect = None
        self.build_ui()

    def _update_rect(self, instance, value):
        """Update background rectangle size."""
        if self.rect:
            self.rect.size = instance.size
            self.rect.pos = instance.pos

    def build_ui(self):
        """Build the home screen UI with professional styling."""
        from kivy.graphics import Color, Rectangle

        layout = BoxLayout(orientation='vertical', padding=20, spacing=12)

        # Set background color
        with layout.canvas.before:
            Color(*COLORS['bg_primary'])
            self.bg_rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=lambda *args: setattr(self.bg_rect, 'size', layout.size))
        layout.bind(pos=lambda *args: setattr(self.bg_rect, 'pos', layout.pos))

        # Header
        header = Label(
            text='🧠 UDAC Portal',
            size_hint=(1, 0.08),
            font_size='28sp',
            bold=True,
            color=COLORS['accent_primary']
        )
        layout.add_widget(header)

        # Tagline
        tagline = Label(
            text='The AI Browser with Memory',
            size_hint=(1, 0.04),
            font_size='13sp',
            color=COLORS['text_secondary']
        )
        layout.add_widget(tagline)

        # Status card
        status_card = BoxLayout(orientation='vertical', size_hint=(1, 0.14), padding=16, spacing=8)
        with status_card.canvas.before:
            Color(*COLORS['bg_secondary'])
            self.status_rect = Rectangle(size=status_card.size, pos=status_card.pos)
        status_card.bind(size=lambda *args: setattr(self.status_rect, 'size', status_card.size))
        status_card.bind(pos=lambda *args: setattr(self.status_rect, 'pos', status_card.pos))

        # Premium indicator
        tier_text = "PREMIUM" if ENTITLEMENTS.is_premium() else "FREE"
        tier_color = COLORS['accent_warning'] if ENTITLEMENTS.is_premium() else COLORS['text_tertiary']
        self.premium_label = Label(
            text=f'{"⭐" if ENTITLEMENTS.is_premium() else "○"} {tier_text} Tier',
            size_hint=(1, 0.5),
            font_size='14sp',
            bold=True,
            color=tier_color
        )
        status_card.add_widget(self.premium_label)

        # Continuity indicator
        cont_enabled = ENGINE.settings.continuity_enabled
        cont_color = COLORS['accent_success'] if cont_enabled else COLORS['text_tertiary']
        self.continuity_label = Label(
            text=f'{"●" if cont_enabled else "○"} Continuity {"Enabled" if cont_enabled else "Disabled"} • Strength {ENGINE.settings.injection_strength}/10',
            size_hint=(1, 0.5),
            font_size='12sp',
            color=COLORS['text_secondary']
        )
        status_card.add_widget(self.continuity_label)
        layout.add_widget(status_card)

        # Toggle premium button
        toggle_btn = Button(
            text='⭐ Toggle Premium (Local Demo)',
            size_hint=(1, 0.06),
            on_press=self.toggle_tier,
            background_color=COLORS['bg_tertiary'],
            color=COLORS['text_primary']
        )
        layout.add_widget(toggle_btn)

        # Settings button
        settings_btn = Button(
            text='⚙️ Settings',
            size_hint=(1, 0.06),
            on_press=self.go_to_settings,
            background_color=COLORS['bg_tertiary'],
            color=COLORS['text_primary']
        )
        layout.add_widget(settings_btn)

        # Platform selection header
        platforms_label = Label(
            text='AI Platforms',
            size_hint=(1, 0.04),
            font_size='16sp',
            bold=True,
            color=COLORS['text_primary']
        )
        layout.add_widget(platforms_label)

        # Platform buttons (scrollable)
        scroll = ScrollView(size_hint=(1, 0.54))
        platform_grid = GridLayout(cols=2, spacing=12, size_hint_y=None, padding=10)
        platform_grid.bind(minimum_height=platform_grid.setter('height'))

        platforms = REGISTRY.get_all_platforms()
        for platform in platforms:
            # Platform card button
            btn_color = COLORS['bg_tertiary'] if platform.enabled else COLORS['bg_secondary']
            text_color = COLORS['text_primary'] if platform.enabled else COLORS['text_tertiary']

            btn = Button(
                text=f'{platform.icon}\n{platform.name}\n{"● Ready" if platform.enabled else "○ Disabled"}',
                size_hint=(None, None),
                size=(160, 130),
                disabled=not platform.enabled,
                background_color=btn_color,
                color=text_color,
                font_size='13sp',
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
        tier_color = (1, 0.8, 0, 1) if ENTITLEMENTS.is_premium() else (0.5, 0.5, 0.6, 1)
        self.premium_label.text = f'▸ TIER: {tier_text}'
        self.premium_label.color = tier_color

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
        self.rect = None
        self.build_ui()

    def _update_rect(self, instance, value):
        """Update background rectangle size."""
        if self.rect:
            self.rect.size = instance.size
            self.rect.pos = instance.pos

    def build_ui(self):
        """Build the portal screen UI."""
        layout = BoxLayout(orientation='vertical', padding=8, spacing=8)

        # Set dark futuristic background
        from kivy.graphics import Color, Rectangle
        with layout.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
            layout.bind(size=self._update_rect, pos=self._update_rect)

        # Top bar with back button and platform name
        top_bar = BoxLayout(size_hint=(1, 0.08), spacing=10)

        back_btn = Button(
            text='◂ BACK',
            size_hint=(0.3, 1),
            on_press=self.go_home,
            background_color=(0.15, 0.15, 0.25, 1),
            background_normal='',
            color=(0.7, 0.8, 1, 1),
            bold=True
        )
        top_bar.add_widget(back_btn)

        self.platform_label = Label(
            text='▸ SELECT PLATFORM',
            size_hint=(0.7, 1),
            font_size='16sp',
            bold=True,
            color=(0, 0.9, 1, 1)
        )
        top_bar.add_widget(self.platform_label)

        layout.add_widget(top_bar)

        # WebView placeholder with futuristic styling
        self.webview_container = BoxLayout(size_hint=(1, 0.77))
        self.webview_placeholder = Label(
            text='━━━ WEBVIEW STANDBY ━━━\n\nSelect a platform to begin',
            font_size='14sp',
            color=(0.4, 0.6, 0.8, 1)
        )
        self.webview_container.add_widget(self.webview_placeholder)
        layout.add_widget(self.webview_container)

        # Context indicator with modern styling
        self.context_label = Label(
            text='▸ CONTINUITY: READY',
            size_hint=(1, 0.04),
            font_size='11sp',
            color=(0, 1, 0.6, 1),
            bold=True
        )
        layout.add_widget(self.context_label)

        # Input bar with modern styling
        input_bar = BoxLayout(size_hint=(1, 0.11), spacing=8)

        self.input_field = TextInput(
            hint_text='▸ Enter message...',
            multiline=False,
            size_hint=(0.75, 1),
            background_color=(0.1, 0.15, 0.2, 1),
            foreground_color=(0.9, 0.9, 1, 1),
            cursor_color=(0, 0.9, 1, 1),
            font_size='14sp'
        )
        self.input_field.bind(on_text_validate=self.send_message)
        input_bar.add_widget(self.input_field)

        send_btn = Button(
            text='SEND ▸',
            size_hint=(0.25, 1),
            on_press=self.send_message,
            background_color=(0.1, 0.3, 0.5, 1),
            background_normal='',
            color=(0, 0.9, 1, 1),
            bold=True
        )
        input_bar.add_widget(send_btn)

        layout.add_widget(input_bar)

        self.add_widget(layout)

    def load_platform(self, platform):
        """Load a platform into the WebView."""
        print(f"[UDAC] load_platform called for: {platform.name}")

        # Set platform info first
        self.current_platform = platform
        self.platform_label.text = f'▸ {platform.icon} {platform.name.upper()}'

        # Start session
        try:
            SESSION.start_session(platform.id)
            print("[UDAC] Session started")
        except Exception as e:
            print(f"[UDAC] Session start error: {e}")

        # Check if jnius is available before attempting WebView
        if not JNIUS_AVAILABLE:
            print("[UDAC] jnius not available, showing fallback message")
            self.webview_placeholder.text = (
                f'━━━ WEBVIEW UNAVAILABLE ━━━\n\n'
                f'🌐 {platform.name.upper()}\n\n'
                f'Platform access requires WebView support.\n\n'
                f'Open in mobile browser:\n{platform.base_url}\n\n'
                f'(Continuity features disabled)'
            )
            return

        # Try to load WebView
        try:
            print("[UDAC] Attempting to load WebView...")
            self.load_webview(platform.base_url)
        except Exception as e:
            import traceback
            print(f"[UDAC] Error loading platform: {e}")
            print(traceback.format_exc())

            # Show error in UI
            self.webview_placeholder.text = (
                f'━━━ CONNECTION ERROR ━━━\n\n'
                f'{str(e)}\n\n'
                f'Use browser:\n{platform.base_url}'
            )
            self.platform_label.text = f'▸ {platform.icon} {platform.name.upper()} [ERROR]'

    def load_webview(self, url):
        """Load URL in WebView (Android WebView)."""
        # Defensive check - should not be called if jnius unavailable
        if not JNIUS_AVAILABLE:
            print("[UDAC] load_webview called but jnius not available")
            return

        # Import jnius classes
        try:
            from jnius import autoclass, PythonJavaClass, java_method
        except Exception as e:
            print(f"[UDAC] Failed to import jnius: {e}")
            self.webview_placeholder.text = f'WebView import failed\n\n{str(e)}'
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
                        # Inject directly without Clock.schedule_once to avoid Handler errors
                        # (onPageFinished is already called on UI thread, no need for Clock)
                        try:
                            # Inject the bridge script with error wrapping
                            bridge_script = PortalScriptBuilder.build(
                                self.portal_screen.current_platform
                            )
                            # Wrap in try-catch for safety
                            safe_script = f"try {{ {bridge_script} }} catch(e) {{ console.log('UDAC bridge error:', e); }}"
                            # Use loadUrl to execute JavaScript
                            view.loadUrl(f"javascript:{safe_script}")
                            print("[UDAC] ✓ Bridge script injected successfully")
                        except Exception as e:
                            print(f"[UDAC] Script injection failed: {e}")
                            import traceback
                            traceback.print_exc()

            # Create WebView on UI thread with comprehensive error handling
            def create_webview(dt):
                try:
                    # Check if we're still on portal screen (race condition fix)
                    if not hasattr(self, 'manager') or self.manager.current != 'portal':
                        print("[UDAC] Portal screen no longer active, skipping WebView creation")
                        return

                    print(f"[UDAC] Creating WebView for {url}...")

                    # Create WebView
                    self.webview = WebView(activity)

                    # Configure settings with error handling on each call
                    try:
                        settings = self.webview.getSettings()
                        settings.setJavaScriptEnabled(True)
                        settings.setDomStorageEnabled(True)
                        settings.setDatabaseEnabled(True)
                        settings.setAllowFileAccess(False)
                        settings.setAllowContentAccess(True)
                        settings.setMediaPlaybackRequiresUserGesture(False)
                        # Enable modern WebView features for better compatibility
                        settings.setMixedContentMode(0)  # MIXED_CONTENT_ALWAYS_ALLOW
                        print("[UDAC] ✓ WebView settings configured")
                    except Exception as e:
                        print(f"[UDAC] Warning: Some WebView settings failed: {e}")

                    # Set up JavaScript bridge
                    try:
                        self.bridge = UDACBridge(self)
                        self.webview.addJavascriptInterface(self.bridge, 'UDACBridge')
                        print("[UDAC] ✓ JavaScript bridge added")
                    except Exception as e:
                        print(f"[UDAC] Warning: JavaScript bridge setup failed: {e}")

                    # Set custom WebViewClient
                    try:
                        self.webview_client = UDACWebViewClient(self)
                        self.webview.setWebViewClient(self.webview_client)
                        print("[UDAC] ✓ WebViewClient set")
                    except Exception as e:
                        print(f"[UDAC] Warning: WebViewClient setup failed: {e}")

                    # Set WebChromeClient for better JS support
                    try:
                        self.webview.setWebChromeClient(WebChromeClient())
                        print("[UDAC] ✓ WebChromeClient set")
                    except Exception as e:
                        print(f"[UDAC] Warning: WebChromeClient setup failed: {e}")

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
                        print(f"[UDAC] ✓ WebView created and loading: {url}")

                        # Update placeholder
                        self.webview_placeholder.text = f'Loading {self.current_platform.name}...\n(WebView active)'
                    else:
                        print("[UDAC] ERROR: Could not get Android layout")
                        self.webview_placeholder.text = 'WebView initialization error\n(Could not find Android layout)'

                except Exception as e:
                    import traceback
                    print(f"[UDAC] ERROR: WebView creation failed: {e}")
                    print(traceback.format_exc())
                    if hasattr(self, 'webview_placeholder'):
                        self.webview_placeholder.text = f'WebView creation failed\n\n{str(e)}\n\nCheck logcat for details'

            # Delay WebView creation slightly to ensure UI is ready
            Clock.schedule_once(create_webview, 0.3)

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

        # Update context label with futuristic styling
        sources = ", ".join(payload.context_sources) if payload.context_sources else "LOCAL"
        self.context_label.text = f'▸ +{payload.tokens_added} TOKENS | SRC: {sources.upper()}'

        # Inject into WebView via JavaScript
        if self.webview:
            try:
                injection_script = PortalScriptBuilder.build_send_prompt_script(
                    self.current_platform,
                    payload.final_prompt_text
                )
                # Use loadUrl instead of evaluateJavascript to avoid Handler null reference
                self.webview.loadUrl(f"javascript:{injection_script}")
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
                # Check if jnius is available first
                try:
                    from jnius import autoclass
                except ImportError:
                    print("[UDAC] jnius not available, skipping native WebView cleanup")
                    self.webview = None
                    # Continue to session cleanup below

                if self.webview:  # Only if not already cleared above
                    activity = autoclass('org.kivy.android.PythonActivity').mActivity
                    layout = activity.findViewById(0x01020002)
                    if layout:
                        layout.removeView(self.webview)
                    self.webview.destroy()
                    self.webview = None
                    print("[UDAC] WebView cleaned up")
            except Exception as e:
                print(f"[UDAC] WebView cleanup error: {e}")
                # Still clear the reference to prevent memory leak
                self.webview = None

        # Always end session, even if WebView cleanup failed
        try:
            if self.current_platform:
                SESSION.shutdown()
                print("[UDAC] Session ended")
        except Exception as e:
            print(f"[UDAC] Session shutdown error: {e}")

        self.current_platform = None
        self.manager.current = 'home'


class SettingsScreen(Screen):
    """Settings screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rect = None
        self.build_ui()

    def _update_rect(self, instance, value):
        """Update background rectangle size."""
        if self.rect:
            self.rect.size = instance.size
            self.rect.pos = instance.pos

    def build_ui(self):
        """Build settings UI."""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Set dark futuristic background
        from kivy.graphics import Color, Rectangle
        with layout.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
            layout.bind(size=self._update_rect, pos=self._update_rect)

        # Header with futuristic styling
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(
            text='◂ BACK',
            size_hint=(0.3, 1),
            on_press=self.go_back,
            background_color=(0.15, 0.15, 0.25, 1),
            background_normal='',
            color=(0.7, 0.8, 1, 1),
            bold=True
        )
        header.add_widget(back_btn)

        title = Label(
            text='⚙ SETTINGS',
            size_hint=(0.7, 1),
            font_size='22sp',
            bold=True,
            color=(0, 0.9, 1, 1)
        )
        header.add_widget(title)
        layout.add_widget(header)

        # Scrollable settings
        scroll = ScrollView(size_hint=(1, 0.9))
        settings_box = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=10)
        settings_box.bind(minimum_height=settings_box.setter('height'))

        # Continuity toggle with futuristic styling
        cont_status = "ACTIVE" if ENGINE.settings.continuity_enabled else "OFFLINE"
        cont_color = (0, 1, 0.6, 1) if ENGINE.settings.continuity_enabled else (0.9, 0.3, 0.3, 1)
        cont_label = Label(
            text=f'▸ CONTINUITY: {cont_status}',
            size_hint=(1, None),
            height=40,
            font_size='16sp',
            color=cont_color,
            bold=True
        )
        settings_box.add_widget(cont_label)

        toggle_cont_btn = Button(
            text='TOGGLE CONTINUITY',
            size_hint=(1, None),
            height=50,
            on_press=lambda x: self.toggle_continuity(cont_label),
            background_color=(0.1, 0.3, 0.5, 1),
            background_normal='',
            color=(0, 0.85, 1, 1),
            bold=True
        )
        settings_box.add_widget(toggle_cont_btn)

        # Injection strength slider with futuristic styling
        strength_label = Label(
            text=f'▸ INJECTION STRENGTH: {ENGINE.settings.injection_strength}/10',
            size_hint=(1, None),
            height=40,
            font_size='16sp',
            color=(0.7, 0.85, 1, 1),
            bold=True
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

        # Platform isolation (premium) with futuristic styling
        iso_status = 'ON' if ENGINE.settings.platform_isolation_mode else 'OFF'
        iso_color = (1, 0.8, 0, 1) if ENTITLEMENTS.is_premium() else (0.5, 0.5, 0.6, 1)
        iso_text = f'▸ PLATFORM ISOLATION: {iso_status}'
        if not ENTITLEMENTS.is_premium():
            iso_text += ' [PREMIUM]'

        iso_label = Label(
            text=iso_text,
            size_hint=(1, None),
            height=40,
            font_size='16sp',
            color=iso_color,
            bold=True
        )
        settings_box.add_widget(iso_label)

        toggle_iso_btn = Button(
            text='TOGGLE ISOLATION',
            size_hint=(1, None),
            height=50,
            disabled=not ENTITLEMENTS.is_premium(),
            on_press=lambda x: self.toggle_isolation(iso_label),
            background_color=(0.1, 0.3, 0.5, 1) if ENTITLEMENTS.is_premium() else (0.15, 0.15, 0.2, 1),
            background_normal='',
            color=(0, 0.85, 1, 1) if ENTITLEMENTS.is_premium() else (0.4, 0.4, 0.5, 1),
            bold=True
        )
        settings_box.add_widget(toggle_iso_btn)

        # Clear data button with futuristic styling
        clear_btn = Button(
            text='🗑 CLEAR ALL DATA',
            size_hint=(1, None),
            height=50,
            background_color=(0.8, 0.2, 0.2, 1),
            background_normal='',
            color=(1, 1, 1, 1),
            bold=True,
            on_press=self.clear_data
        )
        settings_box.add_widget(clear_btn)

        # Diagnostic button with futuristic styling
        diagnostic_btn = Button(
            text='🔍 RUN DIAGNOSTICS',
            size_hint=(1, None),
            height=50,
            background_color=(0.1, 0.5, 0.3, 1),
            background_normal='',
            color=(0, 1, 0.6, 1),
            bold=True,
            on_press=self.run_diagnostics
        )
        settings_box.add_widget(diagnostic_btn)

        # Diagnostic results display
        self.diagnostic_label = Label(
            text='',
            size_hint=(1, None),
            height=0,
            font_size='12sp',
            markup=True
        )
        settings_box.add_widget(self.diagnostic_label)

        # Stats with futuristic styling
        stats = ENGINE.get_stats()
        stats_text = f"""[b]━━━ SYSTEM STATUS ━━━[/b]

▸ Continuity: {"ENABLED" if stats['enabled'] else "DISABLED"}
▸ Injection Strength: {stats['injection_strength']}/10
▸ Cross-platform memories: {stats['cross_platform_memories']}
▸ Platform isolation: {"YES" if stats['platform_isolation'] else "NO"}
        """
        stats_label = Label(
            text=stats_text.strip(),
            size_hint=(1, None),
            height=150,
            font_size='13sp',
            color=(0.7, 0.8, 0.9, 1),
            markup=True,
            bold=True
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
        cont_status = "ACTIVE" if new_value else "OFFLINE"
        cont_color = (0, 1, 0.6, 1) if new_value else (0.9, 0.3, 0.3, 1)
        label.text = f'▸ CONTINUITY: {cont_status}'
        label.color = cont_color

    def update_strength(self, value, label):
        """Update injection strength."""
        strength = int(value)
        ENGINE.update_settings(injection_strength=strength)
        label.text = f'▸ INJECTION STRENGTH: {strength}/10'

    def toggle_isolation(self, label):
        """Toggle platform isolation."""
        if ENTITLEMENTS.is_premium():
            new_value = not ENGINE.settings.platform_isolation_mode
            ENGINE.update_settings(platform_isolation_mode=new_value)
            label.text = f'▸ PLATFORM ISOLATION: {"ON" if new_value else "OFF"}'

    def clear_data(self, instance):
        """Clear all continuity data."""
        ENGINE.clear_all_data()
        print("[UDAC] All data cleared!")

    def run_diagnostics(self, instance):
        """Run comprehensive diagnostics and display results."""
        print("[UDAC] Running diagnostics...")

        # Run diagnostics
        report = run_diagnostics()

        # Save to file
        try:
            # Try to get storage directory
            try:
                from platformdirs import user_data_dir
                storage_dir = user_data_dir("UDAC Portal", "Sunni")
            except ImportError:
                import tempfile
                storage_dir = os.path.join(tempfile.gettempdir(), "udac_portal")

            os.makedirs(storage_dir, exist_ok=True)
            diagnostic_file = os.path.join(storage_dir, f"diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

            with open(diagnostic_file, 'w') as f:
                json.dump(report, f, indent=2)

            print(f"[UDAC] Diagnostic report saved to: {diagnostic_file}")
            file_saved = True
            file_path = diagnostic_file
        except Exception as e:
            print(f"[UDAC] Failed to save diagnostic file: {e}")
            file_saved = False
            file_path = None

        # Display summary
        status = report["overall_status"]
        summary = report["summary"]

        # Color codes for status
        if status == "HEALTHY":
            status_color = "00ff99"
        elif status == "DEGRADED":
            status_color = "ffaa00"
        else:
            status_color = "ff4444"

        # Build summary text
        summary_text = f"""[b]━━━ DIAGNOSTIC REPORT ━━━[/b]

[color={status_color}]Status: {status}[/color]

[b]Test Summary:[/b]
✓ Passed: {summary['passed']}
⚠ Warnings: {summary['warnings']}
✗ Failed: {summary['failed']}
━━━━━━━━━━━━
Total: {summary['total_tests']} tests
Pass Rate: {summary['pass_rate']}

"""

        # Add key test results
        if "jnius" in report["test_results"]:
            jnius_status = report["test_results"]["jnius"]["status"]
            jnius_icon = "✓" if jnius_status == "PASS" else "⚠" if jnius_status == "WARN" else "✗"
            summary_text += f"{jnius_icon} WebView/jnius: {jnius_status}\n"

        if "android_classes" in report["test_results"]:
            android_status = report["test_results"]["android_classes"]["status"]
            android_icon = "✓" if android_status == "PASS" else "⊘" if android_status == "SKIP" else "✗"
            summary_text += f"{android_icon} Android Classes: {android_status}\n"

        if "platform_registry" in report["test_results"]:
            platform_data = report["test_results"]["platform_registry"]
            if platform_data["status"] == "PASS":
                summary_text += f"✓ Platforms: {platform_data['enabled_platforms']}/{platform_data['total_platforms']} enabled\n"

        if "continuity_engine" in report["test_results"]:
            cont_data = report["test_results"]["continuity_engine"]
            if cont_data["status"] == "PASS":
                cont_status = "ON" if cont_data["enabled"] else "OFF"
                summary_text += f"✓ Continuity: {cont_status} (strength: {cont_data['injection_strength']})\n"

        if file_saved:
            summary_text += f"\n[b]Full report saved:[/b]\n{file_path}"
        else:
            summary_text += f"\n[color=ff4444]Could not save report file[/color]"

        # Update label
        self.diagnostic_label.text = summary_text
        self.diagnostic_label.height = 400

        print("[UDAC] Diagnostics complete!")


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
