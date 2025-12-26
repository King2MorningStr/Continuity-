"""
UDAC Portal - Kivy Test Version
================================
Testing if Kivy works on Android where Toga failed.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class UDACTestApp(App):
    def build(self):
        print("[KIVY] Building UI...")

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title
        title = Label(
            text='UDAC Portal - Kivy Test',
            size_hint=(1, 0.3),
            font_size='24sp'
        )
        layout.add_widget(title)

        # Test button
        btn = Button(
            text='Click Me - Test Kivy',
            size_hint=(1, 0.2)
        )
        btn.bind(on_press=self.on_button_click)
        layout.add_widget(btn)

        # Status
        self.status = Label(
            text='Kivy is working!',
            size_hint=(1, 0.5)
        )
        layout.add_widget(self.status)

        print("[KIVY] ✅ UI built successfully!")
        return layout

    def on_button_click(self, instance):
        print("[KIVY] Button clicked!")
        self.status.text = 'Button works! Kivy is compatible!'


if __name__ == '__main__':
    UDACTestApp().run()
