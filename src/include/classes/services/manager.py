"""Service manager for registering and managing background services."""

import asyncio
import logging
import threading
from typing import Dict, Optional, Type, TypeVar, overload

from include.classes.services.base import BaseService

_S = TypeVar("_S", bound=BaseService)

__all__ = ["ServiceManager"]


class ServiceManager:
    """
    Singleton service manager for registering and managing background services.

    The ServiceManager provides centralized management of all background services
    in the application. Services can be registered, started, stopped, and queried
    through this manager.

    Attributes:
        services: Dictionary of registered services, keyed by service name
        logger: Logger instance for the service manager
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.services: Dict[str, BaseService] = {}
        self.logger = logging.getLogger("service.manager")
        self._initialized = True

    def register(self, service: BaseService) -> bool:
        """
        Register a new service.

        Args:
            service: The service instance to register

        Returns:
            True if service was registered successfully, False if a service
            with the same name already exists
        """
        if service.name in self.services:
            self.logger.warning(f"Service '{service.name}' is already registered")
            return False

        self.services[service.name] = service
        self.logger.info(f"Registered service '{service.name}'")
        return True

    def unregister(self, service_name: str) -> bool:
        """
        Unregister a service.

        Args:
            service_name: Name of the service to unregister

        Returns:
            True if service was unregistered successfully, False if service
            was not found
        """
        if service_name not in self.services:
            self.logger.warning(f"Service '{service_name}' is not registered")
            return False

        service = self.services[service_name]
        if service.is_running():
            self.logger.warning(
                f"Cannot unregister running service '{service_name}'. "
                "Stop the service first."
            )
            return False

        del self.services[service_name]
        self.logger.info(f"Unregistered service '{service_name}'")
        return True

    @overload
    def get_service(self, service_name: str) -> Optional[BaseService]: ...

    @overload
    def get_service(self, service_name: str, service_type: Type[_S]) -> Optional[_S]: ...

    def get_service(
        self,
        service_name: str,
        service_type: Optional[Type[_S]] = None,
    ) -> Optional[BaseService]:
        """
        Get a registered service by name.

        Args:
            service_name: Name of the service to retrieve
            service_type: Optional type to cast the result to.  When provided
                the return value is typed as ``Optional[service_type]`` so
                callers do not need a separate ``cast()``.  A ``TypeError`` is
                raised at runtime if the found service is not an instance of
                *service_type*.

        Returns:
            The service instance if found, None otherwise

        Raises:
            TypeError: If the found service is not an instance of *service_type*
        """
        service = self.services.get(service_name)
        if service is None or service_type is None:
            return service
        if not isinstance(service, service_type):
            raise TypeError(
                f"Service '{service_name}' is {type(service).__name__}, "
                f"not {service_type.__name__}"
            )
        return service

    async def start_service(self, service_name: str) -> bool:
        """
        Start a registered service.

        Args:
            service_name: Name of the service to start

        Returns:
            True if service started successfully, False otherwise
        """
        service = self.get_service(service_name)
        if not service:
            self.logger.error(f"Service '{service_name}' not found")
            return False

        return await service.start()

    async def stop_service(self, service_name: str) -> bool:
        """
        Stop a running service.

        Args:
            service_name: Name of the service to stop

        Returns:
            True if service stopped successfully, False otherwise
        """
        service = self.get_service(service_name)
        if not service:
            self.logger.error(f"Service '{service_name}' not found")
            return False

        return await service.stop()

    async def restart_service(self, service_name: str) -> bool:
        """
        Restart a service.

        Args:
            service_name: Name of the service to restart

        Returns:
            True if service restarted successfully, False otherwise
        """
        service = self.get_service(service_name)
        if not service:
            self.logger.error(f"Service '{service_name}' not found")
            return False

        return await service.restart()

    async def start_all(self) -> None:
        """Start all registered services."""
        self.logger.info("Starting all registered services")
        for service_name, service in self.services.items():
            try:
                await service.start()
            except Exception as e:
                self.logger.error(
                    f"Failed to start service '{service_name}': {e}", exc_info=True
                )

    async def stop_all(self) -> None:
        """Stop all running services."""
        self.logger.info("Stopping all running services")
        # Create tasks for all stops to run concurrently
        stop_tasks = []
        for service_name, service in self.services.items():
            if service.is_running():
                stop_tasks.append(service.stop())

        # Wait for all services to stop
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

    def get_all_services(self) -> Dict[str, BaseService]:
        """
        Get all registered services.

        Returns:
            Dictionary of all registered services
        """
        return self.services.copy()

    def get_running_services(self) -> Dict[str, BaseService]:
        """
        Get all currently running services.

        Returns:
            Dictionary of running services
        """
        return {
            name: service
            for name, service in self.services.items()
            if service.is_running()
        }
