"""Declarative settings framework for CFMS Client NEXT.

This module provides base classes and utilities for defining settings pages
declaratively, with automatic UI control generation, load/save handling,
dependency management, and auto-registration in the Settings Overview.

Basic usage (declarative)::

    from include.ui.frameworks.settings import (
        DeclarativeSettingsPage, SettingsField, SectionHeader, Separator,
        HelpText, settings_page,
    )
    from flet_model import route

    @settings_page
    @route("my_settings")
    class MySettingsModel(DeclarativeSettingsPage):
        # Overview metadata
        settings_name = _("My Settings")
        settings_description = _("Configure my settings")
        settings_icon = Symbols.SETTINGS
        settings_route_suffix = "my_settings"

        # Declarative fields with section headers and separators
        _general_header = SectionHeader(_("General"))
        enable_feature: SettingsField[bool] = SettingsField(label=_("Enable feature"))
        feature_value: SettingsField[str] = SettingsField(
            label=_("Feature value"),
            depends_on="enable_feature",
        )
        _divider = Separator()
        _advanced_header = SectionHeader(_("Advanced"))
        advanced_option: SettingsField[str] = SettingsField(label=_("Advanced option"))

Non-declarative (existing complex) pages can still register for Overview
auto-population by mixing in :class:`RegisteredSettingsPage`::

    @settings_page
    @route("complex_settings")
    class ComplexSettingsModel(Model, RegisteredSettingsPage):
        settings_name = _("Complex Settings")
        settings_description = _("Complex configuration")
        settings_icon = Symbols.SETTINGS
        settings_route_suffix = "complex_settings"
        ...
"""

from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    TypeVar,
    get_args,
    get_type_hints,
    overload,
)

import flet as ft
from flet_material_symbols import Symbols
from flet_model import Model, Router

from include.classes.shared import AppShared
from .enum import BrowseMode
from include.ui.util.notifications import send_success
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

_T = TypeVar("_T")

__all__ = [
    "SettingsField",
    "SectionHeader",
    "Separator",
    "HelpText",
    "RegisteredSettingsPage",
    "DeclarativeSettingsPage",
    "DeclarativeActionPage",
    "settings_page",
    "get_settings_registry",
]

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_settings_registry: list[type[RegisteredSettingsPage]] = []


def settings_page(cls: type) -> type:
    """Class decorator that registers a settings page in the global Overview registry.

    Apply this decorator *after* ``@route()`` so that the class is fully
    constructed before registration::

        @settings_page
        @route("my_settings")
        class MySettingsModel(DeclarativeSettingsPage):
            ...
    """
    _settings_registry.append(cls)
    return cls


def get_settings_registry() -> list[type[RegisteredSettingsPage]]:
    """Return all settings pages registered with ``@settings_page``, in order."""
    return list(_settings_registry)


# ---------------------------------------------------------------------------
# RegisteredSettingsPage – lightweight mixin for Overview metadata
# ---------------------------------------------------------------------------


class RegisteredSettingsPage:
    """Mixin that declares the class-level attributes required for Overview
    auto-population.

    Both :class:`DeclarativeSettingsPage` and existing ``Model``-based
    settings pages can use this mixin together with the
    :func:`settings_page` decorator.

    Class-level attributes to define in each subclass:

    settings_name (str):
        Title shown in the Overview list tile (used as a translation key).
    settings_description (str):
        Subtitle shown in the Overview list tile (used as a translation key).
    settings_icon (str):
        ``ft.Icons`` constant for the Overview list tile icon.
    settings_route_suffix (str):
        Route segment appended to the current route when navigating
        (must match the argument passed to ``@route()``).
    """

    settings_name: ClassVar[str] = ""
    settings_description: ClassVar[str] = ""
    settings_icon: ClassVar[ft.IconData] = Symbols.SETTINGS
    settings_route_suffix: ClassVar[str] = ""


# ---------------------------------------------------------------------------
# SettingsField – declarative field descriptor
# ---------------------------------------------------------------------------


