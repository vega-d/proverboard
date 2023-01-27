import sys
import gi
import strings
import util
from util import log
import dialogs

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(600, 600)
        self.set_title(strings.name)

        # headerbar
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.add_site_button = Gtk.Button(label="Open")
        self.add_site_button.connect("clicked", self.on_add_site_press)
        self.add_site_button.set_icon_name("list-add-symbolic")
        self.header.pack_start(self.add_site_button)

        self.group = Adw.PreferencesGroup()
        self.group.set_title(strings.group_title)
        self.group.set_margin_start(5)
        self.group.set_margin_end(5)

        self.scrollable = Gtk.ScrolledWindow()
        self.scrollable.set_child(self.group)
        # self.scrollable.set_size_request(300, 400)

        clamp = Adw.Clamp()
        clamp.set_child(self.scrollable)
        self.set_child(clamp)

        self.sitelist = util.Sitelist()
        self.sitelist.recover()

        if len(self.sitelist.list):
            for i in self.sitelist.list:
                self.add_site(i)

    def on_add_site_press(self, *arg):
        util.log("low", "adding a site")
        self.add_site()

    def on_site_delete_press(self, button, site_obj):
        dialog = dialogs.DeleteDialog()
        dialog.set_transient_for(self)
        dialog.connect("response", self.on_dialog_delete_confirm, site_obj)
        dialog.show()

    def on_dialog_delete_confirm(self, dialog_obj, response, site_obj):
        if response == strings.yes:
            self.group.remove(site_obj)

    def add_site(self, object=None):
        alr = False
        if not object:
            object = util.URL()
            site_row = util.Site(object)
        else:
            alr = True
            site_row = object

        site_row.delete_button.connect("clicked", self.on_site_delete_press, site_row)
        self.group.add(site_row)
        if not alr:
            self.sitelist.list.append(site_row)


class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
        self.connect('shutdown', self.on_shutdown)
        self.win = None  # Forgot to add this originally

    def on_activate(self, app):
        if not self.win:
            self.win = MainWindow(application=app)
        self.win.present()  # if window is already created, this will raise it to the front

    def on_shutdown(self, app):
        self.win.sitelist.save()


app = MyApp(application_id="io.github.vega-d.proverboard")
app.run(sys.argv)
