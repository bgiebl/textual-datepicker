from __future__ import annotations

import pendulum

from textual.app import ComposeResult, App
from textual.widget import Widget, events
from textual.containers import Vertical, Container
from textual.reactive import reactive
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.geometry import Size

# from textual import log

from . import DatePicker


class DatePickerDialog(Widget):
    """The dialog/menu which opens below the DateSelect."""

    DEFAULT_CSS = """
    DatePickerDialog {
        layer: dialog;
        background: $boost;
        width: 30;
        height: 17;
        border: tall $accent;
    }
    """

    # The DatePicker mounted in this dialog.
    date_picker = None
    size = Size(30, 17)

    # A target where to send the message for a selected date
    target = None
    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        self.date_picker = DatePicker()
        self.date_picker.target = self.target
        yield Vertical(self.date_picker)

    def on_descendant_blur(self, event: events.DescendantBlur) -> None:
        if len(self.query("*:focus-within")) == 0:
            self.display = False

    def on_date_picker_selected(self, event: DatePicker.Selected) -> None:
        self.display = False
        self.app.pop_screen()

        if self.target is not None:
            self.target.focus()



class DateSelect(Widget, can_focus=True):
    """A select widget which opens the DatePicker and displays the selected date."""

    DEFAULT_CSS = """
    DateSelect {
      background: $boost;
      color: $text;
      padding: 0 2;
      border: tall $background;
      height: 1;
      min-height: 1;
    }
    DateSelect:focus {
      border: tall $accent;
    }
    """

    # The value displayed in the select (which is the date)
    # value = reactive("", layout=True, init=False)

    # Date of the month which shall be shown when opening the dialog
    date: reactive[pendulum.DateTime | None] = reactive(None)

    def __init__(
        self,
        date: pendulum.DateTime | None = None,
        format: str = "YYYY-MM-DD",
        placeholder: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.placeholder = placeholder
        self.format = format

        if date is not None:
            self.date = date

        # DatePickerDialog widget
        self.dialog = None

    @property
    def value(self) -> pendulum.DateTime:
        """Value of the current date."""
        return self.date

    def render(self) -> str:
        chevron = "\u25bc"
        width = self.content_size.width
        text_space = width - 2

        if text_space < 0:
            text_space = 0

        if not self.date:
            text = self.placeholder
        else:
            text = self.date.format(self.format)

        if len(text) > text_space:
            text = text[0:text_space]

        text = f"{text:{text_space}} {chevron}"

        return text

    def on_mount(self) -> None:
        if self.dialog is None:
            self.dialog = DatePickerDialog()
            self.dialog.target = self

        self.app.install_screen(DatePickerDialogScreen(self.dialog), name="date_picker_dialog_screen")

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self._show_date_picker()

    def on_click(self, event: events.MouseEvent) -> None:
        self._show_date_picker()

    def on_blur(self) -> None:
        pass

    def on_date_picker_selected(self, event: DatePicker.Selected) -> None:
        self.date = event.date

    def _show_date_picker(self) -> None:
        self.dialog.display = True
        self.app.push_screen("date_picker_dialog_screen")


class DatePickerDialogScreen(ModalScreen):
    BINDINGS = [("escape", "app.pop_screen()", "Pop screen")]

    def __init__(self, date_picker_dialog):
        super().__init__()
        self.date = None
        self.dialog = date_picker_dialog

    def compose(self) -> ComposeResult:
        yield self.dialog

    def on_resize(self) -> None:
        self.dialog.offset = (
            (self.app.size[0] - self.dialog.size[0])//2, (self.app.size[1] - self.dialog.size[1])//2)

    def on_click(self, event: events.MouseEvent) -> None:
        # Remove the datepicker screen if the user clicks outside of it:
        if not (self.dialog.offset[0] <= event.screen_x < self.dialog.offset[0] + self.dialog.size[0]) \
                or not (self.dialog.offset[1] <= event.screen_y < self.dialog.offset[1] + self.dialog.size[1]):
            self.app.pop_screen()

    def on_mount(self) -> None:
        # TODO: should be dynamic for smaller inputs
        self.dialog.offset = (
            (self.app.size[0] - self.dialog.size[0])//2, (self.app.size[1] - self.dialog.size[1])//2)

        if self.date is not None:
            if self.date is not None:
                self.dialog.date_picker.date = self.date
            for day in self.dialog.query("DayLabel.--day"):
                if day.day == self.date.day:
                    day.focus()
                    break
        else:
            try:
                self.dialog.query_one("DayLabel.--today").focus()
            except NoMatches:   # pragma: no cover
                # should never happen, because DatePicker always opens this
                # month without a given date. just to be sure,
                # catching query_one fails.
                self.dialog.query("DayLabel.--day").first().focus()