class SettingsField(Generic[_T]):
    """Declarative descriptor for a single settings field.

    Declare as a class attribute with a type annotation to define a settings
    field.  The Python type annotation determines which Flet control is used:

    * ``bool``  → ``ft.Switch``
    * ``str``   → ``ft.TextField``  (or ``ft.Dropdown`` when *options* is given)

    String arguments (*label*, *hint_text*, *description*, and option display
    texts) are stored and returned as-is.  **Always pass them through ``_()``
    at the call site** so that :mod:`pygettext` / :mod:`xgettext` can extract
    the string literals for translation::

        t = get_translation()
        _ = t.gettext

        class MyPage(DeclarativeSettingsPage):
            field: SettingsField[str] = SettingsField(
                label=_("My label"),
                description=_("Help text."),
            )

    When deferred (per-render) translation is required — for example when the
    locale can change at runtime — pass a zero-argument callable instead::

        field: SettingsField[str] = SettingsField(
            label=lambda: _("My label"),
        )

    Parameters
    ----------
    label:
        Human-readable label.  Pass an already-translated string
        (``_("...")``) or a zero-argument callable for deferred evaluation.
    key:
        Key used in ``app_shared.preferences[settings_pref_section]``.
        Defaults to the attribute name.
    default:
        Default value when the key is absent from preferences.
    hint_text:
        Placeholder / hint text for text fields and dropdowns.
        Same convention as *label*.
    options:
        List of ``(config_value, display_text)`` tuples.  When provided, a
        ``ft.Dropdown`` is used regardless of the annotation type.
        Pass display texts as ``_("...")`` strings or use a callable.
        A callable returning such a list is also accepted.
    description:
        Optional help text rendered below the control (or below the row when
        ``row_id`` is used).  Same convention as *label*.
    depends_on:
        One or more dependency specifications.  Accepts:

        * A single attribute name as a plain string — the control is disabled
          when that field's value is falsy (the existing behaviour).
        * A ``!``-prefixed attribute name (e.g. ``"!follow_system_proxy"``) —
          the control is disabled when that field's value is *truthy*.
        * A list combining any of the above — the control is disabled when
          **any** condition in the list is met.

        Example::

            # disabled when enable_proxy is False OR follow_system_proxy is True
            depends_on=["enable_proxy", "!follow_system_proxy"]

    persist:
        When ``False`` the field is *not* automatically loaded from or saved to
        preferences.  Use this for UI-only derived fields whose underlying
        preference key has a different shape (e.g. a proxy-enable toggle that
        is derived from the raw ``proxy_settings`` value rather than stored
        directly).  Override :meth:`DeclarativeSettingsPage._on_load` and
        :meth:`DeclarativeSettingsPage._on_save` to handle the translation
        between stored values and the UI fields.  Defaults to ``True``.
    row_id:
        Arbitrary grouping key.  Fields sharing the same ``row_id`` are
        placed inside a single ``ft.Row`` in declaration order.
    expand:
        Whether the control should expand to fill available horizontal space
        (passed as ``expand`` / ``expand_loose`` on the Flet control).
        Defaults to ``True``.
    disabled:
        Whether the control should be permanently disabled.  Defaults to
        ``False``.
    option_descriptions:
        Mapping from option key to a short description string shown *below*
        the dropdown when that option is selected.  Only meaningful for
        dropdown fields (i.e. when *options* is also provided).  Pass an
        already-translated dict (``{key: _("...")}``) or a zero-argument
        callable returning such a dict for deferred evaluation.  When the
        current selection has no entry, the description area is cleared.
    browse:
        When not ``BrowseMode.OFF`` on a ``SettingsField[str]`` field, a
        ``Browse...`` button is rendered to the right of the text field.
        Pressing it opens a directory-picker dialog when ``browse`` is
        ``BrowseMode.DIRECTORY`` or a file-picker dialog when ``browse`` is
        ``BrowseMode.FILE``, and inserts the chosen path into the text field.
        The button inherits the same disabled state as the text field (from
        ``depends_on``).  Defaults to ``BrowseMode.OFF``.
    """

    def __init__(
        self,
        label: str | Callable[[], str],
        *,
        key: str | None = None,
        default: Any = None,
        hint_text: str | Callable[[], str] = "",
        options: (
            list[tuple[str, str]] | Callable[[], list[tuple[str, str]]] | None
        ) = None,
        description: str | Callable[[], str] | None = None,
        depends_on: str | list[str] | None = None,
        row_id: str | None = None,
        expand: bool = True,
        disabled: bool = False,
        persist: bool = True,
        option_descriptions: (
            dict[str, str] | Callable[[], dict[str, str]] | None
        ) = None,
        browse: BrowseMode = BrowseMode.OFF,
    ) -> None:
        self._label = label
        self.key = key
        self.default = default
        self._hint_text = hint_text
        self._options = options
        self._description = description
        self.depends_on = depends_on
        self.row_id = row_id
        self.expand = expand
        self.disabled = disabled
        self.persist = persist
        self._option_descriptions = option_descriptions
        self.browse = browse
        # _attr_name is set by __set_name__ when the class body is processed.
        # It is initialised here so that the attribute always exists, even for
        # SettingsField instances that are constructed outside a class body
        # (e.g. in tests).
        self._attr_name: str = ""

    # ------------------------------------------------------------------
    # Descriptor protocol
    # ------------------------------------------------------------------

    def __set_name__(self, owner: type, name: str) -> None:
        """Called by Python when the owning class body is processed.

        This is the SQLAlchemy-style pattern: Python automatically informs
        every descriptor of the attribute name it was assigned to, so no
        external mutation (``field._attr_name = name``) is needed.
        """
        self._attr_name = name
        # If no explicit key was provided, use the attribute name as the
        # preferences key (mirrors how SQLAlchemy column names default to the
        # attribute name).
        if self.key is None:
            self.key = name

    @overload
    def __get__(self, obj: None, objtype: Any) -> "SettingsField[_T]": ...
    @overload
    def __get__(self, obj: Any, objtype: Any) -> _T: ...
    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        """Descriptor protocol getter.

        * Class-level access (``obj is None``) returns the :class:`SettingsField`
          itself, so the field can be inspected from the class (e.g. in
          :meth:`DeclarativeSettingsPage._collect_fields`).
        * Instance-level access returns the *current value* held by the
          corresponding Flet control, just as SQLAlchemy columns return the
          mapped attribute value on a model instance.
        """
        if obj is None:
            return self
        control = getattr(obj, "_control_map", {}).get(self._attr_name)
        if control is None:
            return self.default
        return _read_control_value(control)

    def __set__(self, obj: Any, value: _T) -> None:
        """Descriptor protocol setter.

        Writes *value* to the underlying Flet control on *obj*, mirroring how
        SQLAlchemy mapped attributes propagate assignments to the instance state.
        """
        control = getattr(obj, "_control_map", {}).get(self._attr_name)
        if control is not None:
            _apply_value_to_control(control, value)

    # ------------------------------------------------------------------
    # Lazy-translation properties
    # ------------------------------------------------------------------

    @property
    def label(self) -> str:
        return self._label() if callable(self._label) else self._label

    @property
    def hint_text(self) -> str:
        return self._hint_text() if callable(self._hint_text) else self._hint_text

    @property
    def description(self) -> str | None:
        if self._description is None:
            return None
        return self._description() if callable(self._description) else self._description

    @property
    def options(self) -> list[tuple[str, str]] | None:
        if self._options is None:
            return None
        opts = self._options() if callable(self._options) else self._options
        # Return a shallow copy so callers cannot mutate the stored list.
        return list(opts)

    @property
    def option_descriptions(self) -> dict[str, str] | None:
        """Mapping of option key → description string (evaluated lazily)."""
        if self._option_descriptions is None:
            return None
        descs = (
            self._option_descriptions()
            if callable(self._option_descriptions)
            else self._option_descriptions
        )
        return dict(descs)

    @property
    def config_key(self) -> str:
        """Config key in preferences (defaults to the attribute name)."""
        return self.key if self.key is not None else self._attr_name

    # ------------------------------------------------------------------
    # Control factory
    # ------------------------------------------------------------------

    def build_control(self, field_type: type) -> ft.Control:
        """Instantiate and return a fresh Flet control for this field.

        Parameters
        ----------
        field_type:
            The Python type from the class annotation (``bool``, ``str``, ...).
        """
        opts = self.options
        if field_type is bool:
            return ft.Switch(
                label=self.label,
                disabled=self.disabled,
            )
        elif opts is not None:
            return ft.Dropdown(
                label=self.label,
                hint_text=self.hint_text or None,
                options=[ft.DropdownOption(key=k, text=text) for k, text in opts],
                expand=self.expand,
                expand_loose=True,
                disabled=self.disabled,
            )
        else:
            return ft.TextField(
                label=self.label,
                hint_text=self.hint_text or None,
                expand=self.expand,
                expand_loose=True,
                disabled=self.disabled,
                margin=ft.Margin(top=5),
            )


