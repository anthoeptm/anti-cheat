#!/usr/bin/env python

""" Anti-Cheat client :
    See all keys typed by all servers
"""

import threading
import random

import tkinter as tk
from tkinter.colorchooser import askcolor
# todo : make auto install or use setup.py
from PIL import Image, ImageTk

from clientRecvKeys import SocketClient
from clientComponentWindow import SettingsWindow, Student, Notification

DEFAULT_CLASSROOM = '201'
PORT = 2345

CHECK_CONN_HOST_INTERVAL = 10

# --- Other classes ---

class NotificationManager():
    """Manage notifications on the window"""
    def __init__(self):
        self.notifications = []

    def init(self, parent, icon_close):
        """
         Initialize the manger with a parent widget and a close icon for the notifications
         
         Args:
         	 parent: The widget that will be used as parent for the notifications
         	 icon_close: The widget that will be used as close icon
        """
        self.parent = parent
        self.icon_close = icon_close

    def add(self, text, color, autoclose=True):
        """
         Add a notification to the window.

         Args:
         	 text: The text of the notification
         	 color: The color of the notification
         	 autoclose: Say if the notification should be automatically closed or not
        """
        """Show a notification on the window"""
        if not self.parent: return
        notification = Notification(self.parent, text, color, self.icon_close, lambda: self.remove(notification))
        self.notifications.append(notification)
        notification.place(relx=1.3, rely=0.95 - (0.08 * (len(self.notifications)-1)), anchor="se") # to make them appear on top of each other
        notification.show(self.parent)

        if not autoclose: return
        self.parent.after(5000, lambda: notification.close()) # close after 5 seconds

    def remove(self, notification):
        """
         Remove a notification from the window.

         Args:
         	 notification: The notification to be removed 
        """
        if notification not in self.notifications: return

        notification_idx = self.notifications.index(notification)
        for i in range(notification_idx + 1, len(self.notifications)): # move all notifications above this one down once
            old_notification_rely = float(self.notifications[i].place_info()["rely"])
            self.notifications[i].place_configure(rely=old_notification_rely+0.08)

        self.notifications.remove(notification)

# --- Functions ---

def on_window_close(root:tk.Tk):
    """
     Stop the programm, the socket client and destroy the window.
     This is a callback function to be called when the button to close the window is pressed
     
     Args:
     	 root: The root window
    """
    global isRunning, client

    isRunning = False

    if "client" in globals():
        client.is_running = False

    root.destroy()

def update_window(data, students, icon, colors):
    """update the number of students and their keys on the window"""
    global notification_manager, client

    for host in client.hosts_connected_name.values():
        if host["hostname"] is None: continue # if the host has send no keys, skip it

        if "component" in host and host["component"] is None: # if the host has no component, add a component to it, else add keys to the component
            
            s = Student(students, host["hostname"], [key['key'] for key in data["keys"]], icon, colors)
            s.pack(anchor="w", pady=10)
            host["component"] = s


        else:
            host["component"].set_keys([key for key in keys[host["hostname"]]] +  [key['key'] for key in data["keys"]])

    if host["hostname"] not in keys.keys():
        keys[host["hostname"]] = []

    keys[host["hostname"]].extend([key['key'] for key in data["keys"]])


def create_component_for_host(host, students, icon, colors, keys=None):
    global client

    print(client.hosts_connected_name)
    if client.hosts_connected_name[host]["component"]: return # if there is already a component for this host, skip it
    
    s = Student(students, host, keys or [], icon, colors)
    s.pack(anchor="w", pady=10)
    client.hosts_connected_name[host]["component"] = s


def on_connexion_closed(host, colors, students):
    global notification_manager

    notification_manager.add(f"Disconnected from {host}", colors["red"])
    for student in students.winfo_children():
        if student == client.hosts_connected_name[host]["component"]:
            student.destroy()

def all_children(wid, finList=None, indent=0):
    """ Get all the children of a widget recursively with the current one
    https://stackoverflow.com/questions/7290071/getting-every-child-widget-of-a-tkinter-window"""

    finList = finList or [wid]
    children = wid.winfo_children()
    for item in children:
        finList.append(item)
        all_children(item, finList, indent + 1)
    return finList


def update_colors(root:tk.Tk, old, new):
    """Update the colors of all the widgets on the application"""

    for widget in all_children(root):
        if widget.cget("bg") == old:
            widget.configure(bg=new)
        

