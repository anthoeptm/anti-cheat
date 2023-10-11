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

        self.set_keys(keys)

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