# ---------------------------------------------------------------------------
# SectionHeader – declarative section heading
# ---------------------------------------------------------------------------


class SectionHeader:
    """A declarative section header for settings pages.

    Declare as a class attribute (without type annotation) to render a
    section heading between settings fields::

        class MyPage(DeclarativeSettingsPage):
            _network_header = SectionHeader(_("Network"))
            proxy_enabled: SettingsField[bool] = SettingsField(label=_("Enable proxy"))

    String arguments are stored and returned as-is.  **Always pass them
    through ``_()`` at the call site** so that translatable strings can be
    extracted::

        _section = SectionHeader(_("My Section"))

    A zero-argument callable is also accepted for deferred evaluation::

        _section = SectionHeader(lambda: _("My Section"))

    Parameters
    ----------
    title:
        Section heading text.  Pass an already-translated string
        (``_("...")``) or a zero-argument callable for deferred evaluation.
    """

    def __init__(self, title: str | Callable[[], str]) -> None:
        self._title = title
        # Set by __set_name__ when the owning class body is processed.
        self._attr_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    @property
    def title(self) -> str:
        return self._title() if callable(self._title) else self._title

    def build_control(self) -> ft.Control:
        """Return a styled ``ft.Text`` for this section header."""
        return ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD)


# ---------------------------------------------------------------------------
# Separator – declarative horizontal divider
# ---------------------------------------------------------------------------


