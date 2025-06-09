import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

import psutil
import os
import signal

# CSS for styling
css = b"""
* {
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.window {
    background-color: #1e1e2f;
    color: #f0f0f0;
}

.header {
    background-color: #2e2f48;
    padding: 10px;
    font-size: 22px;
    font-weight: bold;
    color: #e0e0ff;
}

.sidebar {
    background-color: #2e2f48;
    padding: 10px;
}

.sidebar button {
    background-color: #3c3f58;
    border-radius: 5px;
    margin: 6px 0;
    color: #cfcfe0;
    font-weight: bold;
    padding: 10px 20px;
    border: none;
}

.sidebar button:hover {
    background-color: #505377;
}

.sidebar button.active {
    background-color: #6064a9;
}

.main-area {
    background-color: #252538;
    padding: 15px;
    border-radius: 10px;
    color: #d0d0d8;
}

.task-list {
    background-color: #33334d;
    border-radius: 8px;
    padding: 10px;
    color: #e0e0e0;
}

.task-list row {
    padding: 8px;
}

.task-list row:hover {
    background-color: #444466;
}

.statusbar {
    padding: 5px 0;
    color: #b0b0c8;
    font-style: italic;
}

.system-info-label {
    font-weight: bold;
    font-size: 14px;
    color: #c0c0ff;
}
"""

class LinuxTaskManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="Linux Task Manager")
        self.set_default_size(1000, 650)
        self.set_border_width(10)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Apply CSS
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.selected_section = "Processes"

        # Main vertical box container
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.vbox)

        # Create menu bar and add to vbox
        self.create_menu_bar()

        # Horizontal box for sidebar and content
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.vbox.pack_start(main_box, True, True, 0)

        # Sidebar setup
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sidebar.set_size_request(220, -1)
        self.sidebar.get_style_context().add_class("sidebar")
        main_box.pack_start(self.sidebar, False, False, 0)

        # Sidebar buttons
        self.sections = ["Processes", "System", "Disk", "Network"]
        self.sidebar_buttons = {}
        for sec in self.sections:
            btn = Gtk.Button(label=sec)
            btn.set_halign(Gtk.Align.FILL)
            btn.set_valign(Gtk.Align.CENTER)
            btn.get_style_context().add_class("sidebar-button")
            btn.connect("clicked", self.on_sidebar_button_clicked)
            self.sidebar.pack_start(btn, False, False, 0)
            self.sidebar_buttons[sec] = btn

        # Set active button style
        self.sidebar_buttons[self.selected_section].get_style_context().add_class("active")

        # Content area
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content_box.set_hexpand(True)
        self.content_box.set_vexpand(True)
        self.content_box.get_style_context().add_class("main-area")
        main_box.pack_start(self.content_box, True, True, 0)

        # Header label
        self.header_label = Gtk.Label()
        self.header_label.set_halign(Gtk.Align.START)
        self.header_label.set_margin_bottom(10)
        self.header_label.set_markup(f"<span size='xx-large' weight='bold'>{self.selected_section}</span>")
        self.content_box.pack_start(self.header_label, False, False, 0)

        # Search entry for filtering processes
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search process by name or PID...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.content_box.pack_start(self.search_entry, False, False, 5)
        self.search_entry.set_visible(True)

        # Section area for dynamic content
        self.section_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.section_area.set_hexpand(True)
        self.section_area.set_vexpand(True)
        self.content_box.pack_start(self.section_area, True, True, 0)

        # Status bar
        self.statusbar = Gtk.Label()
        self.statusbar.set_halign(Gtk.Align.START)
        self.statusbar.get_style_context().add_class("statusbar")
        self.content_box.pack_start(self.statusbar, False, False, 0)

        # Initialize UI for the default section
        self.create_process_list_ui()

        # Start periodic UI update every 3 seconds
        GLib.timeout_add_seconds(3, self.update_ui)

        self.show_all()

    def create_menu_bar(self):
        menubar = Gtk.MenuBar()

        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)

        refresh_item = Gtk.MenuItem(label="Refresh")
        refresh_item.connect("activate", lambda x: self.manual_refresh())
        file_menu.append(refresh_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", lambda x: Gtk.main_quit())
        file_menu.append(quit_item)

        menubar.append(file_item)

        self.vbox.pack_start(menubar, False, False, 0)

    def manual_refresh(self):
        self.update_ui()

    def on_sidebar_button_clicked(self, button):
        sec = button.get_label()
        if sec == self.selected_section:
            return

        # Remove active class from old button, add to new
        self.sidebar_buttons[self.selected_section].get_style_context().remove_class("active")
        button.get_style_context().add_class("active")
        self.selected_section = sec
        self.header_label.set_markup(f"<span size='xx-large' weight='bold'>{sec}</span>")

        # Clear section area
        for child in self.section_area.get_children():
            self.section_area.remove(child)

        # Show or hide search entry
        self.search_entry.set_text("")
        self.search_entry.set_visible(sec == "Processes")

        # Load appropriate section UI
        if sec == "Processes":
            self.section_area.pack_start(self.process_treeview_scrolled, True, True, 0)
            self.process_treeview.show()
        elif sec == "System":
            self.create_system_info_ui()
        elif sec == "Disk":
            self.create_disk_info_ui()
        elif sec == "Network":
            self.create_network_info_ui()

        self.section_area.show_all()

    def create_process_list_ui(self):
        self.process_liststore = Gtk.ListStore(int, str, float, float)
        self.filtered_liststore = self.process_liststore.filter_new()
        self.filtered_liststore.set_visible_func(self.filter_process)

        self.process_treeview = Gtk.TreeView(model=self.filtered_liststore)
        self.process_treeview.set_vexpand(True)

        columns = [("PID", 0), ("Name", 1), ("CPU %", 2), ("Memory %", 3)]
        for title, idx in columns:
            renderer = Gtk.CellRendererText()
            if title in ("CPU %", "Memory %"):
                renderer.set_property("xalign", 1.0)
            col = Gtk.TreeViewColumn(title, renderer, text=idx)
            col.set_resizable(True)
            col.set_sort_column_id(idx)
            self.process_treeview.append_column(col)

        # Connect signals
        self.process_treeview.connect("button-press-event", self.on_process_treeview_button_press)
        self.process_treeview.connect("row-activated", self.on_process_row_activated)

        self.process_treeview_scrolled = Gtk.ScrolledWindow()
        self.process_treeview_scrolled.set_hexpand(True)
        self.process_treeview_scrolled.set_vexpand(True)
        self.process_treeview_scrolled.add(self.process_treeview)

        self.section_area.pack_start(self.process_treeview_scrolled, True, True, 0)

        self.refresh_process_list()

    def filter_process(self, model, iter, data=None):
        query = self.search_entry.get_text().lower()
        if not query:
            return True
        name = model[iter][1].lower()
        pid_str = str(model[iter][0])
        return query in name or query in pid_str

    def on_search_changed(self, entry):
        self.filtered_liststore.refilter()

    def refresh_process_list(self):
        self.process_liststore.clear()
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pid = proc.info['pid']
                name = proc.info['name'] or ""
                cpu = proc.info['cpu_percent'] or 0.0
                mem = proc.info['memory_percent'] or 0.0
                self.process_liststore.append([pid, name, cpu, mem])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def on_process_treeview_button_press(self, treeview, event):
        if event.button == 3:  # Right-click
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is not None:
                path, col, cellx, celly = path_info
                treeview.grab_focus()
                treeview.set_cursor(path, col, False)
                self.show_process_context_menu(event)
                return True
        return False

    def show_process_context_menu(self, event):
        menu = Gtk.Menu()

        kill_item = Gtk.MenuItem(label="End Task")
        kill_item.connect("activate", self.on_kill_process)
        menu.append(kill_item)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

    def on_kill_process(self, menuitem):
        selection = self.process_treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            pid = model[treeiter][0]

            # Confirmation dialog before killing
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Are you sure you want to end the process with PID {pid}?"
            )
            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.YES:
                try:
                    os.kill(pid, signal.SIGTERM)
                    # Wait a bit and if process still alive, SIGKILL
                    GLib.timeout_add_seconds(1, self.check_and_kill_force, pid)
                    self.refresh_process_list()
                    self.filtered_liststore.refilter()
                except PermissionError:
                    self.show_error_dialog("Permission denied to kill this process.")
                except ProcessLookupError:
                    self.show_error_dialog("Process does not exist anymore.")
                except Exception as e:
                    self.show_error_dialog(str(e))

    def check_and_kill_force(self, pid):
        try:
            os.kill(pid, 0)  # Check if process exists
            # Process still alive, force kill
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            # Process is gone
            pass
        return False  # Remove timeout

    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Error",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def on_process_row_activated(self, treeview, path, column):
        model = treeview.get_model()
        iter = model.get_iter(path)
        if iter:
            pid = model[iter][0]
            try:
                proc = psutil.Process(pid)
                info = (
                    f"PID: {proc.pid}\n"
                    f"Name: {proc.name()}\n"
                    f"Status: {proc.status()}\n"
                    f"User: {proc.username()}\n"
                    f"Started: {proc.create_time():.0f}\n"
                    f"CPU Usage: {proc.cpu_percent(interval=0.1)}%\n"
                    f"Memory Usage: {proc.memory_percent():.2f}%\n"
                    f"Executable: {proc.exe()}\n"
                    f"Command Line: {' '.join(proc.cmdline())}"
                )
            except Exception as e:
                info = f"Could not fetch details: {str(e)}"

            dlg = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.CLOSE,
                text=f"Details for PID {pid}",
            )
            dlg.format_secondary_text(info)
            dlg.run()
            dlg.destroy()

    def update_ui(self):
        if self.selected_section == "Processes":
            self.refresh_process_list()
            self.filtered_liststore.refilter()
            self.update_status_bar()
        elif self.selected_section == "System":
            self.update_system_info()
        elif self.selected_section == "Disk":
            self.update_disk_info()
        elif self.selected_section == "Network":
            self.update_network_info()
        return True  # Keep the timeout active

    def update_status_bar(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        self.statusbar.set_text(f"CPU Usage: {cpu:.1f}%   RAM Usage: {mem.percent:.1f}%")

    def create_system_info_ui(self):
        for c in self.section_area.get_children():
            self.section_area.remove(c)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.section_area.pack_start(box, True, True, 0)

        cpu_label = Gtk.Label(label="CPU Usage")
        cpu_label.get_style_context().add_class("system-info-label")
        cpu_label.set_halign(Gtk.Align.START)
        box.pack_start(cpu_label, False, False, 0)

        self.cpu_bar = Gtk.LevelBar()
        self.cpu_bar.set_min_value(0)
        self.cpu_bar.set_max_value(100)
        self.cpu_bar.set_value(psutil.cpu_percent(interval=0.1))
        self.cpu_bar.set_size_request(-1, 20)
        box.pack_start(self.cpu_bar, False, False, 0)

        ram_label = Gtk.Label(label="RAM Usage")
        ram_label.get_style_context().add_class("system-info-label")
        ram_label.set_halign(Gtk.Align.START)
        box.pack_start(ram_label, False, False, 0)

        self.ram_bar = Gtk.LevelBar()
        self.ram_bar.set_min_value(0)
        self.ram_bar.set_max_value(100)
        self.ram_bar.set_value(psutil.virtual_memory().percent)
        self.ram_bar.set_size_request(-1, 20)
        box.pack_start(self.ram_bar, False, False, 0)

        box.show_all()

    def update_system_info(self):
        if hasattr(self, "cpu_bar") and hasattr(self, "ram_bar"):
            self.cpu_bar.set_value(psutil.cpu_percent(interval=None))
            self.ram_bar.set_value(psutil.virtual_memory().percent)

    def create_disk_info_ui(self):
        for c in self.section_area.get_children():
            self.section_area.remove(c)

        self.disk_liststore = Gtk.ListStore(str, str, float, float)
        self.disk_treeview = Gtk.TreeView(model=self.disk_liststore)
        self.disk_treeview.set_vexpand(True)

        columns = [("Device", 0), ("Mount Point", 1), ("Used %", 2), ("Free %", 3)]
        for title, idx in columns:
            renderer = Gtk.CellRendererText()
            if title in ("Used %", "Free %"):
                renderer.set_property("xalign", 1.0)
            col = Gtk.TreeViewColumn(title, renderer, text=idx)
            col.set_resizable(True)
            self.disk_treeview.append_column(col)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.add(self.disk_treeview)

        self.section_area.pack_start(scrolled, True, True, 0)

        self.update_disk_info()

    def update_disk_info(self):
        self.disk_liststore.clear()
        partitions = psutil.disk_partitions(all=False)
        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                used_percent = usage.percent
                free_percent = 100 - used_percent
                self.disk_liststore.append([part.device, part.mountpoint, used_percent, free_percent])
            except PermissionError:
                continue

    def create_network_info_ui(self):
        for c in self.section_area.get_children():
            self.section_area.remove(c)

        self.net_liststore = Gtk.ListStore(str, str, int, int)
        self.net_treeview = Gtk.TreeView(model=self.net_liststore)
        self.net_treeview.set_vexpand(True)

        columns = [("Interface", 0), ("Address", 1), ("Sent (bytes)", 2), ("Recv (bytes)", 3)]
        for title, idx in columns:
            renderer = Gtk.CellRendererText()
            if title in ("Sent (bytes)", "Recv (bytes)"):
                renderer.set_property("xalign", 1.0)
            col = Gtk.TreeViewColumn(title, renderer, text=idx)
            col.set_resizable(True)
            self.net_treeview.append_column(col)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.add(self.net_treeview)

        self.section_area.pack_start(scrolled, True, True, 0)

        self.last_net_io = psutil.net_io_counters(pernic=True)
        self.update_network_info()

    def update_network_info(self):
        self.net_liststore.clear()
        current_net_io = psutil.net_io_counters(pernic=True)
        for iface, io in current_net_io.items():
            addr = self.get_interface_address(iface)
            sent = io.bytes_sent
            recv = io.bytes_recv
            self.net_liststore.append([iface, addr, sent, recv])
        self.last_net_io = current_net_io

    def get_interface_address(self, iface):
        addrs = psutil.net_if_addrs()
        if iface in addrs:
            for addr in addrs[iface]:
                if addr.family == 2:  # AF_INET
                    return addr.address
        return "N/A"

def main():
    app = LinuxTaskManager()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()

if __name__ == "__main__":
    main()
