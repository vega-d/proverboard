import os, appdirs, strings, dialogs, dialogs, json, pathlib, requests
from datetime import datetime

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log(severity="low", *message):
    def colorprint(color, *args):
        args = " ".join(args)
        print(f"{color}" + args + f"{color}")

    time = datetime.now().strftime("%H:%M:%S")

    # listify the arguments list and stringify it's contents
    message = list(message)
    for i in range(len(message)):
        if type(message[i]) != str:
            message[i] = str(message[i])
    if type(severity) != str:
        severity = str(severity)

    if severity == "low":
        colorprint(bcolors.OKGREEN, time, ":", *message)
    elif severity == "mid":
        colorprint(bcolors.WARNING,
                   "< !!! > --------- < !!! > --------- < WARNING START > --------- < !!! > --------- < !!! >")
        colorprint(bcolors.WARNING, time, ":", *message)
        colorprint(bcolors.WARNING,
                   "< !!! > --------- < !!! > --------- < WARNING END > --------- < !!! > --------- < !!! >")
    elif severity == "high":
        colorprint(bcolors.FAIL,
                   "< !!! > --------- < !!! > --------- < ERROR START > --------- < !!! > --------- < !!! >")
        colorprint(bcolors.FAIL, time, ":", *message)
        colorprint(bcolors.FAIL,
                   "< !!! > --------- < !!! > --------- < ERROR END > --------- < !!! > --------- < !!! >")
    else:
        colorprint(bcolors.OKGREEN, time, ":", severity, *message)


class URL:
    arguments: dict
    page: list
    domain: str
    protocol: str
    enabled: bool

    def __init__(self, protocol=None, domain=None, port="80", page=None, arguments=None):
        self.protocol = protocol  # "http://"
        self.domain = domain  # "example.com"
        self.port = port
        self.page = page  # ["downloads", "index.html"] => "/downloads/index.html
        self.arguments = arguments  # ["arg1": "data1", "arg2": "data2"] => "&arg1=data1?arg2=data2"
        self.enabled = False

    def is_empty(self):
        return not (self.protocol or self.domain or self.page or self.arguments)

    def get_domain(self):
        return self.domain

    def get_protocol(self):
        return self.protocol

    def get_shortened_url(self):
        if self.protocol and self.domain:
            return self.protocol + self.domain
        else:
            return None

    def get_link_args(self):
        page = ""
        if not self.page and not self.arguments and not self.port:
            return None
        if self.port:
            page += ":"
            page += str(self.port)

        if self.page:
            for i in self.page:
                page += "/"
                page += i

        if self.arguments:
            args = "&"
            arg_counter = 0
            for i in self.arguments.keys():
                args += i
                if self.arguments[i]:
                    args += "="
                    args += self.arguments[i]

                if arg_counter < len(self.arguments.keys()) - 1:
                    args += "?"

                arg_counter += 1
        else:
            args = ""
        return page + args

    def sanitize_url_for_gtk(self, url_str=None, none_possible=False):
        if url_str:
            if type(url_str) is str:
                return url_str.rstrip("/").rstrip("&").replace("&", "&amp;")
            if type(url_str) is URL:
                return self.sanitize_url_for_gtk(url_str.get_url())
        elif none_possible or url_str == "":
            return ""
        return self.sanitize_url_for_gtk(self)

    def get_url(self):
        domain = self.get_shortened_url()
        args = self.get_link_args()
        if domain:
            if args:
                domain += args
            return domain
        return None

    def __str__(self):
        if self.get_url():
            return "your URL type object is: " + self.get_url()
        else:
            return "This URL type object is empty."

    def __bool__(self):
        return bool(self.get_url())

    def get_port(self):
        return self.port

    def validate(self, url=None):
        log("low", "validating url:", url)
        if url is None:
            return False
        elif type(url) is URL:
            self.validate(self.get_url())
        else:
            return url.count("://") == 1

    def from_string(self, url):
        # url = "http://example.com/downloads/index.html&arg1=data1?arg2=data2"
        # accepts "http://example.com/index.html&arg1=data1" type of strings
        if not self.validate(url) or type(url) is not str:
            log("high", "Failed to validate url? :", url)
            return URL()
        url = url.rstrip("&").rstrip("/")
        page_path = []
        arguments = {}
        port = None

        protocol_split = url.split("://")
        protocol = protocol_split[0] + "://"

        domain_split = protocol_split[1].split("/")
        domain = domain_split[0]

        # if url.count("/") > 2:
        page_split = domain_split
        page_path = page_split[1:]

        if url.count("&"):
            argument_split = domain_split[-1].split("&")
            log("mid", argument_split)
            if url.count("/") > 2:
                page_path[-1] = argument_split[0]
            if url.count("/") == 2:
                domain = argument_split[0]
            preargument_array = argument_split[1].split("?")
            for i in preargument_array:
                if i.count("="):
                    subargument_split = i.split("=")
                    arguments[subargument_split[0]] = subargument_split[1]
                else:
                    arguments[i] = ""

        if url.count(":") == 2:
            port_split = domain.split(":")
            domain = port_split[0]
            port = port_split[1]

        log("parsed in the url:", protocol, domain, port, page_path, arguments)
        return URL(protocol, domain, port, page_path, arguments)

    def set_url(self, url):
        if type(url) is str:
            url = self.from_string(url)
        self.protocol = url.protocol  # "http://"
        self.domain = url.domain  # "example.com"
        self.page = url.page  # ["downloads", "index.html"] => "/downloads/index.html
        self.port = url.port
        self.arguments = url.arguments  # ["arg1": "data1", "arg2": "data2"] => "&arg1=data1?arg2=data2"

    def set_enabled(self, enabled):
        self.enabled = enabled


