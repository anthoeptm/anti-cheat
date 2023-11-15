#!/usr/bin/env python

""" Anti-Cheat client :
    See all keys typed by all servers
    TODO    : add time to search db to divide by day
"""

import os
import sys
from threading import Thread
from time import sleep
from json import dumps, load
from pymongo import MongoClient, errors
from dotenv import load_dotenv

import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.simpledialog import askstring

from PIL import Image, ImageTk

from clientRecvKeys import SocketClient
from clientGui import Student, NotificationManager, SettingsWindow, BlacklistWindow, colors

DEFAULT_CLASSROOM = '201'
PORT = 2345

CHECK_CONN_HOST_INTERVAL = 10 # seconds

UPDATE_DB_INTERVAL = 5 # seconds


KEYS_TO_REMOVE = ["alt gr", "right shift", "maj", "ctrl droite", "ctrl", "alt", "haut", "bas", "gauche", "droite", "enter", "backspace", "verr.maj", "suppr", "fin", "origine", "pg.suiv", "pg.prec", "tab", "menu", "windows gauche", "impr.ecran"] # special keys (fr-CH layout)


def on_window_close(root:tk.Tk):
    """
     Stop the programm, the socket client and destroy the window.
     This is a callback function to be called when the button to close the window is pressed
     
     Args:
     	 root: The root window
    """
    global isRunning, client

    isRunning = False

    if "client" in globals(): # if the variable client exist
        client.is_running = False

    root.destroy()


def update_db_loop(interval):
    """Update the database with all the keys every {interval} seconds"""
    global isRunning, client_mongo

    while isRunning:
        sleep(interval)
        update_db()

    client_mongo.close()


def update_db():
    """Update the database with all the keys"""
    global db, keys, notification_manager, colors
    
    # insert into log collection
    col_keys = db["keys"]
    for host in keys.keys():
        for key in keys[host]:
            try:
                col_keys.insert_one({"hostname" : host, "key" : key["key"] if key["key"] != "space" else " ", "time" : key["time"]})
            except errors.PyMongoError as e: 
                notification_manager.add("DB erreur", colors["red"])
                print(e)
                continue

    # insert into search collection
    col_keys_search = db["keys-search"]
    for host in keys.keys():

        keys_text = "".join([key["key"] for key in keys[host]])
        keys_text = keys_text.replace("space", " ")

        old_keys_text = col_keys_search.find_one({"hostname" : host})

        if old_keys_text is None:
            col_keys_search.insert_one({"hostname" : host, "keys" : keys_text})
            continue

        try:
            col_keys_search.update_one({"hostname" : host},
                                       {"$set" : {"keys" : old_keys_text["keys"] + keys_text}},
                                       upsert=True)
        except errors.PyMongoError as e:
            notification_manager.add("DB erreur", colors["red"])
            print(e)
            continue

    for host in keys.keys():
        keys[host].clear()


def update_window(data, students, icon):
    """update the number of students and their keys on the window
    ! blacklist : makes no distinction between the host, they can all be part of the same progress for the words
    """
    global notification_manager, client

    keys_filtered = list(filter(lambda item: item["key"] not in KEYS_TO_REMOVE, data["keys"])) # remove the keys that are useless
    only_keys = [key["key"] for key in keys_filtered] # get only the keys
    only_keys = list(map(lambda key: key.replace("space", " "), only_keys))

    # check for word in blacklist
    for key in only_keys:
        for word in blacklist.keys():
            if key == word[blacklist[word]]: # the user has made some progress in typing the word
                blacklist[word] += 1
            
            else: # if he has stopped the progress reset it
                blacklist[word] = 0
            
            if len(word) == blacklist[word]:  # if the progress is egal to the len of the word he has found it
                notification_manager.add(f"{data.get('hostname')} à écrit {word}", colors["red"])
                blacklist[word] = 0

    # add keys to the right component
    host_ip = {v.get("hostname"): k for k, v in client.hosts_connected_name.items()} # {ip:hostname} https://stackoverflow.com/questions/483666/reverse-invert-a-dictionary-mapping

    host = client.hosts_connected_name[host_ip[data["hostname"]]] # get the host that has send the keys

    if host["component"]: # if there is already a component for this host
        host["component"].add_keys(only_keys)
        host["component"].update_name(data["hostname"]) # update the name of the component


    else: # if there is no component for this host, create a new one
        s = Student(students, host["hostname"], only_keys, icon, colors)
        s.pack(anchor="w", pady=10)
        host["component"] = s
        keys[data["hostname"]] = []

    if data["hostname"] in keys.keys():
        keys[data["hostname"]].extend(keys_filtered)
    else:
        keys[data["hostname"]] = keys_filtered


