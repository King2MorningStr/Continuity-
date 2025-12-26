"""
UDAC Portal - Minimal Test Version
===================================
Test basic Toga functionality step by step.
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

class UDACPortalApp(toga.App):
    """Minimal test app."""

    def startup(self):
        """Initialize with absolute minimum."""
        print("[MINIMAL] Starting app...")

        # Step 1: Create window
        print("[MINIMAL] Creating main window...")
        self.main_window = toga.MainWindow(title="UDAC Test")

        # Step 2: Create simple box
        print("[MINIMAL] Creating box...")
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Step 3: Add simple label
        print("[MINIMAL] Adding label...")
        label = toga.Label(
            'UDAC Portal - Minimal Test',
            style=Pack(padding=10)
        )
        main_box.add(label)

        # Step 4: Add button
        print("[MINIMAL] Adding button...")
        button = toga.Button(
            'Click Me',
            on_press=self.say_hello,
            style=Pack(padding=10)
        )
        main_box.add(button)

        # Step 5: Set content
        print("[MINIMAL] Setting content...")
        self.main_window.content = main_box

        # Step 6: Show window
        print("[MINIMAL] Showing window...")
        self.main_window.show()

        print("[MINIMAL] ✅ Startup complete!")

    def say_hello(self, widget):
        """Test button click."""
        print("[MINIMAL] Button clicked!")
        self.main_window.info_dialog('Hello', 'UDAC Portal is working!')


def main():
    return UDACPortalApp(
        'UDAC Portal Minimal',
        'com.udacportal.minimal',
        formal_name='UDAC Minimal'
    )


if __name__ == '__main__':
    main().main_loop()
