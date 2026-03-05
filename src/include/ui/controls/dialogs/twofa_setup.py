"""Two-Factor Authentication setup dialog."""

import base64
import io

import flet as ft
import qrcode

from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class TwoFactorSetupDialog(AlertDialog):
    """
    Dialog for setting up 2FA with TOTP.

    Displays QR code and secret key for user to scan with authenticator app,
    then verifies with a test code.
    """

    def __init__(
        self,
        secret: str,
        qr_uri: str,
        on_verify_callback=None,
        on_cancel_callback=None,
    ):
        """
        Initialize the 2FA setup dialog.

        Args:
            secret: The TOTP secret key (plaintext for manual entry)
            qr_uri: The otpauth:// URI for QR code generation
            on_verify_callback: Async function to call when user verifies setup
            on_cancel_callback: Async function to call when user cancels
        """
        super().__init__(
            modal=True,
            title=ft.Text(_("Set Up Two-Factor Authentication")),
        )

        self.secret = secret
        self.qr_uri = qr_uri
        self.on_verify_callback = on_verify_callback
        self.on_cancel_callback = on_cancel_callback

        # Generate QR code as base64 image
        qr_image_base64 = self._generate_qr_code(qr_uri)

        # QR code image
        self.qr_image = ft.Image(
            src=qr_image_base64,
            width=200,
            height=200,
            fit=ft.BoxFit.CONTAIN,
        )

        # Secret key display (for manual entry)
        self.secret_text = ft.TextField(
            value=secret,
            read_only=True,
            label=_("Secret Key (manual entry)"),
            text_size=12,
            expand=True,
            expand_loose=True,
            margin=ft.Margin(top=10),
        )

        # Code verification field
        self.code_field = ft.TextField(
            label=_("Enter verification code to confirm"),
            hint_text=_("6-digit code"),
            max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(r"^[0-9]*$"),
            on_submit=self._on_verify_click,
            expand=True,
            expand_loose=True,
        )

        # Buttons
        self.verify_button = ft.TextButton(
            _("Verify and Enable"),
            on_click=self._on_verify_click,
        )

        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self._on_cancel_click,
        )

        self.loading_ring = ft.ProgressRing(visible=False, width=20, height=20)

        # Dialog content
        self.content = ft.Column(
            [
                ft.Text(
                    _(
                        "Scan this QR code with your authenticator app (e.g., Google Authenticator, Authy, Microsoft Authenticator)"
                    ),
                    size=14,
                ),
                ft.Container(
                    content=self.qr_image,
                    alignment=ft.Alignment.CENTER,
                    padding=10,
                ),
                ft.Divider(),
                ft.Text(
                    _("Or enter this key manually:"),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
                self.secret_text,
                ft.Divider(),
                self.code_field,
                ft.Row(
                    [self.loading_ring],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            tight=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [
            self.cancel_button,
            self.verify_button,
        ]

    def _generate_qr_code(self, uri: str) -> str:
        """
        Generate QR code image as base64 string.

        Args:
            uri: The otpauth:// URI to encode

        Returns:
            Base64-encoded PNG image string
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return img_base64

    def disable_interactions(self):
        """Disable all interactive elements."""
        self.code_field.disabled = True
        self.verify_button.disabled = True
        self.cancel_button.disabled = True
        self.loading_ring.visible = True
        self.update()

    def enable_interactions(self):
        """Enable all interactive elements."""
        self.code_field.disabled = False
        self.verify_button.disabled = False
        self.cancel_button.disabled = False
        self.loading_ring.visible = False
        self.update()

    async def _on_verify_click(self, e):
        """Handle verify button click."""
        code = self.code_field.value

        if not code or len(code) != 6:
            self.code_field.error = _("Please enter a 6-digit code")
            self.update()
            return

        self.disable_interactions()

        if self.on_verify_callback:
            success = await self.on_verify_callback(code)
            if success:
                self.close()
            else:
                self.enable_interactions()
                self.code_field.value = ""
                self.code_field.error = _("Invalid code. Please try again.")
                self.update()
        else:
            self.enable_interactions()

    async def _on_cancel_click(self, e):
        """Handle cancel button click."""
        if self.on_cancel_callback:
            await self.on_cancel_callback()
        self.close()