def on_connexion_closed(host, students):
    """Callback function to be called when the socket connection is closed"""
    global notification_manager

    if display_on_disconnexion_notif:
        notification_manager.add(f"Déconnexion de {host}", colors["red"])
    for student in students.winfo_children():
        if student == client.hosts_connected_name[host]["component"]:
            student.destroy()


def on_connexion_opened(host, students, icon):
    """Callback function to be called when the socket connection is opened"""
    global notification_manager, client

    s = Student(students, host, [], icon, colors)
    s.pack(anchor="w", pady=10)

    if host in client.hosts_connected_name.keys():
        client.hosts_connected_name[host]["component"] = s # get the host that has send the keys
    else:
        client.hosts_connected_name[host] = {"component" : s} # add the host

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


def export_to_json(db_name="keys"):
    """Export the keys to a json file (all the keys from the db)

    Args:
        db_name: the name of the database to get the keys from
    """
    global db, notification_manager

    # ask the user a file the save the json
    filename = asksaveasfilename(filetypes=[("json", "*.json")])
    if not filename or filename == "": return

    # load all the keys from the db
    if db_name == "keys":
        keys_to_load = get_keys_from_db()
    elif db_name == "keys-search":
        keys_to_load = get_keys_from_db("keys-search")
    else:
        notification_manager.add(f"DB {db_name} inconnue", colors["red"])
        return

    with open(filename, "w") as f:
        f.writelines(dumps(keys_to_load, indent=4))

    notification_manager.add(f"Export réussi ({filename})", colors["green"])


def import_json(students, icon):
    """Import the keys from a json file"""
    global notification_manager

    filename = askopenfilename(filetypes=[("json", "*.json")])
    if not filename or filename == "": return

    with open(filename, "r") as f:
        keys = load(f)

    for host in keys.keys():
        if host not in list(map(lambda host: host["hostname"] if "hostname" in host.keys() else "", client.hosts_connected_name.values())): # if the host is not currently connected
            print(f"import keys to host that is NOT connected ({host})")
            # create a new component
            client.hosts_connected_name[host] = {}
            s = Student(students, host, list(map(lambda key: key["key"], keys[host])), icon, colors)
            s.pack(anchor="w", pady=10)
            client.hosts_connected_name[host]["component"] = s

        else: # if the host is currently connected
            print(f"import keys to host that is connected ({host})")

            for host_connected in client.hosts_connected_name.keys(): # loop over each host to get the right one
                if client.hosts_connected_name[host_connected]["hostname"] == host:
                    client.hosts_connected_name[host_connected]["component"].set_keys(list(map(lambda key: key["key"], keys[host])))

    notification_manager.add(f"Import réussi ({filename})", colors["green"])


def get_keys_from_db(db_name="keys"):
    """
    Simply get all the info from the db

    -> "keys" has one document per keys\n  
    -> "keys-search" one document per hostname with all the keys in a string
    """
    global db

    if db_name == "keys-search":
        return list(db["keys-search"].find({}))

    # load all the keys from the db
    all_keys = db["keys"].find({})
    keys_to_return = {}

    for key in all_keys:
        key_to_load = {"key":key["key"],"time":key["time"]}
        if key["hostname"] in keys_to_return.keys():
            keys_to_return[key["hostname"]].append(key_to_load)
        else:
            keys_to_return[key["hostname"]] = [key_to_load]

    return keys_to_return


