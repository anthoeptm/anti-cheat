#!/usr/bin/env python

""" Anti-Cheat client :
    See all keys typed by all servers
"""

import socket
import json
import threading
import time
import random

import tkinter as tk
# todo : make auto install or use setup.py
from PIL import Image, ImageTk

DEFAULT_CLASSROOM = '201'
PORT = 2345

CHECK_CONN_HOST_INTERVAL = 10

# --- Socket related functions ---

def generate_ip_for_classroom(classroom:str=DEFAULT_CLASSROOM) -> list[str]:
    """
     Generate a list of IPs for a given classroom. Start at 10.205.{classroom}.100 to 10.205.{classroom}.251
     
     Args:
     	 classroom: The name of the classroom. Defaults to 201.
     
     Returns: 
     	 A list of IP addresses in dotted decimal format ( 10. 205. { classroom }. { i + 100 } )
    """
    return [f"10.205.{classroom}.{i+100}" for i in range(1, 151)]


def recv_host_key(s:socket.socket, host:str):
    """
     Receive host key from socket and add to list of keys in a loop as long as the host is connected

     todo : add timeout to revc so the programm can close (dont block until it receive)
     
     Args:
     	 s: socket to recieve data from. This is used to create a list of keys
     	 host: host to which the key is connected. This is used to determine the key type
     
     Returns: 
     	 None if everything went fine error message if something went wrong
    """
    global keys, isRunning

    while isRunning: # main loop
        try:
            data = s.recv(1024) # {'hostname': 'SIOP0201-EDU-11', 'keys': [{'key': 'maj', 'time': 1694068657.8892527}]}
        except socket.error:
            return f"Connection timed out by {host} 💥"

        if not data:
            return f"Connection closed by {host} 🚧"
        
        try:
            data_json = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError: # the keys on the server are longer than 1024 characters
            print(f"can't decode : {data.decode('utf-8')}")

        hostname = data_json.get("hostname")

        hosts_connected_name[host]["hostname"] = hostname

        # create new list of keys for this host or append to existing list
        keys.setdefault(hostname, []).extend(data_json.get("keys"))

        print(f"{hostname} > {''.join([k['key'] for k in data_json.get('keys')])}")


def conn_host(host:str):
    """
     Connect to a host and receive keystrokes from it.
     
     Args:
     	 host: The host to connect to
    
    """
    global keys, hosts_connected_name

    if host in hosts_connected_name: return # if the host is already connected, don't reconnect to it


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1) # so it don't try to connect for too long

        try: s.connect((host, PORT))

        except socket.timeout: return # if you can't connect just return

        s.settimeout(None) # so it cant wait until it receives data

        # New connection
        print(f"New connection to {host} 🛫")
        hosts_connected_name[host] = {"hostname" : None, "component" : None}

        recv_host_key(s, host)


    hosts_connected_name.pop(host)


def try_to_connect_to_classroom(classroom:str=DEFAULT_CLASSROOM):
    """
     Try to connect to every host in a classroom.
     
     Args:
     	 classroom: Name of the classroom
    """
    """Try to connect to every host in a given classroom"""
    for ip in generate_ip_for_classroom(classroom):
        threading.Thread(target=conn_host, args=(ip,)).start()


def try_to_connect_to_classroom_for_ever():
    """
     Try to connect to classroom for ever. This is a long running function that will wait CHECK_CONN_HOST_INTERVAL between attempts
    """
    global isRunning

    while isRunning:
        try_to_connect_to_classroom(DEFAULT_CLASSROOM)

        time.sleep(CHECK_CONN_HOST_INTERVAL)

# --- Other functions ---

def on_window_close(root:tk.Tk):
    """
     Called when the window is closed. This is a callback function to be called when Tk is about to close the window
     
     Args:
     	 root: The root window
    """
    global isRunning

    isRunning = False
    root.destroy()

# --- Components ---

class Student(tk.Frame):
    """Frame to display the keys of a student"""
    def __init__(self, parent, name, keys, icon):
        """
         Initialize the Student Frame. This is the top level function called by Tkinter to initialize the frame
         
         Args:
         	 parent: The parent widget of the frame
         	 name: The name of the student's name ( string )
         	 icon: The icon to display ( string ). It is used as a logo
        """
        tk.Frame.__init__(self, parent)

        self.configure(bg="white")

        self.img_student = tk.Label(self, image=icon)
        self.img_student.grid(row=0, column=0)

        self.lbl_student = tk.Label(self, text=name)
        self.lbl_student.grid(row=1, column=0)

        self.lbl_touches = tk.Label(self, text=keys, bg="#EFEFEF", width=100, height=3, anchor="w", padx=50, font=("Arial", 15))
        self.lbl_touches.grid(row=0, column=1, rowspan=2, padx=15)

    def set_keys(self, keys:list[str]):

        self.lbl_touches.config(text=keys[-20:])


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