def main():
    """
     Main function of Anti-Cheat.
     Sets up and starts the Tk application and all its
    """
    global isRunning, notification_manager, client

    # Colors
    colors = {
        "black" : "#000000",
        "dark" : "#3F4962",
        "green" : "#A0C553",
        "red" : "#FC5855",
        "blue" : "#44B8B9",
        "yellow" : "#FBD04E",
        "white" : "#FFFFFF",
        "gray" : "#EFEFEF"
    }


    # Window
    root = tk.Tk()
    root.title("Anti-Cheat")
    root.configure(bg=colors["white"])
    root.geometry("1400x800+100+100")
    root.protocol("WM_DELETE_WINDOW", lambda: on_window_close(root))

    # set default options
    root.wm_attributes("-transparentcolor", "blue")
    root.option_add("*activeBackground", colors["dark"])
    root.option_add("*highlightThickness", 0)
    root.option_add("*Button*cursor", "hand2")
    root.option_add("*Background", colors["white"])


    # Icons
    icon_refresh = ImageTk.PhotoImage(Image.open("icons/refresh_white.png").resize((25, 25)))
    icon_list = ImageTk.PhotoImage(Image.open("icons/list_white.png").resize((25, 25)))
    icon_download = ImageTk.PhotoImage(Image.open("icons/download_white.png").resize((20, 25)))
    icon_upload = ImageTk.PhotoImage(Image.open("icons/upload_white.png").resize((20, 25)))
    icon_close_white = ImageTk.PhotoImage(Image.open("icons/close_white.png").resize((25, 25)))
    icon_close_black = ImageTk.PhotoImage(Image.open("icons/close_black.png").resize((12, 15)))
    icon_computer = ImageTk.PhotoImage(Image.open("icons/computer_black.png").resize((60, 50))) # ! big
    icon_settings = ImageTk.PhotoImage(Image.open("icons/settings_white.png").resize((25, 25)))

    notification_manager.init(root, icon_close_black)

    # Tool menu
    tool_menu = tk.Frame(root, height=100, bg=colors["dark"])
    tool_menu.pack(side=tk.TOP, fill=tk.X)

    tool_menu_left = tk.Frame(tool_menu, bg=colors["dark"])
    tool_menu_left.pack(side="left")

    tool_menu_right = tk.Frame(tool_menu, bg=colors["dark"])
    tool_menu_right.pack(side="right")

    tk.Button(tool_menu_left, image=icon_refresh, bg=colors["dark"], height=50, bd=0, command=lambda: client.try_to_connect_to_classroom()).grid(row=0, column=0, padx=20)
    tk.Button(tool_menu_right, image=icon_list, bg=colors["dark"], height=50, bd=0).grid(row=0, column=3, padx=20)
    tk.Button(tool_menu_right, image=icon_download, bg=colors["dark"], height=50, bd=0).grid(row=0, column=4)
    tk.Button(tool_menu_right, image=icon_upload, bg=colors["dark"], height=50, bd=0).grid(row=0, column=5, padx=15)
    tk.Button(tool_menu_right, image=icon_settings, bg=colors["dark"], height=50, bd=0, command=lambda: SettingsWindow(root, colors).grab_set()).grid(row=0, column=6, padx=15)

    tk.Label(tool_menu_left, text="Classe :", bg=colors["dark"], fg=colors["white"]).grid(row=0, column=1)

    txt_classroom = tk.Entry(tool_menu_left, bg=colors["dark"], fg=colors["white"], highlightbackground=colors["red"], highlightthickness=1, highlightcolor=colors["red"], bd=0)
    txt_classroom.grid(row=0, column=2)

    # Eleves frame
    students = tk.Frame(root)
    students.pack(fill=tk.BOTH, expand=1, padx=20, pady=20)

    # Student(students, "SIOP-EDU0201-01", "test", icon_computer, colors).pack(anchor="w", pady=10)

    client.on_connexion = lambda host: notification_manager.add(f"New connection from {host}", colors["green"])
    client.on_connexion_closed = lambda host: on_connexion_closed(host, colors, students)
    client.on_key_recv = lambda data : update_window(data, students, icon_computer, colors) # update the window when new keys are received

    root.mainloop()
    

if __name__ == "__main__":
    keys = {}
    hosts_connected_name = {}
    isRunning = True
    notification_manager = NotificationManager()

    # Settings variables (changed from SettingsWindow and acces by main)
    auto_refresh = True
    check_conn_host_interval = CHECK_CONN_HOST_INTERVAL
    display_on_connexion_notif = True
    display_on_disconnexion_notif = True

    client = SocketClient(DEFAULT_CLASSROOM, PORT, CHECK_CONN_HOST_INTERVAL)
    client.try_to_connect_to_classroom()

    # threading.Thread(target=client.try_to_connect_to_classroom_for_ever).start()

    main()