def reset_search():
    """Reset the search"""
    
    for host in client.hosts_connected_name.keys():
        if client.hosts_connected_name[host]["component"]:
            client.hosts_connected_name[host]["component"].lbl_touches.config(bg=colors["gray"])


def make_search(query):
    """
    Search some keys into all keys typed
    """
    global notification_manager

    try:
        all_keys = get_keys_from_db("keys-search")
    except BaseException as e:
        print(f"Error getting keys from db : {e}")


    num_of_res = 0

    for host_keys in all_keys:
        if query in host_keys["keys"]:
            num_of_res += 1           
            # if host in list(map(lambda host_conn: host_conn["hostname"], client.hosts_connected_name.values())): # if the host is connected
            print(f"Found '{query}' in {host_keys['hostname']}'s keys")
            for host_connected in client.hosts_connected_name.keys(): # loop over each host to get the right one
                if client.hosts_connected_name[host_connected]["hostname"] == host_keys["hostname"]: # right one
                    client.hosts_connected_name[host_connected]["component"].lbl_touches.config(bg=colors["red"])

    notification_manager.add(f"{num_of_res} résultats pour {query}", colors["green"])


def update_blacklist(new_blacklist):
    """Update the list of blacklisted words
    Called from BlacklistWindow"""
    global blacklist

    blacklist.clear()

    for word in new_blacklist:
        blacklist[word] = 0


def set_auto_refresh(value):
    """Set the auto refresh option"""
    global client
    client.auto_refresh = value

def set_on_disconnexion_notif(value):
    """Set the on disconnexion notification option"""
    global display_on_disconnexion_notif
    display_on_disconnexion_notif = value

def set_on_connexion_notif(value):
    """Set the on connection notification option"""
    global display_on_connexion_notif
    display_on_connexion_notif = value

