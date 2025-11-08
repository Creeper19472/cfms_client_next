"""Base controller class for UI components."""

from typing import Generic, TypeVar

from include.classes.config import AppConfig

T = TypeVar('T')

__all__ = ["BaseController"]


class BaseController(Generic[T]):
    """
    Base controller class for managing UI control interactions.
    
    Generic type T represents the type of control being managed.
    
    Attributes:
        control: The UI control instance being managed
        app_config: Singleton application configuration instance
    """
    
    control: T
    app_config: AppConfig

    def __init__(self, control: T, *args, **kwargs) -> None:
        """
        Initialize the controller with a control instance.
        
        Args:
            control: The UI control to manage
        """
        self.control = control
        self.app_config = AppConfig()