class Notification(tk.Frame):
    """Notification Frame."""
    def __init__(self, parent, text, color, close_img, on_close=None):
        """
         Initialize the Tkinter notification frame. This is the top level function called by Tkinter to initialize the notification frame
         
         Args:
         	 parent: The parent widget of the frame
         	 text: The text to display in the notification label. Max length is 16 characters
         	 color: The color of the background of the button.
         	 close_img: The image to use for the close button.
         	 on_close: The function to call when the button is closed.
        """
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.on_close = on_close

        self.configure(bg=color, width=200, height=50)

        self.button_close = tk.Button(self, image=close_img, width=13, height=12, bd=0, bg=color,
                                      activebackground=color, command=self.close)
        
        self.button_close.place(relx=1, rely=0, anchor="ne")

        self.lbl_notification = tk.Label(self, text=text if len(text) < 30 else text[0:30] + "...", font=("Arial", 9), bg=color)
        self.lbl_notification.place(relx=0.5, rely=0.5, anchor="center", relwidth=1)

    def show(self, root):
        """
         Show the notification with an animation.
         
         Args:
         	 root: Root element of tkinter
        """
        relx = float(self.place_info()["relx"])
        if relx > 0.99:
            # move from 0.01 every 5 miliseconds
            self.place_configure(relx=relx-0.01)
            root.after(5, lambda: self.show(root))

    def close(self):
        """
         Close the notification and call the on_close callback if it has been set. This is called when the user presses the close button
        """
        self.on_close() if self.on_close else None
        self.destroy()


def update_window(root, students, icon):
    """update the number of students and their keys on the window"""
    global notification_manager, hosts_connected_name

    for host in hosts_connected_name.values():
        if host["hostname"] is None: continue # if the host has send no keys, skip it

        if "component" in host and host["component"] is None: # if the host has no component, add it else add keys to the component
            print(f"Adding {host['hostname']}...")

            s = Student(students, host["hostname"], [key['key'] for key in keys[host["hostname"]]], icon)
            s.pack(anchor="w", pady=10)
            host["component"] = s

        else:
            host["component"].set_keys([key['key'] for key in keys[host["hostname"]]])
    
    root.after(1000, lambda: update_window(root, students, icon))


def main():
    """
     Main function of Anti-Cheat. Sets up and starts the Tk application and all its
    """
    global isRunning, notification_manager

    # Colors
    dark = "#3F4962"
    green = "#A0C553"
    red = "#FC5855"
    blue = "#44B8B9"
    yellow = "#FBD04E"


    # Window
    root = tk.Tk()
    root.title("Anti-Cheat")
    root.configure(bg="white")
    root.geometry("1400x800+100+100")
    root.protocol("WM_DELETE_WINDOW", lambda: on_window_close(root))

    # set default options
    root.wm_attributes("-transparentcolor", "blue")
    root.option_add("*activeBackground", dark)
    root.option_add("*highlightThickness", 0)
    root.option_add("*Button*cursor", "hand2")
    root.option_add("*Background", "white")


    # Icons
    icon_refresh = ImageTk.PhotoImage(Image.open("icons/refresh_white.png").resize((25, 25)))
    icon_list = ImageTk.PhotoImage(Image.open("icons/list_white.png").resize((25, 25)))
    icon_download = ImageTk.PhotoImage(Image.open("icons/download_white.png").resize((20, 25)))
    icon_upload = ImageTk.PhotoImage(Image.open("icons/upload_white.png").resize((20, 25)))
    icon_close_white = ImageTk.PhotoImage(Image.open("icons/close_white.png").resize((25, 25)))
    icon_close_black = ImageTk.PhotoImage(Image.open("icons/close_black.png").resize((12, 15)))
    icon_computer = ImageTk.PhotoImage(Image.open("icons/computer_black.png").resize((60, 50))) # ! big

    notification_manger.init(root, icon_close_black)

    # Tool menu
    tool_menu = tk.Frame(root, height=100, bg=dark)
    tool_menu.pack(side=tk.TOP, fill=tk.X)

    tool_menu_left = tk.Frame(tool_menu, bg=dark)
    tool_menu_left.pack(side="left")

    tool_menu_right = tk.Frame(tool_menu, bg=dark)
    tool_menu_right.pack(side="right")

    tk.Button(tool_menu_left, image=icon_refresh, bg=dark, height=50, bd=0, command=lambda: notification_manger.add(f"hello {random.randint(0, 100)}!", green)).grid(row=0, column=0, padx=20)
    tk.Button(tool_menu_right, image=icon_list, bg=dark, height=50, bd=0).grid(row=0, column=3, padx=20)
    tk.Button(tool_menu_right, image=icon_download, bg=dark, height=50, bd=0).grid(row=0, column=4)
    tk.Button(tool_menu_right, image=icon_upload, bg=dark, height=50, bd=0).grid(row=0, column=5, padx=15)

    tk.Label(tool_menu_left, text="Classe :", bg=dark, fg="white").grid(row=0, column=1)

    txt_classroom = tk.Entry(tool_menu_left, bg=dark, fg="white", highlightbackground=red, highlightthickness=1, highlightcolor=red, bd=0)
    txt_classroom.grid(row=0, column=2)

    # Eleves frame
    students = tk.Frame(root)
    students.pack(fill=tk.BOTH, expand=1, padx=20, pady=20)

    Student(students, "SIOP-EDU0201-01", "test", icon_computer).pack(anchor="w", pady=10)

    # update_window(root, students, icon_computer)

    # notification_manger.add("10.205.201.211 connected", green)
    # notification_manger.add("10.205.201.211 disconnected", red)
    # notification_manger.add("10.205.201.213 connected", green)
    
    # notification_manger.add("10.205.201.214 connected", green)


    root.mainloop()
    


if __name__ == "__main__":
    keys = {}
    hosts_connected_name = {}
    isRunning = True
    notification_manger = NotificationManager()
    threading.Thread(target=try_to_connect_to_classroom_for_ever).start()
    main()