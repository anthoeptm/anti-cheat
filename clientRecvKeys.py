#!/usr/bin/env python

""" Anti-Cheat client :
    Try to connect to all host in a classroom and receive all the keys
"""

from time import sleep
from threading import Thread
import socket
from json import loads, JSONDecodeError


class SocketClient:
    """A client that will connect to all host in a classroom and receive all the keys send by servers"""

    def __init__(self, classroom, port, check_interval, auto_refresh=True, on_connexion_closed=None, on_key_recv=None, on_connexion=None, on_error=None):
        """
         Initialize the instance that will connect to all host in a classroom and try to receive all keys send by servers

         Args:
         	 classroom: classroom to connect to.
         	 port: port to connect to. Should be between 0 and 65535
         	 check_interval: time between checks for connection in seconds. Should be bigger that 0.5 seconds
         	 on_connexion_closed: function to be call when a user disconnected
         	 on_key_recv: function to be call when the socket receive new keys from a host
         	 on_connexion: function to be call when a new host connect to the socket
         	 on_error: function to be call when an error occurs
        """

        self.classroom = classroom
        self.port = port
        self.check_interval = check_interval if check_interval > 0.5 else 0.5
        self.classroom_ips = self.generate_ip_for_classroom()

        self.is_running = True
        self.keys = {}
        self.hosts_connected_name = {}
        self.auto_refresh = auto_refresh

        self.on_connexion_closed = lambda host: on_connexion_closed(host) if on_connexion_closed else None
        self.on_key_recv = lambda keys: on_key_recv(keys) if on_key_recv else None
        self.on_connexion = lambda host: on_connexion(host) if on_connexion else None
        self.on_error = lambda error: on_error(error) if on_error else None

    def generate_ip_for_classroom(self) -> list[str]:
        """
         Generate a list of IPs for the classroom. Start at 10.205.{classroom}.100 to 10.205.{classroom}.251

         Returns: 
         	 A list of IP addresses in dotted decimal format ( 10. 205. { classroom }. { i + 100 } )
        """
        return [f"10.205.{self.classroom}.{i+100}" for i in range(1, 151)]
    

    def set_classroom(self, classroom:str):
        """
         Set the classroom to connect to
        """

        try:
            num_classroom = int(classroom)
        except ValueError:
            raise ValueError("Classroom should be an integer")

        if num_classroom < 100 or num_classroom > 255:
            raise ValueError("Classroom should be between 100 and 255")

        if classroom == self.classroom: return

        # generate new list of IPs for the classroom
        self.classroom = classroom
        self.classroom_ips = self.generate_ip_for_classroom()

        # disconnect from all hosts that are not in the classroom
        for host in self.hosts_connected_name.keys():
            if host not in self.classroom_ips:
                self.hosts_connected_name[host]["socket"].close()

        # Try to connect to all hosts of the classroom
        self.try_to_connect_to_classroom()


    def recv_host_key(self, s:socket.socket, host:str):
        """
         Receive host key from socket and add to list of keys in a loop as long as the host is connected

         Args:
         	 s: socket to recieve data from. This is used to create a list of keys
         	 host: host to which the key is connected. This is used to determine the key type

         Returns: 
         	 None if everything went fine error message if something went wrong
        """

        while self.is_running: # main loop
            try:
                data = s.recv(1024)
            except socket.timeout:
                continue
            except socket.error:
                self.on_connexion_closed(host)
                return #f"Connection timed out by {host} 💥"

            if not data:
                self.on_connexion_closed(host)
                return #f"Connection closed by {host} 🚧"

            try:
                data_json = loads(data.decode("utf-8")) # load the json from the data recv
            except JSONDecodeError as e: # the keys on the server are longer than 1024 characters
                self.on_error(e)

            hostname = data_json.get("hostname")

            self.hosts_connected_name[host]["hostname"] = hostname

            # create new list of keys for this host or append to existing list
            self.keys.setdefault(hostname, []).extend(data_json.get("keys"))

            self.on_key_recv(data_json)


    def conn_host(self, host:str):
        """
         Connect to a host and receive keystrokes from it.

         Args:
         	 host: The host to connect to

        """

        if host in self.hosts_connected_name.keys(): return # if the host is already connected, don't reconnect to it

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1) # so it don't try to connect for too long

            try: s.connect((host, self.port))

            except socket.timeout: return # if you can't connect just return

            # s.settimeout(None) # so it cant wait until it receives data

            # New connection
            self.on_connexion(host)

            if host not in self.hosts_connected_name.keys(): # if the host is not in the list
                self.hosts_connected_name[host] = {"hostname" : None, "component" : None, "socket" : s}
            else:
                self.hosts_connected_name[host]["socket"] = s
                self.hosts_connected_name[host]["hostname"] = None
            

            self.recv_host_key(s, host)

            # End of connection
            self.hosts_connected_name.pop(host) #if host in self.hosts_connected_name.keys() else None
        

    def try_to_connect_to_classroom(self):
        """
         Try to connect to every host in the classroom.
        """
        for ip in self.classroom_ips:
            Thread(target=self.conn_host, args=(ip,)).start()


    def try_to_connect_to_classroom_for_ever(self):
        """
         Try to connect to classroom for ever. This is a long running function that will wait self.check_interval between attempts
        """

        while self.is_running:
            if self.auto_refresh: # try to reconnect only if auto_refresh is True
                self.try_to_connect_to_classroom()

            sleep(self.check_interval)


if __name__ == "__main__":
    c = SocketClient("201", 2345, 1,
                    on_connexion=lambda host: print(f"✨ New connection to {host}"),
                    on_connexion_closed=lambda host: print(f"💀 Connexion closed by {host}"),
                    on_key_recv=lambda data: print(f"{data.get('hostname')} > {''.join([k['key'] for k in data.get('keys')])}"),
                    on_error=lambda error: print(f"🚑 Error : {error}"),
                    )
    
    c.try_to_connect_to_classroom_for_ever()