class Separator:
    """A declarative horizontal separator for settings pages.

    Declare as a class attribute (without type annotation) to render a
    horizontal divider between settings fields or sections::

        class MyPage(DeclarativeSettingsPage):
            first_field: SettingsField[bool] = SettingsField(label=_("First"))
            _divider = Separator()
            second_field: SettingsField[str] = SettingsField(label=_("Second"))

    Parameters
    ----------
    thickness:
        Divider thickness in logical pixels.  Defaults to ``1``.
    color:
        Divider color expressed as a Flet/CSS colour string or
        ``ft.Colors`` constant.  Defaults to ``None`` (theme default).
    """

    def __init__(
        self,
        *,
        thickness: float = 1,
        color: str | None = None,
    ) -> None:
        self.thickness = thickness
        self.color = color
        # Set by __set_name__ when the owning class body is processed.
        self._attr_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    def build_control(self) -> ft.Control:
        """Return a ``ft.Divider`` for this separator."""
        return ft.Divider(thickness=self.thickness, color=self.color)


# ---------------------------------------------------------------------------
# HelpText – declarative paragraph of help/description text
# ---------------------------------------------------------------------------


class HelpText:
    """A declarative paragraph of help or description text for settings pages.

    Declare as a class attribute (without a type annotation) to render a
    block of informational text between settings fields::

        class MyPage(DeclarativeSettingsPage):
            _proxy_header = SectionHeader(_("Proxy"))
            _proxy_help = HelpText(
                _("Configure a proxy server for outbound connections."),
            )
            proxy_host: SettingsField[str] = SettingsField(label=_("Host"))

    String arguments are stored and returned as-is.  **Always pass them
    through ``_()`` at the call site** so that translatable strings can be
    extracted::

        _help = HelpText(_("Some helpful information."))

    A zero-argument callable is also accepted for deferred evaluation::

        _help = HelpText(lambda: _("Some helpful information."))

    Parameters
    ----------
    text:
        Paragraph text.  Pass an already-translated string (``_("...")``)
        or a zero-argument callable for deferred evaluation.
    size:
        Font size in logical pixels.  Defaults to ``13``.
    color:
        Text color expressed as a Flet/CSS colour string or
        ``ft.Colors`` constant.  Defaults to ``None`` (theme default).
    """

    def __init__(
        self,
        text: str | Callable[[], str],
        *,
        size: int = 13,
        color: str | None = None,
    ) -> None:
        self._text = text
        self.size = size
        self.color = color
        # Set by __set_name__ when the owning class body is processed.
        self._attr_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    @property
    def text(self) -> str:
        return self._text() if callable(self._text) else self._text

    def build_control(self) -> ft.Control:
        """Return a ``ft.Text`` for this help paragraph."""
        return ft.Text(self.text, size=self.size, color=self.color)


# ---------------------------------------------------------------------------
# DeclarativeSettingsPage – base Model for declarative settings pages
# ---------------------------------------------------------------------------


