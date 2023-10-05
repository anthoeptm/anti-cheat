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

DEFAULT_CLASSROOM = '201'
PORT = 2345

CHECK_CONN_HOST_INTERVAL = 10

# --- Windows ---

class SettingsWindow(tk.Toplevel):
    """Window to change the settings"""

    def __init__(self, parent, colors):
        global auto_refresh, display_on_connexion_notif, display_on_disconnexion_notif, check_conn_host_interval

        tk.Toplevel.__init__(self, parent)

        self.title("Paramètres")
        self.resizable(False, False)
        self.geometry("480x600")

        self.colors = colors
        self.parent = parent

        tk.Label(self, text="Paramètres", font=("Arial", 20)).pack(anchor="w", padx=30, pady=10)
        self.auto_refesh = tk.BooleanVar(value=auto_refresh)
        tk.Checkbutton(self, text="Auto-refresh", activebackground=colors["white"], command=self.toogle_auto_refresh, variable=self.auto_refesh).pack(anchor="w", padx=40, pady=10)

        tk.Label(self, text="Intervale de refresh (secondes)").pack(anchor="w", padx=40)
        self.interval = tk.StringVar(value=str(check_conn_host_interval))
        tk.Entry(self, validate="focusout", validatecommand=self.change_interval, textvariable=self.interval).pack(anchor="w", padx=40)

        tk.Label(self, text="Thème de couleur", font=("Arial", 13)).pack(anchor="w", padx=40, pady=15)

        self.color_frame = tk.Frame(self)

        self.lbl_of_colors = {
            "dark" : "Menu",
            "green" : "Notifications connexion",
            "red" : "Notifications déconnexion",
            "blue" : "Fond popup",
            "yellow" : "Fond liste noir",
            "white" : "Fond fenêtres",
            "gray" : "Fond touches"
        }

        self.colors_frame = []

        for idx, color in enumerate(colors.keys()):
            cur_color_frame = tk.Frame(self.color_frame)

            btn_change_color = tk.Button(cur_color_frame, background=colors[color], width=5, height=2, relief="solid", bd=1, activebackground=colors[color])
            btn_change_color.config(command=lambda color=color, btn=btn_change_color: self.on_color_click(color, btn))
            btn_change_color.pack()

            tk.Label(cur_color_frame, text=self.lbl_of_colors.setdefault(color, "...")).pack()
            cur_color_frame.grid(row=(idx)//3, column=(idx)%3)
            self.colors_frame.append(cur_color_frame)

        self.color_frame.pack(anchor="w", padx=50, pady=10)

        tk.Label(self, text="Notifications à afficher", font=("Arial", 13)).pack(anchor="w", padx=40, pady=15)
        self.on_connexion_notif = tk.BooleanVar(value=display_on_connexion_notif)
        tk.Checkbutton(self, text="Connexion d'un éléve", activebackground=colors["white"], command=self.toogle_on_connexion_notif, variable=self.on_connexion_notif).pack(anchor="w", padx=50)
        self.on_disconnexion_notif = tk.BooleanVar(value=display_on_disconnexion_notif)
        tk.Checkbutton(self, text="Déconnexion d'un élève", activebackground=colors["white"], command=self.toogle_on_disconnexion_notif, variable=self.on_disconnexion_notif).pack(anchor="w", padx=50)

    def toogle_auto_refresh(self):
        """Change the auto-refresh setting"""
        global auto_refresh
        auto_refresh = self.auto_refesh.get()

    def toogle_on_connexion_notif(self):
        """Change the on_connexion_notif setting"""
        global display_on_connexion_notif
        display_on_connexion_notif = self.on_connexion_notif.get()

    def toogle_on_disconnexion_notif(self):
        """Change the on_disconnexion_notif setting"""
        global display_on_disconnexion_notif
        display_on_disconnexion_notif = self.on_disconnexion_notif.get()

    def change_interval(self):
        """Change the check_conn_host_interval setting"""
        global check_conn_host_interval
        try:
            check_conn_host_interval = int(self.interval.get())
            return True
        
        except ValueError:
            self.interval.delete(0, tk.END)
            self.interval.insert(tk.END, str(check_conn_host_interval))
            return False


    def on_color_click(self, color, btn):
        """Change a color for the entire application"""
        old_color = self.colors[color]
        user_color = askcolor(parent=self)
        self.colors[color] = user_color[1]
        btn.config(background=user_color[1])
        update_colors(self.parent, old_color, user_color[1])


# --- Components ---

class Student(tk.Frame):
    """Frame to display the keys of a student"""
    def __init__(self, parent, name, keys, icon, colors):
        """
         Initialize the Student Frame.
         This is the top level function called by Tkinter to initialize the frame
         
         Args:
         	 parent: The parent widget of the frame
         	 name: The name of the student's name ( string )
         	 icon: The icon to display ( string ). It is used as a logo
        """
        tk.Frame.__init__(self, parent)

        self.configure(bg=colors["white"])

        self.img_student = tk.Label(self, image=icon)
        self.img_student.grid(row=0, column=0)

        self.lbl_student = tk.Label(self, text=name)
        self.lbl_student.grid(row=1, column=0)

        self.lbl_touches = tk.Label(self, text=keys, bg=colors["gray"], width=100, height=3, anchor="w", padx=50, font=("Arial", 15))
        self.lbl_touches.grid(row=0, column=1, rowspan=2, padx=15)

    def set_keys(self, keys:list[str]):

        self.lbl_touches.config(text=keys[-20:])


class Notification(tk.Frame):
    """Notification Frame."""
    def __init__(self, parent, text, color, close_img, on_close=None):
        """
         Initialize the Tkinter notification frame.
         This is the top level function called by Tkinter to initialize the notification frame
         
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

        self.button_close = tk.Button(self, image=close_img, width=20, height=20, bd=0, bg=color,
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
         Close the notification and call the on_close callback if it has been set.
         This is called when the user presses the close button
        """
        self.on_close() if self.on_close else None
        self.destroy()

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

def update_window(root, students, icon, colors):
    """update the number of students and their keys on the window"""
    global notification_manager, client

    for host in client.hosts_connected_name.values():
        if host["hostname"] is None: continue # if the host has send no keys, skip it

        if "component" in host and host["component"] is None: # if the host has no component, add it else add keys to the component
            print(f"Adding {host['hostname']}...")

            s = Student(students, host["hostname"], [key['key'] for key in keys[host["hostname"]]], icon, colors)
            s.pack(anchor="w", pady=10)
            host["component"] = s

        else:
            host["component"].set_keys([key['key'] for key in keys[host["hostname"]]])
    
    root.after(1000, lambda: update_window(root, students, icon))


def all_children(wid, finList=None, indent=0):
    """https://stackoverflow.com/questions/7290071/getting-every-child-widget-of-a-tkinter-window"""
    finList = finList or []
    children = wid.winfo_children()
    for item in children:
        finList.append(item)
        all_children(item, finList, indent + 1)
    return finList

def update_colors(root:tk.Tk, old, new):
    for widget in all_children(root):
        print(widget)
        print(widget.cget("bg"), old)
        if widget.cget("bg") == old:
            widget.configure(bg=new)


def main():
    """
     Main function of Anti-Cheat.
     Sets up and starts the Tk application and all its
    """
    global isRunning, notification_manager

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
    root.configure(bg="white")
    root.geometry("1400x800+100+100")
    root.protocol("WM_DELETE_WINDOW", lambda: on_window_close(root))

    # set default options
    root.wm_attributes("-transparentcolor", "blue")
    root.option_add("*activeBackground", colors["dark"])
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
    icon_settings = ImageTk.PhotoImage(Image.open("icons/settings_white.png").resize((25, 25)))

    notification_manger.init(root, icon_close_black)

    # Tool menu
    tool_menu = tk.Frame(root, height=100, bg=colors["dark"])
    tool_menu.pack(side=tk.TOP, fill=tk.X)

    tool_menu_left = tk.Frame(tool_menu, bg=colors["dark"])
    tool_menu_left.pack(side="left")

    tool_menu_right = tk.Frame(tool_menu, bg=colors["dark"])
    tool_menu_right.pack(side="right")

    tk.Button(tool_menu_left, image=icon_refresh, bg=colors["dark"], height=50, bd=0, command=lambda: notification_manger.add(f"hello {random.randint(0, 100)}!", colors["green"])).grid(row=0, column=0, padx=20)
    tk.Button(tool_menu_right, image=icon_list, bg=colors["dark"], height=50, bd=0).grid(row=0, column=3, padx=20)
    tk.Button(tool_menu_right, image=icon_download, bg=colors["dark"], height=50, bd=0).grid(row=0, column=4)
    tk.Button(tool_menu_right, image=icon_upload, bg=colors["dark"], height=50, bd=0).grid(row=0, column=5, padx=15)
    tk.Button(tool_menu_right, image=icon_settings, bg=colors["dark"], height=50, bd=0, command=lambda: SettingsWindow(root, colors).grab_set()).grid(row=0, column=6, padx=15)

    tk.Label(tool_menu_left, text="Classe :", bg=colors["dark"], fg="white").grid(row=0, column=1)

    txt_classroom = tk.Entry(tool_menu_left, bg=colors["dark"], fg="white", highlightbackground=colors["red"], highlightthickness=1, highlightcolor=colors["red"], bd=0)
    txt_classroom.grid(row=0, column=2)

    # Eleves frame
    students = tk.Frame(root)
    students.pack(fill=tk.BOTH, expand=1, padx=20, pady=20)

    Student(students, "SIOP-EDU0201-01", "test", icon_computer, colors).pack(anchor="w", pady=10)

    # update_window(root, students, icon_computer, colors)

    root.mainloop()
    

if __name__ == "__main__":
    keys = {}
    hosts_connected_name = {}
    isRunning = True
    notification_manger = NotificationManager()

    # Variables for settings
    auto_refresh = True
    check_conn_host_interval = CHECK_CONN_HOST_INTERVAL
    display_on_connexion_notif = True
    display_on_disconnexion_notif = True

    # client = SocketClient(DEFAULT_CLASSROOM, PORT, CHECK_CONN_HOST_INTERVAL)

    # threading.Thread(target=client.try_to_connect_to_classroom_for_ever).start()
    main()