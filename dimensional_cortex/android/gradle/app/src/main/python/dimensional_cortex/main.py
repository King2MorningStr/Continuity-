"""
Dimensional Cortex - UDAC Continuity Engine
============================================
Enhanced Dashboard Version
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, BOLD, LEFT, RIGHT
import sys
import logging
import asyncio
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UDAC")

# Track what loaded
MODULES_LOADED = {
    'trinity': False,
    'udac': False,
    'injector': False
}
ERRORS = []

# Try imports
try:
    from dimensional_cortex.dimensional_memory_constant_standalone_demo import start_memory_system, stop_memory_system
    from dimensional_cortex.dimensional_processing_system_standalone_demo import CrystalMemorySystem, GovernanceEngine
    from dimensional_cortex.dimensional_energy_regulator_mobile import DimensionalEnergyRegulator
    MODULES_LOADED['trinity'] = True
    logger.info("Trinity modules loaded")
except Exception as e:
    ERRORS.append(f"Trinity: {e}")
    logger.error(f"Trinity load failed: {e}")

try:
    from dimensional_cortex.udac_listener import start_udac_listener, get_udac_stats
    MODULES_LOADED['udac'] = True
    logger.info("UDAC module loaded")
except Exception as e:
    ERRORS.append(f"UDAC: {e}")
    logger.error(f"UDAC load failed: {e}")

try:
    from dimensional_cortex.continuity_injector import get_injector, Platform, InjectionResult
    MODULES_LOADED['injector'] = True
    logger.info("Injector module loaded")
except Exception as e:
    ERRORS.append(f"Injector: {e}")
    logger.error(f"Injector load failed: {e}")


class TrinityManager:
    """Manages Trinity system."""

    def __init__(self):
        self.running = False
        self.memory_system = None
        self.crystal_system = None
        self.energy_regulator = None
        self.error = None
        self.start_time = None
        self.conversations_processed = 0 # Mock for demo

    def start(self):
        if self.running:
            return True

        if not MODULES_LOADED['trinity']:
            self.error = "Trinity modules not loaded"
            return False

        try:
            logger.info("Starting Trinity...")

            # Memory
            self.memory_governor, self.memory_system, self.save_thread, self.merge_thread = start_memory_system()

            # Processing
            governance = GovernanceEngine(data_theme="conversation")
            self.crystal_system = CrystalMemorySystem(governance_engine=governance)

            # Energy
            self.energy_regulator = DimensionalEnergyRegulator(conservation_limit=50.0)

            # Injector connection
            if MODULES_LOADED['injector']:
                injector = get_injector()
                injector.set_trinity(self)

            self.running = True
            self.start_time = time.time()
            logger.info("Trinity online!")
            return True

        except Exception as e:
            self.error = str(e)
            logger.error(f"Trinity start failed: {e}")
            return False

    def get_stats(self):
        if not self.running:
            return {'nodes': 0, 'crystals': 0, 'energy': 0.0, 'uptime': '0s'}

        try:
            uptime = int(time.time() - self.start_time) if self.start_time else 0
            energy = 0.0
            if self.energy_regulator:
                # Basic energy sum
                energy = sum(self.energy_regulator.facet_energy.values())

            return {
                'nodes': len(self.memory_system.nodes) if self.memory_system else 0,
                'crystals': len(self.crystal_system.crystals) if self.crystal_system else 0,
                'energy': round(energy, 2),
                'uptime': f"{uptime}s"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'nodes': 0, 'crystals': 0, 'energy': 0.0, 'uptime': 'Error'}


# Global instance
TRINITY = TrinityManager()


class UDACApp(toga.App):
    """Main UDAC Application."""

    def startup(self):
        logger.info("=== UDAC App Starting ===")

        self.main_window = toga.MainWindow(title=self.formal_name)

        # --- Main Layout ---
        # Add flex=1 to ensure it fills the screen
        main_box = toga.Box(style=Pack(
            direction=COLUMN,
            background_color='#1a1a2e',
            flex=1
        ))

        # --- 1. Header ---
        header_box = toga.Box(style=Pack(
            direction=COLUMN,
            padding=15,
            background_color='#252542'
        ))
        header_box.add(toga.Label(
            '⚡ UDAC Continuity Engine',
            style=Pack(font_size=18, font_weight=BOLD, color='#00d4aa')
        ))
        header_box.add(toga.Label(
            'Universal AI Memory Bridge',
            style=Pack(font_size=12, color='#888888')
        ))

        self.status_label = toga.Label(
            'System Ready',
            style=Pack(color='#ffa500', font_size=12, padding_top=5)
        )
        header_box.add(self.status_label)
        main_box.add(header_box)

        # --- 2. Stats Dashboard ---
        stats_box = toga.Box(style=Pack(
            direction=ROW,
            padding=10,
            background_color='#1a1a2e'
        ))

        # Helper to create stat cards
        def create_stat_card(label, value_id):
            card = toga.Box(style=Pack(
                direction=COLUMN,
                padding=8,
                flex=1,
                background_color='#333355',
                margin=2
            ))
            card.add(toga.Label(label, style=Pack(color='#aaaaaa', font_size=10)))
            lbl = toga.Label('0', style=Pack(color='#ffffff', font_weight=BOLD, font_size=14))
            setattr(self, value_id, lbl) # Save reference
            card.add(lbl)
            return card

        stats_box.add(create_stat_card('NODES', 'stat_nodes'))
        stats_box.add(create_stat_card('CRYSTALS', 'stat_crystals'))
        stats_box.add(create_stat_card('ENERGY', 'stat_energy'))

        main_box.add(stats_box)

        # --- 3. Snippet Window (Last Conversation) ---
        snippet_container = toga.Box(style=Pack(
            direction=COLUMN,
            padding=10,
            flex=1  # Allow this to expand
        ))
        snippet_container.add(toga.Label(
            'Last Injection Snippet:',
            style=Pack(color='#00d4aa', font_weight=BOLD, padding_bottom=5)
        ))

        self.snippet_text = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, background_color='#111122', color='#cccccc', font_family='monospace')
        )
        self.snippet_text.value = "Waiting for injection activity..."
        snippet_container.add(self.snippet_text)

        main_box.add(snippet_container)

        # --- 4. Controls / Buttons ---
        controls_box = toga.Box(style=Pack(
            direction=ROW,
            padding=10,
            background_color='#252542',
            alignment=CENTER
        ))

        # Start/Stop Trinity Button
        self.trinity_btn = toga.Button(
            'START TRINITY',
            on_press=self.toggle_trinity,
            style=Pack(background_color='#00d4aa', color='#000000', font_weight=BOLD, flex=1, margin_right=5)
        )
        controls_box.add(self.trinity_btn)

        # History Button
        history_btn = toga.Button(
            'History',
            on_press=self.open_history,
            style=Pack(background_color='#444466', color='#ffffff', flex=0.5, margin_right=5)
        )
        controls_box.add(history_btn)

        # Settings Button
        settings_btn = toga.Button(
            'Settings',
            on_press=self.open_settings,
            style=Pack(background_color='#444466', color='#ffffff', flex=0.5)
        )
        controls_box.add(settings_btn)

        main_box.add(controls_box)

        self.main_window.content = main_box
        self.main_window.show()

        # Start background update task
        self.add_background_task(self.update_dashboard_loop)

        logger.info("=== UDAC App Started ===")

    async def update_dashboard_loop(self, app):
        """Background loop to update dashboard."""
        while True:
            try:
                # Update Stats
                stats = TRINITY.get_stats()
                self.stat_nodes.text = str(stats['nodes'])
                self.stat_crystals.text = str(stats['crystals'])
                self.stat_energy.text = str(stats['energy'])

                if TRINITY.running:
                    self.status_label.text = f"✓ Online ({stats['uptime']})"
                    self.status_label.style.color = '#00d4aa'

                # Update Snippet
                if MODULES_LOADED['injector']:
                    injector = get_injector()
                    last_injection = injector.get_last_injection()
                    if last_injection:
                        # Format the snippet
                        text = f"[{datetime.fromtimestamp(last_injection.timestamp).strftime('%H:%M:%S')}] "
                        text += f"Score: {last_injection.relevance_score:.2f}\n"
                        text += f"{last_injection.context_summary}\n\n"
                        text += "--- Context Block ---\n"
                        text += last_injection.context_block

                        # Only update if changed to avoid cursor jumping (though it's readonly)
                        if self.snippet_text.value != text:
                            self.snippet_text.value = text

            except Exception as e:
                logger.error(f"Dashboard update error: {e}")

            await asyncio.sleep(2) # Update every 2 seconds

    def toggle_trinity(self, widget):
        if not TRINITY.running:
            self.status_label.text = "Starting..."
            if TRINITY.start():
                self.trinity_btn.text = "TRINITY RUNNING"
                self.trinity_btn.style.background_color = '#335533'
                self.trinity_btn.enabled = False # Can't stop it easily in this demo structure

                # Start Listener
                if MODULES_LOADED['udac']:
                    try:
                        start_udac_listener(port=7013)
                    except Exception as e:
                        logger.error(f"Listener error: {e}")
        else:
            self.status_label.text = "Already Running"

    # --- SETTINGS WINDOW ---
    def open_settings(self, widget):
        if not MODULES_LOADED['injector']:
            self.main_window.info_dialog("Error", "Injector module not loaded.")
            return

        injector = get_injector()

        settings_window = toga.Window(title="Injector Settings", size=(300, 400))
        box = toga.Box(style=Pack(direction=COLUMN, padding=15, background_color='#1a1a2e'))

        # Title
        box.add(toga.Label("Configuration", style=Pack(color='#00d4aa', font_weight=BOLD, font_size=16, padding_bottom=15)))

        # 1. Enable Toggle
        row_enable = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        row_enable.add(toga.Label("Enable Injection", style=Pack(color='#ffffff', flex=1)))

        switch_enable = toga.Switch(
            "",
            value=injector.enabled,
            on_change=lambda w: injector.configure(enabled=w.value)
        )
        row_enable.add(switch_enable)
        box.add(row_enable)

        # 2. Force Injection Toggle
        row_force = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        row_force.add(toga.Label("Force Injection", style=Pack(color='#ffffff', flex=1)))

        switch_force = toga.Switch(
            "",
            value=injector.force_injection,
            on_change=lambda w: injector.configure(force_injection=w.value)
        )
        row_force.add(switch_force)
        box.add(row_force)

        # 3. Debug Mode (Visible) Toggle
        row_debug = toga.Box(style=Pack(direction=ROW, padding_bottom=20))
        row_debug.add(toga.Label("Debug Mode (Visible)", style=Pack(color='#ffffff', flex=1)))

        switch_debug = toga.Switch(
            "",
            value=injector.debug_mode,
            on_change=lambda w: injector.configure(debug_mode=w.value)
        )
        row_debug.add(switch_debug)
        box.add(row_debug)

        # 4. Threshold Slider
        box.add(toga.Label("Relevance Threshold", style=Pack(color='#ffffff', font_weight=BOLD)))

        lbl_threshold = toga.Label(f"{injector.min_relevance:.2f}", style=Pack(color='#aaaaaa', padding_bottom=5))
        box.add(lbl_threshold)

        def on_slider_change(w):
            val = w.value
            lbl_threshold.text = f"{val:.2f}"
            injector.configure(min_relevance=val)

        slider = toga.Slider(
            value=injector.min_relevance,
            range=(0.0, 1.0),
            on_change=on_slider_change,
            style=Pack(padding_bottom=20)
        )
        box.add(slider)

        # Close Button
        btn_close = toga.Button("Close", on_press=lambda w: settings_window.close(), style=Pack(background_color='#444466'))
        box.add(btn_close)

        settings_window.content = box
        settings_window.show()

    # --- HISTORY WINDOW ---
    def open_history(self, widget):
        if not MODULES_LOADED['injector']:
            self.main_window.info_dialog("Error", "Injector module not loaded.")
            return

        injector = get_injector()
        history = injector.get_recent_injections(count=50)

        hist_window = toga.Window(title="Injection History", size=(400, 500))

        # Data source for the table
        # Format: Time, Score, Summary
        data = []
        for h in reversed(history): # Newest first
            t_str = datetime.fromtimestamp(h.timestamp).strftime('%H:%M:%S')
            data.append(
                (t_str, f"{h.relevance_score:.2f}", h.context_summary)
            )

        table = toga.Table(
            headings=["Time", "Score", "Summary"],
            data=data,
            style=Pack(flex=1)
        )

        # Layout
        box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        box.add(table)

        # Refresh Button
        def refresh_history(w):
            new_hist = injector.get_recent_injections(count=50)
            new_data = []
            for h in reversed(new_hist):
                t_str = datetime.fromtimestamp(h.timestamp).strftime('%H:%M:%S')
                new_data.append(
                    (t_str, f"{h.relevance_score:.2f}", h.context_summary)
                )
            table.data = new_data

        btn_box = toga.Box(style=Pack(direction=ROW, padding=10))
        btn_refresh = toga.Button("Refresh", on_press=refresh_history, style=Pack(flex=1, margin_right=5))
        btn_close = toga.Button("Close", on_press=lambda w: hist_window.close(), style=Pack(flex=1))

        btn_box.add(btn_refresh)
        btn_box.add(btn_close)
        box.add(btn_box)

        hist_window.content = box
        hist_window.show()


def main():
    logger.info("main() called")
    return UDACApp(
        'UDAC Continuity',
        'com.udacapp.udac'
    )


if __name__ == '__main__':
    logger.info("__main__ executing")
    app = main()
    app.main_loop()