class DeclarativeSettingsPage(Model, RegisteredSettingsPage):
    """Base class for declarative settings pages.

    Subclasses declare settings fields as annotated class attributes using
    :class:`SettingsField`.  The framework automatically:

    * Generates Flet controls from type annotations.
    * Loads values from ``app_shared.preferences[settings_pref_section]`` on
      mount.
    * Saves values back on the Save button press.
    * Disables dependent controls based on ``depends_on`` relationships.
    * Groups controls that share the same ``row_id`` into ``ft.Row``\\s.

    Additional class-level attributes:

    settings_pref_section (str):
        Top-level key in the ``preferences`` dict.  Defaults to
        ``"settings"``.

    Override :meth:`_on_save` for custom save logic (it is called *after* the
    automatic field saving).
    Override :meth:`_on_load` for extra loading steps (called after automatic
    value loading).  :meth:`_on_save` may return a custom success-message
    string; if it does, it replaces the default ``"Settings Saved."``
    notification.
    """

    settings_pref_section: ClassVar[str] = "settings"

    # Shared layout defaults (consistent with the existing settings pages)
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router) -> None:
        super().__init__(page, router)
        self.app_shared = AppShared()

        self.appbar = ft.AppBar(
            title=ft.Text(type(self).settings_name),
            leading=ft.IconButton(icon=Symbols.ARROW_BACK, on_click=self._go_back),
            actions=[
                ft.IconButton(
                    ft.Icon(Symbols.SAVE, fill=1), on_click=self._save_button_click
                )
            ],
            actions_padding=10,
        )

        # Introspect fields, build controls, wire dependencies.
        self._fields = self._collect_fields()
        self._control_map: dict[str, ft.Control] = {}
        # Maps attr_name → ft.Text for option-specific descriptions.
        self._option_desc_controls: dict[str, ft.Text] = {}
        # Maps attr_name → ft.Button for browse-path buttons.
        self._browse_button_map: dict[str, ft.Button] = {}
        self.controls = self._build_controls()

    # ------------------------------------------------------------------
    # Field introspection
    # ------------------------------------------------------------------

    def _collect_fields(
        self,
    ) -> list[
        tuple[str, "SettingsField | SectionHeader | Separator | HelpText", type | None]
    ]:
        """Return items in declaration order.

        Each element is a triple ``(attr_name, item, python_type)`` where
        *item* is a :class:`SettingsField`, :class:`SectionHeader`,
        :class:`Separator`, or :class:`HelpText` instance.
        *python_type* is ``None`` for :class:`SectionHeader`,
        :class:`Separator`, and :class:`HelpText`.

        The class ``__dict__`` is walked (not just ``__annotations__``) so that
        unannotated descriptors such as :class:`SectionHeader`,
        :class:`Separator`, and :class:`HelpText` are discovered alongside
        annotated :class:`SettingsField` entries, all in their original
        declaration order.
        The MRO is traversed in reverse so that base-class items appear before
        subclass items.
        """
        cls = type(self)
        try:
            hints = get_type_hints(cls)
        except Exception:
            hints = {}

        result: list[
            tuple[
                str, SettingsField | SectionHeader | Separator | HelpText, type | None
            ]
        ] = []
        # cls.__annotations__ preserves declaration order (Python 3.7+) and
        # only contains annotations defined directly on cls (not inherited ones).
        # We walk the MRO to support field inheritance in subclasses.
        seen: set[str] = set()
        for klass in reversed(cls.__mro__):
            # klass.__dict__ is an ordered mapping (guaranteed since Python 3.7)
            # that contains both annotated and unannotated class attributes in
            # their declaration order.  This lets us discover SectionHeader /
            # Separator instances (which have no type annotation) interleaved
            # with SettingsField entries while preserving the visual order
            # defined in the class body.
            for attr_name, value in klass.__dict__.items():
                if attr_name in seen:
                    continue

                # Only reserve the name in `seen` once we know `value` is a
                # framework item.  Regular methods, class constants, or other
                # non-framework attributes in base classes must *not* block a
                # subclass from declaring a SettingsField (or layout item) with
                # the same name; silently dropping such a field would be hard to
                # debug.  We still prevent the same framework-item name from
                # being collected twice (e.g. inherited then re-declared).
                if isinstance(value, (SectionHeader, Separator, HelpText)):
                    seen.add(attr_name)
                    result.append((attr_name, value, None))
                elif isinstance(value, SettingsField):
                    seen.add(attr_name)
                    ann = getattr(klass, "__annotations__", {})
                    # Prefer the fully-resolved hint from get_type_hints; fall
                    # back to the raw annotation object.
                    hint = hints.get(attr_name) or ann.get(attr_name)
                    # Support both the canonical SettingsField[T] annotation
                    # and legacy bare type annotations (str, bool, ...) for
                    # backward compatibility.
                    origin = getattr(hint, "__origin__", None)
                    if origin is SettingsField:
                        # SettingsField[T] — extract the inner type T.
                        args = get_args(hint)
                        if not args:
                            raise TypeError(
                                f"{cls.__qualname__}.{attr_name}: "
                                "SettingsField must be parameterised with a type, "
                                "e.g. SettingsField[bool] or SettingsField[str]."
                            )
                        field_type: type = args[0]
                    elif isinstance(hint, type) and not issubclass(hint, SettingsField):
                        # Legacy bare annotation e.g.
                        # `name: str = SettingsField(...)`
                        # The `issubclass` guard prevents using the bare
                        # SettingsField class itself as the field_type.
                        field_type = hint
                    else:
                        field_type = str
                    result.append((attr_name, value, field_type))
        return result

    # ------------------------------------------------------------------
    # Control building
    # ------------------------------------------------------------------

    def _build_controls(self) -> list[ft.Control]:
        """Build the list of Flet controls from the collected field definitions.

        Controls that share the same ``row_id`` are placed inside a single
        ``ft.Row``.  An optional description text is appended immediately
        after each standalone control or row.

        Extra layout rules for special field parameters:

        * ``browse=True`` — the text field and a *Browse...* button are wrapped
          in a ``ft.Row``.  The button is stored in :attr:`_browse_button_map`
          so its disabled state can be updated by :meth:`_flush_dependencies`.
        * ``option_descriptions`` — a ``ft.Text`` is added immediately below
          the dropdown control and stored in :attr:`_option_desc_controls`.
          It is updated whenever the dropdown selection changes.
        """
        controls: list[ft.Control] = []

        # State for the current pending row group
        pending_row_id: str | None = None
        pending_row_controls: list[ft.Control] = []
        pending_row_description: str | None = None
        # option-description texts belonging to fields in the current row group
        pending_option_desc_controls: list[ft.Text] = []

        def flush_pending_row() -> None:
            nonlocal pending_row_id, pending_row_controls, pending_row_description, pending_option_desc_controls
            if pending_row_controls:
                controls.append(ft.Row(controls=pending_row_controls))
                if pending_row_description is not None:
                    controls.append(
                        ft.Text(
                            pending_row_description,
                            size=12,
                            color=ft.Colors.GREY,
                        )
                    )
                # Emit any option-description texts from fields in this row group.
                for opt_desc in pending_option_desc_controls:
                    controls.append(opt_desc)
            pending_row_id = None
            pending_row_controls = []
            pending_row_description = None
            pending_option_desc_controls = []

        for attr_name, field, field_type in self._fields:
            # Section headers, separators and help-text are rendered directly
            # and never participate in row groups, dependency tracking, or
            # persistence.
            if isinstance(field, (SectionHeader, Separator, HelpText)):
                flush_pending_row()
                controls.append(field.build_control())
                continue

            # field_type is always set for SettingsField entries; the SectionHeader,
            # Separator, and HelpText branches above handle the None cases and continue.
            assert field_type is not None
            control = field.build_control(field_type)

            # Wire switch-change handler for automatic dependency flushing.
            if isinstance(control, ft.Switch):
                control.on_change = self._on_switch_change

            # Wire dropdown change handler when option_descriptions is set.
            if (
                isinstance(control, ft.Dropdown)
                and field.option_descriptions is not None
            ):
                control.on_select = self._on_dropdown_select
                desc_text = ft.Text(
                    "",
                    size=14,
                    color=ft.Colors.GREY,
                    expand=True,
                    expand_loose=True,
                )
                self._option_desc_controls[attr_name] = desc_text

            self._control_map[attr_name] = control

            # For browse fields, wrap the TextField in a Row with a Browse button.
            if field.browse and isinstance(control, ft.TextField):
                browse_btn = ft.Button(
                    _("Browse..."),
                    on_click=self._make_browse_handler(attr_name, field.browse),
                    disabled=field.disabled,
                )
                self._browse_button_map[attr_name] = browse_btn
                layout_control: ft.Control = ft.Row([control, browse_btn])
            else:
                layout_control = control

            if field.row_id is not None:
                if field.row_id != pending_row_id:
                    # Starting a new row group – flush the previous one first
                    flush_pending_row()
                    pending_row_id = field.row_id
                pending_row_controls.append(layout_control)
                # Keep the last non-None description within the row group
                if field.description is not None:
                    pending_row_description = field.description
                # Accumulate any option-description text for this field so that
                # flush_pending_row can emit it after the row widget.
                if attr_name in self._option_desc_controls:
                    pending_option_desc_controls.append(
                        self._option_desc_controls[attr_name]
                    )
            else:
                # Standalone control – flush any pending row first
                flush_pending_row()
                controls.append(layout_control)
                if field.description is not None:
                    controls.append(
                        ft.Text(
                            field.description,
                            size=12,
                            color=ft.Colors.GREY,
                        )
                    )
                # Option-descriptions text sits right below the dropdown.
                if attr_name in self._option_desc_controls:
                    controls.append(self._option_desc_controls[attr_name])

        # Flush any remaining pending row
        flush_pending_row()
        return controls

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self._load_values)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    async def _load_values(self) -> None:
        """Load all field values from preferences and refresh the UI."""
        section: dict[str, Any] = self.app_shared.preferences.get(
            type(self).settings_pref_section, {}
        )
        for attr_name, field, _ftype in self._fields:
            if not isinstance(field, SettingsField):
                continue
            if not field.persist:
                continue
            value = section.get(field.config_key, field.default)
            # Use the descriptor __set__ to write the value onto the control.
            setattr(self, attr_name, value)

        await self._on_load()
        # Refresh all option-description texts after values have been loaded.
        for attr_name in self._option_desc_controls:
            self._refresh_option_description(attr_name)
        await self._flush_dependencies()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    async def _save_button_click(self, event: ft.Event[ft.IconButton]) -> None:
        """Handle Save button press: persist all field values and notify."""
        section: dict[str, Any] = self.app_shared.preferences.setdefault(
            type(self).settings_pref_section, {}
        )
        for attr_name, field, _ftype in self._fields:
            if not isinstance(field, SettingsField):
                continue
            if not field.persist:
                continue
            # Use the descriptor __get__ to read the current control value.
            section[field.config_key] = getattr(self, attr_name)

        # Call the hook *before* dumping so that it can modify preferences
        # (e.g. translate UI-only fields into the stored representation).
        custom_message = await self._on_save()
        self.app_shared.dump_preferences()
        send_success(self.page, custom_message or _("Settings Saved."))

    # ------------------------------------------------------------------
    # Dependency management
    # ------------------------------------------------------------------

    async def _flush_dependencies(self) -> None:
        """Update the *disabled* state of controls with a ``depends_on``
        relationship.

        Each dependency specification is evaluated as follows:

        * Plain name (e.g. ``"enable_proxy"``) — the control is disabled when
          that field's value is falsy.
        * ``!``-prefixed name (e.g. ``"!follow_system_proxy"``) — the control
          is disabled when that field's value is *truthy*.

        When ``depends_on`` is a list, the control is disabled as soon as
        **any** condition in the list is met.  Permanently-disabled fields
        (``SettingsField.disabled is True``) are never re-enabled.
        """
        for attr_name, field, _ftype in self._fields:
            if not isinstance(field, SettingsField):
                continue
            if field.depends_on is None or field.disabled:
                continue
            control = self._control_map.get(attr_name)
            if control is None:
                continue
            specs = (
                field.depends_on
                if isinstance(field.depends_on, list)
                else [field.depends_on]
            )
            should_disable = False
            for spec in specs:
                if not isinstance(spec, str):
                    continue
                if spec.startswith("!"):
                    dep_value = getattr(self, spec[1:])
                    if bool(dep_value):
                        should_disable = True
                        break
                else:
                    dep_value = getattr(self, spec)
                    if not bool(dep_value):
                        should_disable = True
                        break
            control.disabled = should_disable
            # If this field also has a browse button, keep it in sync.
            browse_btn = self._browse_button_map.get(attr_name)
            if browse_btn is not None:
                browse_btn.disabled = should_disable
        self.update()

    async def _on_switch_change(self, event: ft.Event[ft.Switch]) -> None:
        """Called when any ``ft.Switch`` in this page changes.

        The default implementation refreshes the disabled state of all
        dependent controls via :meth:`_flush_dependencies`.  Override to
        add extra behaviour (e.g. requesting permissions) — call
        ``await super()._on_switch_change(event)`` to keep the default
        logic::

            async def _on_switch_change(self, event):
                if self.my_switch and needs_permission():
                    self.page.show_dialog(PermissionDialog())
                await super()._on_switch_change(event)
        """
        await self._flush_dependencies()

    async def _on_dropdown_select(self, event: ft.Event[ft.Dropdown]) -> None:
        """Called when any ``ft.Dropdown`` with ``option_descriptions`` changes.

        Refreshes the description text for the changed dropdown.
        """
        changed_control = event.control
        for attr_name, mapped_control in self._control_map.items():
            if mapped_control is changed_control:
                self._refresh_option_description(attr_name)
                break
        self.update()

    def _refresh_option_description(self, attr_name: str) -> None:
        """Update the option-description ``ft.Text`` for *attr_name*.

        Reads the current dropdown value and looks it up in the field's
        ``option_descriptions`` mapping.  Sets the text to ``""`` when the
        value has no entry.
        """
        desc_text = self._option_desc_controls.get(attr_name)
        if desc_text is None:
            return
        field = getattr(type(self), attr_name, None)
        if not isinstance(field, SettingsField):
            return
        descs = field.option_descriptions
        if descs is None:
            return
        control = self._control_map.get(attr_name)
        value = _read_control_value(control) if control is not None else ""
        desc_text.value = descs.get(value or "", "")

    def _make_browse_handler(self, attr_name: str, mode: BrowseMode):
        """Return an async click handler that opens a directory picker for *attr_name*."""

        async def _handler(event: ft.Event[ft.Button]) -> None:
            match mode:
                case BrowseMode.DIRECTORY:
                    storage_path = await ft.FilePicker().get_directory_path()
                case BrowseMode.FILE:
                    result = await ft.FilePicker().pick_files()
                    storage_path = result[0].path if result else ""
                case _:
                    raise ValueError(f"Unsupported BrowseMode: {mode}")

            if storage_path:
                control = self._control_map.get(attr_name)
                if control is not None:
                    _apply_value_to_control(control, storage_path)
                    self.update()

        return _handler

    # ------------------------------------------------------------------
    # Override hooks
    # ------------------------------------------------------------------

    async def _on_save(self) -> str | None:
        """Called *after* automatic field saving.

        Override to add custom save logic (e.g. applying a new language).

        Returns
        -------
        str | None
            A custom success message to display, or ``None`` to use the
            default ``"Settings Saved."`` notification.
        """
        return None

    async def _on_load(self) -> None:
        """Called *after* automatic value loading.

        Override to perform additional initialization steps.
        """

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def _go_back(self, event: ft.Event[ft.IconButton]) -> None:
        await self.page.push_route(get_parent_route(self.page.route))


