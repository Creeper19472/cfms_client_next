import flet as ft

from include.ui.util.notifications import send_error


class AlertDialog(ft.AlertDialog):
    """
    AlertDialog(ft.AlertDialog)

    A lightweight dialog wrapper that provides explicit lifecycle helpers for enabling/disabling
    user interactions and a convenient close action.

    This class extends the base ft.AlertDialog and centralizes common behaviors used by
    application dialogs:
    
    - enable_interactions()
        Intended to re-enable user interaction within the dialog (e.g., re-enable buttons,
        inputs, or other controls) after a temporary disabled state. The base implementation
        is a no-op; override in subclasses to apply concrete behavior.
    - disable_interactions()
        Intended to disable user interaction within the dialog (e.g., while a background task
        is running or a network request is in progress). The base implementation is a no-op;
        override in subclasses to apply concrete behavior.
    - close() -> None
        Closes the dialog by setting the inherited `open` attribute to False and calling
        `update()` to refresh the UI. Subclasses may override to perform teardown or
        additional actions, but should generally call super().close() to ensure the dialog
        is properly closed and the UI updated.
    """

    def enable_interactions(self):
        """
        Enable user interactions with the dialog.
        Override in subclasses if needed.
        """
        pass

    def disable_interactions(self):
        """
        Disable user interactions with the dialog.
        Override in subclasses if needed.
        """
        pass

    def send_error(self, message: str):
        send_error(self.page, message)

    def close(self) -> None:
        self.open = False
        self.update()
