"""Declarative settings framework for CFMS Client NEXT.

This module provides base classes and utilities for defining settings pages
declaratively, with automatic UI control generation, load/save handling,
dependency management, and auto-registration in the Settings Overview.

Basic usage (declarative)::

    from include.ui.settings_framework import (
        DeclarativeSettingsPage, SettingsField, settings_page,
    )
    from flet_model import route

    @settings_page
    @route("my_settings")
    class MySettingsModel(DeclarativeSettingsPage):
        # Overview metadata
        settings_name = "My Settings"
        settings_description = "Configure my settings"
        settings_icon = ft.Icons.SETTINGS
        settings_route_suffix = "my_settings"

        # Declarative fields
        enable_feature: SettingsField[bool] = SettingsField(label=_("Enable feature"))
        feature_value: SettingsField[str] = SettingsField(
            label=_("Feature value"),
            depends_on="enable_feature",
        )

Non-declarative (existing complex) pages can still register for Overview
auto-population by mixing in :class:`RegisteredSettingsPage`::

    @settings_page
    @route("complex_settings")
    class ComplexSettingsModel(Model, RegisteredSettingsPage):
        settings_name = "Complex Settings"
        settings_description = "Complex configuration"
        settings_icon = ft.Icons.SETTINGS
        settings_route_suffix = "complex_settings"
        ...
"""

from __future__ import annotations

from typing import Any, Callable, ClassVar, Generic, TypeVar, get_args, get_type_hints, overload

_T = TypeVar("_T")
import flet as ft
from flet_model import Model, Router

from include.classes.shared import AppShared
from include.ui.util.notifications import send_success
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