# ---------------------------------------------------------------------------
# DeclarativeActionPage – base Model for action-based settings pages
# ---------------------------------------------------------------------------


class DeclarativeActionPage(Model, RegisteredSettingsPage):
    """Base class for action-based settings pages.

    Use this base class for settings pages that *perform operations* rather
    than editing stored preferences — for example: Two-Factor Authentication
    management, password changes, or account linking.  Unlike
    :class:`DeclarativeSettingsPage`, this class:

    * Does **not** declare :class:`SettingsField` attributes.
    * Has **no** Save button in the AppBar (only a back arrow).
    * Calls ``page.run_task(self._on_load)`` in :meth:`did_mount` so
      subclasses only need to override :meth:`_on_load` for async
      initialization.

    Subclasses should:

    1. Call ``super().__init__(page, router)`` to set up ``self.app_shared``
       and the AppBar.
    2. Build their own controls in ``__init__`` and assign to
       ``self.controls``.
    3. Override :meth:`_on_load` for any async initialization (e.g. a
       server status fetch).

    Example::

        @settings_page
        @route("password_settings")
        class PasswordSettingsModel(DeclarativeActionPage):
            settings_name = _("Change Password")
            settings_description = _("Update your account password")
            settings_icon = Symbols.LOCK
            settings_route_suffix = "password_settings"

            def __init__(self, page, router):
                super().__init__(page, router)
                self.change_btn = ft.Button(_("Change..."), on_click=self._on_change)
                self.controls = [self.change_btn]

            async def _on_load(self):
                # e.g. fetch password-policy info from server
                ...
    """

    # Shared layout defaults (consistent with DeclarativeSettingsPage)
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router) -> None:
        super().__init__(page, router)
        self.app_shared = AppShared()

        self.appbar = ft.AppBar(
            title=ft.Text(type(self).settings_name),
            leading=ft.IconButton(icon=Symbols.ARROW_BACK, on_click=self._go_back),
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self._on_load)

    # ------------------------------------------------------------------
    # Override hooks
    # ------------------------------------------------------------------

    async def _on_load(self) -> None:
        """Called on mount.  Override to perform async initialization
        (e.g. fetching current status from the server)."""

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def _go_back(self, event: ft.Event[ft.IconButton]) -> None:
        await self.page.push_route(get_parent_route(self.page.route))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_value_to_control(control: ft.Control, value: Any) -> None:
    """Write *value* into the appropriate attribute of *control*."""
    if isinstance(control, ft.Switch):
        control.value = bool(value) if value is not None else False
    elif isinstance(control, (ft.TextField, ft.Dropdown)):
        control.value = str(value) if value is not None else ""


def _read_control_value(control: ft.Control) -> Any:
    """Read the current value from *control*."""
    if isinstance(control, (ft.Switch, ft.TextField, ft.Dropdown)):
        return control.value
    return None
