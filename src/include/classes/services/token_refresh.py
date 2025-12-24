"""Token refresh service for automatic token renewal."""

import time

from include.classes.config import AppShared
from include.classes.services.base import BaseService
from include.util.requests import do_request_2

__all__ = ["TokenRefreshService"]

# Constants for configuration
DEFAULT_CHECK_INTERVAL = 60.0  # Check every minute
DEFAULT_REFRESH_THRESHOLD = 300.0  # Refresh when token expires in 5 minutes


class TokenRefreshService(BaseService):
    """
    Service that periodically checks token expiration and refreshes it.
    
    This service monitors the authentication token's expiration time and
    automatically requests a new token from the server before it expires.
    The refresh is triggered when the remaining time until expiration falls
    below the configured threshold.
    
    Attributes:
        app_shared: Application shared state singleton
        refresh_threshold: Seconds before expiration to trigger refresh
    """
    
    def __init__(
        self,
        enabled: bool = True,
        interval: float = DEFAULT_CHECK_INTERVAL,
        refresh_threshold: float = DEFAULT_REFRESH_THRESHOLD,
    ):
        """
        Initialize the token refresh service.
        
        Args:
            enabled: Whether service is enabled
            interval: Check interval in seconds (default: 60)
            refresh_threshold: Seconds before expiration to refresh (default: 300)
        """
        super().__init__(name="token_refresh", enabled=enabled, interval=interval)
        self.app_shared = AppShared()
        self.refresh_threshold = refresh_threshold
    
    async def on_start(self):
        """Initialize service on start."""
        self.logger.info(
            f"Token refresh service starting with interval: {self.interval}s, "
            f"refresh_threshold: {self.refresh_threshold}s"
        )
    
    async def execute(self):
        """
        Execute token expiration check and refresh if necessary.
        
        This method is called periodically based on the interval setting.
        It checks if the token is about to expire and requests a new one.
        """
        # Check if user is logged in
        if not self.app_shared.token or not self.app_shared.username:
            self.logger.debug("No active session, skipping token refresh check")
            return
        
        # Check if token expiration time is set
        if not self.app_shared.token_exp:
            self.logger.warning("Token expiration time not set, cannot check expiration")
            return
        
        # Calculate remaining time until expiration
        current_time = time.time()
        time_until_expiry = self.app_shared.token_exp - current_time
        
        self.logger.debug(
            f"Token expires in {time_until_expiry:.1f} seconds "
            f"(threshold: {self.refresh_threshold}s)"
        )
        
        # Check if token needs refresh or is already expired
        if time_until_expiry <= 0:
            self.logger.warning(
                f"Token has already expired ({time_until_expiry:.1f}s ago), "
                "clearing session and skipping refresh"
            )
            # Clear session so subsequent checks do not try to refresh with invalid credentials
            self.app_shared.token = None
            self.app_shared.token_exp = None
            return
        elif time_until_expiry <= self.refresh_threshold:
            self.logger.info(
                f"Token expiring soon ({time_until_expiry:.1f}s remaining), "
                "requesting refresh"
            )
            await self._refresh_token()
        else:
            self.logger.debug(
                f"Token still valid for {time_until_expiry:.1f}s, no refresh needed"
            )
    
    async def _refresh_token(self):
        """
        Request a new token from the server.
        
        Sends a refresh_token request to the server with the current
        username and token. Updates the app_shared state with the new
        token and expiration time.
        """
        try:
            # Make refresh_token request
            # The request automatically includes username and token from app_shared
            response = await do_request_2(
                action="refresh_token",
                data={},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )
            
            if response.code == 200:
                # Extract new token and expiration from response
                new_token = response.data.get("token")
                new_exp = response.data.get("exp")
                
                if new_token and new_exp:
                    # Update app_shared with new credentials
                    self.app_shared.token = new_token
                    self.app_shared.token_exp = new_exp
                    
                    self.logger.info(
                        f"Token refreshed successfully. "
                        f"New expiration: {new_exp} "
                        f"(in {new_exp - time.time():.1f} seconds)"
                    )
                else:
                    self.logger.error(
                        "Token refresh response missing required fields "
                        f"(token: {new_token is not None}, exp: {new_exp is not None})"
                    )
            else:
                self.logger.error(
                    f"Token refresh failed: ({response.code}) {response.message}"
                )

                # If the failure is due to authentication issues, invalidate the session
                if response.code in (401, 403):
                    self.logger.warning(
                        "Token refresh failed due to authentication error "
                        "(session may have expired or token is invalid). "
                        "Clearing session and stopping further refresh attempts "
                        "until re-authentication."
                    )
                    # Clear token-related state so execute() will skip future refreshes
                    self.app_shared.token = None
                    self.app_shared.token_exp = None
                    self.app_shared.username = None
                
        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}", exc_info=True)
    
    async def on_error(self, error: Exception):
        """
        Handle errors during execution.
        
        Args:
            error: The exception that occurred
        """
        self.logger.error(
            f"Token refresh service encountered an error: {error}",
            exc_info=True
        )
