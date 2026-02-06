"""Base controller class for UI components."""

from typing import Generic, TypeVar

from include.classes.shared import AppShared

T = TypeVar("T")

__all__ = ["Controller"]


class Controller(Generic[T]):
    """
    Base controller class for managing UI control interactions.

    Generic type T represents the type of control being managed.

    Attributes:
        control: The UI control instance being managed
        app_shared: Singleton application configuration instance
    """

    control: T
    app_shared: AppShared

    def __init__(self, control: T, *args, **kwargs) -> None:
        """
        Initialize the controller with a control instance.

        Args:
            control: The UI control to manage
        """
        self.control = control
        self.app_shared = AppShared()
