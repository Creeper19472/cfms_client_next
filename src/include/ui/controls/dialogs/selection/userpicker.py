import flet as ft
from websockets import ClientConnection
from include.classes.config import AppShared
from include.classes.datacls import User
from include.util.locale import get_translation
from include.util.requests import do_request_2

t = get_translation()
_ = t.gettext


class UserPicker(ft.AlertDialog):
    """
    A dialog for picking a user from a list.
    Inherits from flet.AlertDialog and sets up the UI components and page settings.
    """

    def __init__(
        self,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.app_shared = AppShared()
        self.title = ft.Text(_("Select User"))

        self.progress_ring = ft.ProgressRing(visible=False)
        self.user_dropdown = ft.Dropdown(expand=True, expand_loose=True)

        self.content = ft.Column(
            controls=[self.progress_ring, self.user_dropdown],
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.submit_button = ft.TextButton(
            "OK",
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(
            "Cancel",
            on_click=self.cancel_button_click,
        )

        self.actions = [self.submit_button, self.cancel_button]

    def enable_interactions(self):
        self.progress_ring.visible = False
        self.user_dropdown.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.modal = False

    async def get_user_list(self) -> list[User]:
        """
        Retrieves the list of users from the application configuration.

        Returns:
            A list of usernames as strings.
        """

        response = await do_request_2(
            "list_users",
            {},
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        users_data = response.data["users"]

        return [
            User(
                username=user["username"],
                nickname=user["nickname"],
                created_at=user["created_time"],
                last_login=user["last_login"],
                permissions=user["permissions"],
                groups=user["groups"],
            )
            for user in users_data
        ]


    async def pick_user(self) -> str | None:
        """
        Displays the user picker dialog and returns the selected user.

        Returns:
            The selected user as a string, or None if cancelled.
        """

        # Load users from config
        users = self.app_shared.get_users()
        self.user_DropdownOptions = [ft.DropdownOption(user) for user in users]

        # Show dialog
        self.page.dialog = self
        self.open = True

        # Wait for user interaction
        result = await self.page.wait_for_dialog_closed()

        if result == "ok":
            return self.user_dropdown.value
        else:
            return None
