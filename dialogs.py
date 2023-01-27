import gi
import strings
import util

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw


class DeleteDialog(Adw.MessageDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_body(strings.delete_label_sub+"?")
        self.add_response(strings.no, strings.no)
        self.add_response(strings.yes, strings.yes)
        self.set_response_appearance(strings.yes, Adw.ResponseAppearance.DESTRUCTIVE)