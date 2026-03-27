"""UI constants for colors, styles, and common text values."""

__all__ = [
    "PRIMARY_COLOR",
    "PLACEHOLDER_COLOR",
    "FIELD_BG",
    "BORDER_COLOR",
    "TEXT_COLOR",
    "ERROR_COLOR",
    "SUCCESS_COLOR",
    "FORM_BORDER_RADIUS",
    "BUTTON_RADIUS",
    "FORM_WIDTH",
    "REMOTE_ADDRESS_PLACEHOLDER",
]


# Color Palette
PRIMARY_COLOR = "#4f46e5"  # Deep indigo for primary actions
PLACEHOLDER_COLOR = "#9ca3af"  # Softer neutral for hint text
FIELD_BG = "#1f2937"  # Dark slate for input fields
BORDER_COLOR = "#374151"  # Neutral border with good contrast
TEXT_COLOR = "#f3f4f6"  # Near-white for clarity
ERROR_COLOR = "#f87171"  # Softer red for errors
SUCCESS_COLOR = "#34d399"  # Minty green for success

# UI Dimensions
FORM_BORDER_RADIUS = 12  # Border radius for forms
BUTTON_RADIUS = 20  # Border radius for buttons
FORM_WIDTH = 380  # Standard form width in pixels

# Placeholder Texts
REMOTE_ADDRESS_PLACEHOLDER = "localhost:5104"
