import tkinter as tk
from tkinter.colorchooser import askcolor

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

# --- Windows ---

class SettingsWindow(tk.Toplevel):
    """Window to change the settings"""

    def __init__(self, parent, update_colors, set_auto_refresh, set_display_on_disconnexion_notif, set_display_on_connexion_notif, set_check_conn_host_interval, default_check_conn_interval=10, default_auto_refresh=True, default_display_on_disconnexion_notif=True, default_display_on_connexion_notif=True):

        tk.Toplevel.__init__(self, parent)

        self.title("Paramètres")
        self.resizable(False, False)
        self.geometry("480x600")

        self.colors = colors
        self.parent = parent
        self.default_check_conn_interval = default_check_conn_interval
        self.update_colors = update_colors

        self.set_auto_refresh = set_auto_refresh
        self.set_display_on_disconnexion_notif = set_display_on_disconnexion_notif
        self.set_display_on_connexion_notif = set_display_on_connexion_notif
        self.set_check_conn_host_interval = set_check_conn_host_interval

        tk.Label(self, text="Paramètres", font=("Arial", 20)).pack(anchor="w", padx=30, pady=10)
        self.auto_refesh = tk.BooleanVar(value=default_auto_refresh)
        tk.Checkbutton(self, text="Auto-refresh", activebackground=colors["white"], command=self.toogle_auto_refresh, variable=self.auto_refesh).pack(anchor="w", padx=40, pady=10)

        tk.Label(self, text="Intervale de refresh (secondes)").pack(anchor="w", padx=40)
        self.interval = tk.StringVar(value=str(default_check_conn_interval))
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
        self.on_connexion_notif = tk.BooleanVar(value=default_display_on_connexion_notif)
        tk.Checkbutton(self, text="Connexion d'un éléve", activebackground=colors["white"], command=self.toogle_on_connexion_notif, variable=self.on_connexion_notif).pack(anchor="w", padx=50)
        self.on_disconnexion_notif = tk.BooleanVar(value=default_display_on_disconnexion_notif)
        tk.Checkbutton(self, text="Déconnexion d'un élève", activebackground=colors["white"], command=self.toogle_on_disconnexion_notif, variable=self.on_disconnexion_notif).pack(anchor="w", padx=50)

    def toogle_auto_refresh(self):
        """Change the auto-refresh setting"""
        self.set_auto_refresh(self.auto_refesh.get())

    def toogle_on_connexion_notif(self):
        """Change the on_connexion_notif setting"""
        self.set_display_on_connexion_notif(self.on_connexion_notif.get())

    def toogle_on_disconnexion_notif(self):
        """Change the on_disconnexion_notif setting"""
        self.set_display_on_disconnexion_notif(self.on_disconnexion_notif.get())

    def change_interval(self):
        """Change the check_conn_host_interval setting"""
        try:
            self.set_check_conn_host_interval(int(self.interval.get()))
            return True
        
        except ValueError:
            self.interval.delete(0, tk.END)
            self.interval.insert(tk.END, str(self.default_check_conn_interval))
            return False


    def on_color_click(self, color, btn):
        """Change a color for the entire application"""
        old_color = self.colors[color]
        user_color = askcolor(parent=self)
        self.colors[color] = user_color[1]
        btn.config(background=user_color[1])
        self.update_colors(self.parent, old_color, user_color[1])

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

        self.lbl_touches = tk.Label(self, bg=colors["gray"], width=100, height=3, anchor="w", padx=50, font=("Arial", 15))
        self.lbl_touches.grid(row=0, column=1, rowspan=2, padx=15)
        self.list_key = []
        self.add_keys(keys)

    def update_keys(self):
        self.lbl_touches.config(text=self.list_key[-20:])

    def add_keys(self, keys:list):
        self.list_key.extend(keys.copy())
        self.update_keys()


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

if __name__ == "__main__":
    print("This script is not meant to be run directly.")
    print("Exiting...")