class Sitelist:
    def __init__(self):
        self.list = []

    def recover(self):
        if not self.make_sure_conf_exists():
            return None
        try:
            with open(os.path.join(appdirs.user_config_dir(strings.name, strings.author, version=strings.version),
                                   "config.json"), "r") as file:
                # print(file.read())
                recovered = json.loads(file.read())
            log(recovered)
        except Exception as e:
            recovered = []
            log('high', "failed to load json config, deciding to assume it's empty instead.")
        for i in recovered:
            i: dict
            if "url" in i.keys():
                if i["url"]:
                    url = URL.from_string(URL(), i["url"])
                    url.set_enabled(i["enabled"])
                    log("low", "loaded in an url from conf file:", url)
                    self.list.append(Site(url))

    def save(self):
        log("low", "Saving current data into json config")

        if not self.make_sure_conf_exists():
            raise FileNotFoundError
        log("low", "our current objects are:")
        for i in self.list:
            i: Site
            if not i.url.get_url():
                self.list.remove(i)
            log(i)

        with open(os.path.join(appdirs.user_config_dir(strings.name, strings.author, version=strings.version),
                               "config.json"), "w") as file:
            file.write(json.dumps([i.toJSON() for i in self.list]))

    def __getitem__(self, item):
        return self.list[item]

    def __sizeof__(self):
        return len(self.list)

    def make_sure_conf_exists(self):
        folder = appdirs.user_config_dir(strings.name, strings.author, version=strings.version)
        path = os.path.join(folder, "config.json")
        log("low", "config path is:", path)
        try:
            with open(path, "r") as file:
                return True
        except FileNotFoundError:
            if not os.path.exists(folder):  # create the folder if it doesn't exist
                try:
                    os.makedirs(folder)
                except Exception as e:
                    log("high", strings.cant_create_config_folder, e)
                    raise e
            if not os.path.isfile(path):
                try:
                    with open(path, "w+") as file:
                        return True
                except Exception as e:
                    log("high", strings.cant_create_config_file, e)
                    raise e
        return False


class Site(Adw.ExpanderRow):
    url: URL

    def __init__(self, url=None, **properties):
        super().__init__(**properties)
        self.url = url

        icon = Gtk.Image()
        icon.set_from_icon_name("network-server-symbolic")
        self.add_prefix(icon)

        self.add_css_class("card")
        if url.enabled == 0:
            self.add_css_class("background")

        toggle_field = Adw.ActionRow()
        toggle_field.set_title(strings.enabled_label)
        toggle_field.set_subtitle(strings.enabled_label_sub)
        minibox = Gtk.CenterBox(orientation=Gtk.Orientation.VERTICAL)
        self.switch = Gtk.Switch()
        self.switch.set_active(url.enabled == 1)
        minibox.set_center_widget(self.switch)
        toggle_field.add_suffix(minibox)

        if url.is_empty():
            self.set_title("New Site")
            self.switch.set_active(False)
            self.switch.set_sensitive(False)
            self.set_expanded(True)
        else:
            self.set_text()

        url_field = Adw.EntryRow()
        url_field.set_title(strings.url_title)
        url_field.set_input_purpose(Gtk.InputPurpose.URL)
        url_field.set_input_hints(Gtk.InputHints.NO_SPELLCHECK)
        url_field.set_show_apply_button(True)
        url_field.connect("apply", self.on_apply_url)
        if not url.is_empty():
            url_field.set_text(url.get_url())

        delete_field = Adw.ActionRow()
        minibox = Gtk.CenterBox(orientation=Gtk.Orientation.VERTICAL)
        self.delete_button = Gtk.Button(label=strings.delete_label)
        self.delete_button.add_css_class("destructive-action")
        minibox.set_center_widget(self.delete_button)
        delete_field.add_suffix(minibox)

        self.add_row(toggle_field)
        self.add_row(url_field)
        self.add_row(delete_field)
        # TODO here go settings for a site

    def on_apply_url(self, entry_row):
        new_url = entry_row.get_text()
        log("mid", "new url should be:", new_url, type(new_url))
        if self.url.validate(new_url):
            self.url.set_url(new_url)
            self.set_text()
            entry_row.remove_css_class("error")
            self.switch.set_sensitive(True)
        else:
            entry_row.add_css_class("error")
            # TODO: maybe send a toast notification on failure?

    def set_text(self, url=None):
        url: URL
        if url is None:
            url = self.url
        args = url.get_link_args()
        if args:
            self.set_subtitle(self.url.sanitize_url_for_gtk(args))

        self.set_title(self.url.sanitize_url_for_gtk(url.get_shortened_url()))

    def get_url_object(self):
        return self.url

    def __str__(self):
        url = self.url.get_url()
        if not url:
            url = "None"
        return "URL:" + url + "; ENABLED:" + ("True" if self.switch.get_active() else "False") + ";"

    def __bool__(self):
        return bool(self.url.get_url())

    def toJSON(self):
        return {"url": self.url.get_url(), "enabled": self.switch.get_active()}
