#!/usr/bin/env python

""" Anti-Cheat client :
    See all keys typed by all servers
    TODO : add time to search db to divide by day make the buttons in the menu works
"""

import os
import threading
import random
import time
import json
import pymongo
from dotenv import load_dotenv

import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter.filedialog import askopenfilename, asksaveasfilename

from PIL import Image, ImageTk

from clientRecvKeys import SocketClient
from clientGui import Student, NotificationManager, colors

DEFAULT_CLASSROOM = '201'
PORT = 2345

CHECK_CONN_HOST_INTERVAL = 10 # seconds

UPDATE_DB_INTERVAL = 5 # seconds


KEYS_TO_REMOVE = ["alt gr", "right shift", "maj", "ctrl droit", "ctrl", "haut", "bas", "gauche", "droite", "enter"] # special keys

# --- Windows ---

class SettingsWindow(tk.Toplevel):
    """Window to change the settings"""

    def __init__(self, parent):
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
        self.update_colors(self.parent, old_color, user_color[1])

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


def update_db_loop(interval):
    """Update the database with all the keys every {interval} seconds"""
    while isRunning:
        time.sleep(interval)
        update_db()

def update_db():
    """Update the database with all the keys"""
    global db, keys, db_need_update

    if not db_need_update: return
    
    # insert into log collection
    col_keys = db["keys"]
    for host in keys.keys():
        for key in keys[host]:
            try:
                col_keys.insert_one({"hostname" : host, "key" : key["key"], "time" : key["time"]})
            except pymongo.errors.PyMongoError as e:
                print(e)
                continue

    # insert into search collection
    col_keys_search = db["keys-search"]
    for host in keys.keys():

        keys_text = "".join([key["key"] for key in keys[host]])

        old_keys_text = col_keys_search.find_one({"hostname" : host})

        if old_keys_text is None:
            col_keys_search.insert_one({"hostname" : host, "keys" : keys_text})
            continue

        try:
            col_keys_search.update_one({"hostname" : host},
                                       {"$set" : {"keys" : old_keys_text["keys"] + keys_text}},
                                       upsert=True)
        except pymongo.errors.PyMongoError as e:
            print(e)
            continue

    db_need_update = False
    keys.clear()



def update_window(data, students, icon):
    """update the number of students and their keys on the window"""
    global notification_manager, client, db_need_update

    data["keys"] = filter(lambda item: item["key"] not in KEYS_TO_REMOVE, data["keys"]) # remove the keys that are useless

    for host in client.hosts_connected_name.values():
        if host["hostname"] is None: continue # if the host has send no keys, skip it

        if "component" in host and host["component"] is None: # if the host has no component, add a component to it, else add keys to the component
            s = Student(students, host["hostname"], [key['key'] for key in data["keys"]], icon, colors)
            s.pack(anchor="w", pady=10)
            host["component"] = s

        if host["hostname"] in keys.keys(): # if the hostname has keys add them to the component
            host["component"].add_keys([key['key'] for key in data["keys"]])

        else: # else create an empty list to hold new keys
            keys[host["hostname"]] = []

    keys[host["hostname"]].extend(data["keys"])

    db_need_update = True

def create_component_for_host(host, students, icon, keys=None):
    global client

    print(client.hosts_connected_name)
    if client.hosts_connected_name[host]["component"]: return # if there is already a component for this host, skip it
    
    s = Student(students, host, keys or [], icon, colors)
    s.pack(anchor="w", pady=10)
    client.hosts_connected_name[host]["component"] = s


def on_connexion_closed(host, students):
    global notification_manager

    if display_on_disconnexion_notif:
        notification_manager.add(f"Déconnexion de {host}", colors["red"])
    for student in students.winfo_children():
        if student == client.hosts_connected_name[host]["component"]:
            student.destroy()

def on_connexion_opened(host):
    global notification_manager

    if display_on_connexion_notif:
        notification_manager.add(f"Connexion de {host}", colors["green"])


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

def export_to_json():
    """Export the keys to a json file
    TODO : test the code"""

    filename = asksaveasfilename(filetypes=[("json", "*.json")])
    with open(filename, "w") as f:
        f.writelines(json.dumps(keys, indent=4))

def import_json():
    """Import the keys from a json file
    TODO : test the code"""

    filename = askopenfilename(filetypes=[("json", "*.json")])
    with open(filename, "r") as f:
        keys = json.load(f)

    for host in keys.keys():
        if host not in client.hosts_connected_name.keys():
            client.hosts_connected_name[host] = {}
        client.hosts_connected_name[host]["component"] = None
        client.hosts_connected_name[host]["hostname"] = host
        client.hosts_connected_name[host]["keys"] = keys[host]
        

def main():
    """
     Main function of Anti-Cheat.
     Sets up and starts the Tk application and all its
    """
    global isRunning, notification_manager, client

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
    tk.Button(tool_menu_right, image=icon_settings, bg=colors["dark"], height=50, bd=0, command=lambda: SettingsWindow(root).grab_set()).grid(row=0, column=6, padx=15)

    tk.Label(tool_menu_left, text="Classe :", bg=colors["dark"], fg=colors["white"]).grid(row=0, column=1)

    txt_classroom = tk.Entry(tool_menu_left, bg=colors["dark"], fg=colors["white"], highlightbackground=colors["red"], highlightthickness=1, highlightcolor=colors["red"], bd=0)
    txt_classroom.grid(row=0, column=2)

    # Eleves frame
    students = tk.Frame(root)
    students.pack(fill=tk.BOTH, expand=1, padx=20, pady=20)

    # Student(students, "SIOP-EDU0201-01", "test", icon_computer).pack(anchor="w", pady=10)

    client.on_connexion = lambda host: on_connexion_opened(host)
    client.on_connexion_closed = lambda host: on_connexion_closed(host, students)
    client.on_key_recv = lambda data : update_window(data, students, icon_computer)

    root.mainloop()
    

if __name__ == "__main__":
    load_dotenv() # load .env file into environment variables

    keys = {}
    hosts_connected_name = {}
    isRunning = True
    notification_manager = NotificationManager()
    db_need_update = False

    # Settings variables (changed from SettingsWindow and accesed by main)
    auto_refresh = True
    check_conn_host_interval = CHECK_CONN_HOST_INTERVAL
    display_on_connexion_notif = True
    display_on_disconnexion_notif = True

    # MongoDB
    connection_string = os.environ.get("MONGODB_URI")
    client_mongo = pymongo.MongoClient(connection_string)
    db = client_mongo["anti-cheat"]

    threading.Thread(target=update_db_loop, args=(UPDATE_DB_INTERVAL,)).start()

    # Socket
    client = SocketClient(DEFAULT_CLASSROOM, PORT, CHECK_CONN_HOST_INTERVAL)
    client.try_to_connect_to_classroom()

    main()