__all__ = [
    "SettingsField",
    "RegisteredSettingsPage",
    "DeclarativeSettingsPage",
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
    _settings_registry.append(cls)  # type: ignore[arg-type]
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
    settings_icon: ClassVar[ft.IconData] = ft.Icons.SETTINGS
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
        (``_("…")``) or a zero-argument callable for deferred evaluation.
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
        Pass display texts as ``_("…")`` strings or use a callable.
        A callable returning such a list is also accepted.
    description:
        Optional help text rendered below the control (or below the row when
        ``row_id`` is used).  Same convention as *label*.
    depends_on:
        Attribute name of another ``bool`` field in the same class.  This
        field's control is disabled when the referenced field's value is
        falsy.
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
        depends_on: str | None = None,
        row_id: str | None = None,
        expand: bool = True,
        disabled: bool = False,
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
            The Python type from the class annotation (``bool``, ``str``, …).
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
            )


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
    automatic field saving and receives the preferences section dict).
    Override :meth:`_on_load` for extra loading steps (called after automatic
    value loading).  Both hooks may return a custom success-message string; if
    they do, it replaces the default ``"Settings Saved."`` notification.
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
            title=ft.Text(_(type(self).settings_name)),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK, on_click=self._go_back
            ),
            actions=[
                ft.IconButton(
                    ft.Icons.SAVE_OUTLINED, on_click=self._save_button_click
                )
            ],
            actions_padding=10,
        )

        # Introspect fields, build controls, wire dependencies.
        self._fields = self._collect_fields()
        self._control_map: dict[str, ft.Control] = {}
        self.controls = self._build_controls()

    # ------------------------------------------------------------------
    # Field introspection
    # ------------------------------------------------------------------

    def _collect_fields(self) -> list[tuple[str, SettingsField, type]]:
        """Return ``(attr_name, field, python_type)`` triples in declaration order.

        Only annotated class attributes whose value is a :class:`SettingsField`
        instance are included.

        Because :meth:`SettingsField.__set_name__` is called by Python when the
        class body is processed, each field already knows its own attribute name
        — no external mutation is required here.
        """
        cls = type(self)
        try:
            hints = get_type_hints(cls)
        except Exception:
            hints = {}

        result: list[tuple[str, SettingsField, type]] = []
        # cls.__annotations__ preserves declaration order (Python 3.7+) and
        # only contains annotations defined directly on cls (not inherited ones).
        # We walk the MRO to support field inheritance in subclasses.
        seen: set[str] = set()
        for klass in reversed(cls.__mro__):
            ann = getattr(klass, "__annotations__", {})
            for attr_name in ann:
                if attr_name in seen:
                    continue
                seen.add(attr_name)
                # Class-level access returns the SettingsField descriptor itself
                # (via __get__ with obj=None).
                val = getattr(cls, attr_name, None)
                if not isinstance(val, SettingsField):
                    continue
                # Prefer the fully-resolved hint from get_type_hints; fall back
                # to the raw annotation object (which may already be a resolved
                # generic alias when `from __future__ import annotations` is not
                # in effect in the subclass's module).
                hint = hints.get(attr_name) or ann.get(attr_name)
                # Support both the canonical SettingsField[T] annotation and
                # legacy bare type annotations (str, bool, …) for backward
                # compatibility.
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
                    # Legacy bare annotation e.g. `name: str = SettingsField(...)`
                    # The `issubclass` guard prevents using the bare SettingsField
                    # class itself as the field_type.
                    field_type = hint
                else:
                    field_type = str
                result.append((attr_name, val, field_type))
        return result

    # ------------------------------------------------------------------
    # Control building
    # ------------------------------------------------------------------

    def _build_controls(self) -> list[ft.Control]:
        """Build the list of Flet controls from the collected field definitions.

        Controls that share the same ``row_id`` are placed inside a single
        ``ft.Row``.  An optional description text is appended immediately
        after each standalone control or row.
        """
        controls: list[ft.Control] = []

        # State for the current pending row group
        pending_row_id: str | None = None
        pending_row_controls: list[ft.Control] = []
        pending_row_description: str | None = None

        def flush_pending_row() -> None:
            nonlocal pending_row_id, pending_row_controls, pending_row_description
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
            pending_row_id = None
            pending_row_controls = []
            pending_row_description = None

        for attr_name, field, field_type in self._fields:
            control = field.build_control(field_type)
            # Wire switch-change handler for automatic dependency flushing
            if isinstance(control, ft.Switch):
                control.on_change = self._on_switch_change
            self._control_map[attr_name] = control

            if field.row_id is not None:
                if field.row_id != pending_row_id:
                    # Starting a new row group – flush the previous one first
                    flush_pending_row()
                    pending_row_id = field.row_id
                pending_row_controls.append(control)
                # Keep the last non-None description within the row group
                if field.description is not None:
                    pending_row_description = field.description
            else:
                # Standalone control – flush any pending row first
                flush_pending_row()
                controls.append(control)
                if field.description is not None:
                    controls.append(
                        ft.Text(
                            field.description,
                            size=12,
                            color=ft.Colors.GREY,
                        )
                    )

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
            value = section.get(field.config_key, field.default)
            # Use the descriptor __set__ to write the value onto the control.
            setattr(self, attr_name, value)

        await self._on_load()
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
            # Use the descriptor __get__ to read the current control value.
            section[field.config_key] = getattr(self, attr_name)

        self.app_shared.dump_preferences()

        custom_message = await self._on_save()
        send_success(self.page, custom_message or _("Settings Saved."))

    # ------------------------------------------------------------------
    # Dependency management
    # ------------------------------------------------------------------

    async def _flush_dependencies(self) -> None:
        """Update the *disabled* state of controls with a ``depends_on``
        relationship.

        A control is disabled when its dependency field's value is falsy,
        *unless* the field is permanently disabled (``SettingsField.disabled``
        is ``True``).
        """
        for attr_name, field, _ftype in self._fields:
            if field.depends_on is None or field.disabled:
                continue
            control = self._control_map.get(attr_name)
            if control is None:
                continue
            # Use the descriptor __get__ to read the dependency's current value.
            dep_value = getattr(self, field.depends_on)
            control.disabled = not bool(dep_value)
        self.update()

    async def _on_switch_change(self, event: ft.Event[ft.Switch]) -> None:
        """Generic handler wired to every ``ft.Switch`` for dependency updates."""
        await self._flush_dependencies()

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
