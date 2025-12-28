"""Kivy application entrypoint compatible with the previous Toga-style API."""

from udac_portal.kivy_app import UDACPortalApp


class _PortalAppWithLoop(UDACPortalApp):
    """Expose a Briefcase-friendly ``main_loop`` alias for ``run``."""

    def main_loop(self):
        return self.run()


def main():
    """Return a configured Kivy ``App`` instance."""
    return _PortalAppWithLoop()


if __name__ == "__main__":
    main().main_loop()
