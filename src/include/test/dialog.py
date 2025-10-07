import flet as ft


class AlertDialogTesting(ft.AlertDialog):
    def __init__(
        self,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            ref=ref,
        )
        self.title = "AlertDialog Example for Testing"
        self.content = ft.Text("Hello, World!")
        self.actions = [ft.TextButton("Open New Dialog", on_click=self.open_button_click)]

    async def open_button_click(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()
        self.page.show_dialog(AlertDialogTesting()) # will fail randomly


async def main(page: ft.Page):
    page.show_dialog(AlertDialogTesting())


if __name__ == "__main__":
    ft.run(main)