def set_check_conn_host_interval(value):
    """Set the check connection host interval option"""
    global check_conn_host_interval
    check_conn_host_interval = value

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller https://stackoverflow.com/a/44352931"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def main():
    """
     Main function of Anti-Cheat.
     Sets up and starts the Tk application
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
    icon_refresh = ImageTk.PhotoImage(Image.open(resource_path("./icons/refresh_white.png")).resize((25, 25)))
    icon_download = ImageTk.PhotoImage(Image.open(resource_path("./icons/download_white.png")).resize((20, 25)))
    icon_upload = ImageTk.PhotoImage(Image.open(resource_path("./icons/upload_white.png")).resize((20, 25)))
    icon_close_black = ImageTk.PhotoImage(Image.open(resource_path("./icons/close_black.png")).resize((12, 15)))
    icon_computer = ImageTk.PhotoImage(Image.open(resource_path("./icons/computer_black.png")).resize((60, 50))) # ! big
    icon_settings = ImageTk.PhotoImage(Image.open(resource_path("./icons/settings_white.png")).resize((25, 25)))
    icon_blacklist = ImageTk.PhotoImage(Image.open(resource_path("./icons/blacklist.png")).resize((30, 30)))


    notification_manager.init(root, icon_close_black)

    # Tool menu
    tool_menu = tk.Frame(root, height=100, bg=colors["dark"])
    tool_menu.pack(side=tk.TOP, fill=tk.X)

    tool_menu_left = tk.Frame(tool_menu, bg=colors["dark"])
    tool_menu_left.pack(side="left")

    tool_menu_center = tk.Frame(tool_menu, bg=colors["dark"])
    tool_menu_center.pack(side="left")

    tool_menu_right = tk.Frame(tool_menu, bg=colors["dark"])
    tool_menu_right.pack(side="right")

    # Left tool menu
    tk.Button(tool_menu_left, image=icon_refresh, bg=colors["dark"], height=50, bd=0, command=lambda: client.try_to_connect_to_classroom()).grid(row=0, column=0, padx=20)
    tk.Label(tool_menu_left, text="Classe :", bg=colors["dark"], fg=colors["white"]).grid(row=0, column=1)

    txt_classroom = tk.Entry(tool_menu_left, bg=colors["dark"], fg=colors["white"], highlightbackground=colors["red"], highlightthickness=1, highlightcolor=colors["red"], bd=0)
    txt_classroom.insert(0, client.classroom)
    txt_classroom.grid(row=0, column=2)

    txt_classroom.bind("<Return>", lambda e, txt_classroom=txt_classroom: client.set_classroom(txt_classroom.get()))

    # Center tool menu
    search_bar = tk.Entry(tool_menu_center, width=100, bg=colors["dark"], fg=colors["white"], bd=0, highlightthickness=1, highlightbackground=colors["white"])
    search_bar.bind("<Return>", lambda e, search_bar=search_bar: make_search(search_bar.get()))
    search_bar.bind("<Key>", lambda e, colors=colors: reset_search())
    search_bar.insert(0, "Recherche...")
    search_bar.bind("<FocusIn>", lambda args: search_bar.delete(0, tk.END))
    search_bar.bind("<FocusOut>", lambda args: search_bar.delete(0, tk.END) or search_bar.insert(0, "Recherche..."))
    search_bar.pack(padx=50)

    # Right tool menu
    tk.Button(tool_menu_right, image=icon_blacklist, bg=colors["dark"], height=50, bd=0, command=lambda: BlacklistWindow(root, update_blacklist, default_blacklist=list(blacklist.keys()), position=(root.winfo_x(), root.winfo_y())).grab_set()).grid(row=0, column=3, padx=20)
    tk.Button(tool_menu_right, image=icon_upload, bg=colors["dark"], height=50, bd=0, command=lambda: export_to_json()).grid(row=0, column=5, padx=15)
    tk.Button(tool_menu_right, image=icon_settings, bg=colors["dark"], height=50, bd=0, command=lambda: SettingsWindow(root, update_colors, set_auto_refresh, set_on_disconnexion_notif, set_on_connexion_notif, set_check_conn_host_interval, CHECK_CONN_HOST_INTERVAL, client.auto_refresh, display_on_connexion_notif, display_on_disconnexion_notif, position=(root.winfo_x(), root.winfo_y())).grab_set()).grid(row=0, column=6, padx=15)


    # Eleves frame
    students = tk.Frame(root)
    students.pack(fill=tk.BOTH, expand=1, padx=20, pady=20)

    tk.Button(tool_menu_right, image=icon_download, bg=colors["dark"], height=50, bd=0, command=lambda students=students: import_json(students, icon_computer)).grid(row=0, column=4)
    # Student(students, "SIOP-EDU0201-01", "test", icon_computer).pack(anchor="w", pady=10)

    client.on_connexion = lambda host: on_connexion_opened(host, students, icon_computer)
    client.on_connexion_closed = lambda host: on_connexion_closed(host, students)
    client.on_key_recv = lambda data : update_window(data, students, icon_computer)

    client.try_to_connect_to_classroom()

    root.mainloop()


if __name__ == "__main__":
    load_dotenv() # load .env file into environment variables

    keys = {}
    # hosts_connected_name = {}
    isRunning = True
    blacklist = {} # {word:idx}
    notification_manager = NotificationManager()

    # Settings variables (changed from SettingsWindow and accesed by main)
    check_conn_host_interval = CHECK_CONN_HOST_INTERVAL
    display_on_connexion_notif = True
    display_on_disconnexion_notif = True

    # MongoDB
    connection_string = os.environ.get("MONGODB_URI")
    client_mongo = MongoClient(connection_string)
    
    db = client_mongo["anti-cheat"]

    Thread(target=update_db_loop, args=(UPDATE_DB_INTERVAL,)).start()

    # Socket
    client = SocketClient(DEFAULT_CLASSROOM, PORT, CHECK_CONN_HOST_INTERVAL)
    

    main()