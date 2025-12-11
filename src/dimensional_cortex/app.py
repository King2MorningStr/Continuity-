import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from .core.platform_registry import PlatformRegistry
from .core.session_manager import SessionManager
from .core.continuity_engine import ContinuityEngine
from .core.logger import InteractionLogger
from .ui.web_host import PortalWebHost

class UDACApp(toga.App):
    def startup(self):
        self.platform_registry = PlatformRegistry()
        self.logger = InteractionLogger()
        self.continuity_engine = ContinuityEngine()
        self.session_manager = SessionManager(self.continuity_engine, self.logger)

        self.main_window = toga.MainWindow(title=self.formal_name)

        # Simple UI: Platform List on left (or top), WebHost in center, Controls on bottom
        self.main_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        # Platform Selector
        self.platform_select = toga.Selection(
            items=[p.name for p in self.platform_registry.get_all()],
            on_select=self.on_platform_selected,
            style=Pack(padding=5)
        )

        # Web Host Container
        self.web_container = toga.Box(style=Pack(flex=1))

        # Input Area (UDAC Input Layer)
        self.input_input = toga.TextInput(placeholder="Type your prompt...", style=Pack(flex=1))
        self.send_button = toga.Button("Send", on_press=self.on_send, style=Pack(padding_left=5))
        self.input_box = toga.Box(
            children=[self.input_input, self.send_button],
            style=Pack(direction=ROW, padding=5)
        )

        self.main_box.add(self.platform_select)
        self.main_box.add(self.web_container)
        self.main_box.add(self.input_box)

        self.main_window.content = self.main_box
        self.main_window.show()

        # Load initial platform
        self.on_platform_selected(self.platform_select)

    def on_platform_selected(self, widget):
        selected_name = widget.value
        # Find platform object
        platform = next((p for p in self.platform_registry.get_all() if p.name == selected_name), None)
        if platform:
            self.current_web_host = PortalWebHost(platform, self.session_manager)

            # Clear container and add new webview
            # Note: Toga might need specific handling to replace content efficiently
            if self.web_container.children:
                 self.web_container.remove(self.web_container.children[0])

            self.web_container.add(self.current_web_host.create_widget())
            self.web_container.refresh()

    def on_send(self, widget):
        text = self.input_input.value
        if text and self.current_web_host:
            platform_id = self.current_web_host.platform.id
            self.session_manager.on_user_submit_from_udac(
                platform_id,
                text,
                self.current_web_host
            )
            self.input_input.value = ""

def main():
    return UDACApp()

if __name__ == '__main__':
    main().main_loop()
