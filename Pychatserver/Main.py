import tkinter as tk
from tkinter import messagebox
import ChatClient as client
import BaseEntry as entry
import BaseDialog as dialog
import threading
import argparse
import sys

class SocketThreadedTask(threading.Thread):
    def __init__(self, socket, **callbacks):
        threading.Thread.__init__(self)
        self.socket = socket
        self.callbacks = callbacks

    def run(self):
        while True:
            try:
                message = self.socket.receive()
                chat_history = ""

                if '&&&' in message:
                    print("The message is:\n")
                    print(message)

                    split_history = message.split("&&&")

                    print(str(message.split("&&&")))

                    chat_history = split_history[0]
                    message = split_history[1]


                print("The whole message is:\n" + message)

                if message == '/quit':
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window']('\n> You have been disconnected from the server.\n')
                    self.socket.disconnect()
                    break
                elif message == '/squit':
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window']('\n> The server was forcibly shutdown. No further messages are able to be sent\n')
                    self.socket.disconnect()
                    break
                elif 'joined the channel' in message or '|users:' in message:
                    split_message = message.split('|')
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window'](chat_history + split_message[0])
                    self.callbacks['update_user_list'](split_message[1].replace('users:', ''))

                elif 'left channel' in message:
                    split_message = message.split('|')
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window'](split_message[0])

                    if '[update channel]' in message:
                        self.callbacks['update_channel_list'](split_message[2])
                        print('inside update channel')
                    if '[update users]' in message:

                        if (len(split_message)) == 3:
                            self.callbacks['update_user_list'](split_message[2])
                        else:
                            self.callbacks['update_user_list'](split_message[4])
                elif 'changed your name' in message:
                    self.callbacks['update_chat_window'](split_message[0])
                    self.callbacks['update_user_list'](split_message[1])
                elif '[update channel]' in message:
                    print('GUI received update channel')
                    split_message = message.split('|')
                    self.callbacks['update_channel_list'](split_message[1])
                elif '[remove channel]' in message:
                    print('GUI received remove channel')
                    split_message = message.split('|')
                    self.callbacks['remove_channel_list'](split_message[1])
                elif '[update users]' in message:
                    print('GUI received update users')
                    split_message = message.split('|')
                    self.callbacks['update_user_list'](split_message[1])
                else:
                    self.callbacks['clear_prev_messages']()
                    print("Chat history in Main: " + chat_history)
                    self.callbacks['update_chat_window'](chat_history + message)
            except OSError:
                break

class ChatDialog(dialog.BaseDialog):
    def body(self, master):
        tk.Label(master, text="Enter host:").grid(row=0, sticky="w")
        tk.Label(master, text="Enter port:").grid(row=1, sticky="w")
        tk.Label(master, text="Enter username:").grid(row=2, sticky="w")
        tk.Label(master, text="Enter password:").grid(row=3, sticky="w")

        self.hostEntryField = entry.BaseEntry(master, placeholder="Enter host")
        self.portEntryField = entry.BaseEntry(master, placeholder="Enter port")
        self.usernameEntryField = entry.BaseEntry(master, placeholder="Optional")
        self.passwordEntryField = entry.BaseEntry(master, placeholder="Optional")

        self.hostEntryField.grid(row=0, column=1)
        self.portEntryField.grid(row=1, column=1)
        self.usernameEntryField.grid(row=2, column=1)
        self.passwordEntryField.grid(row=3, column=1)

        return self.hostEntryField

    def validate(self):
        host = str(self.hostEntryField.get())
        username = str(self.usernameEntryField.get())
        username = username if username != 'Optional' else ''  #For username to prompt only once
        password = str(self.passwordEntryField.get())
        password = password if password != 'Optional' else ''

        try:
            port = int(self.portEntryField.get())

            if (port >= 0 and port < 65536):
                self.result = (host, port, username, password)
                return True
            else:
                tk.messagebox.showwarning("Error", "The port number has to be between 0 and 65535. Both values are inclusive.")
                return False
        except ValueError:
            tk.messagebox.showwarning("Error", "The port number has to be an integer.")
            return False

class ChatWindow(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.initUI(parent)

    def initUI(self, parent):
        self.backgroundColor = 'LightSkyBlue1'
        self.backgroundListColor = 'cornflower blue'
        self.textColor = 'gray25'
        self.labelColor = 'floral white'
        self.labelBackgroundColor = "#152225"
        self.listBoxTextColor = '#fff'

        self.messageLabel = tk.Label(parent, fg=self.labelColor, bg=self.labelBackgroundColor, text="", height='0', justify='left')
        self.messageLabel.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.channelLabel = tk.Label(parent, fg=self.labelColor, bg=self.labelBackgroundColor, text="Channels:", height='0', justify='left')
        self.channelLabel.grid(row=0, column=4, sticky="nsew")

        self.usersLabel = tk.Label(parent, fg=self.labelColor, bg=self.labelBackgroundColor, text="Users:", height='0', justify='left')
        self.usersLabel.grid(row=0, column=5, sticky="nsew")

        self.messageTextArea = tk.Text(parent, height=34, bg=self.backgroundColor, fg=self.textColor, state=tk.DISABLED, wrap=tk.WORD)
        self.messageTextArea.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.messageScrollbar = tk.Scrollbar(parent, troughcolor="red", orient=tk.VERTICAL, command=self.messageTextArea.yview)
        self.messageScrollbar.grid(row=1, column=3, sticky="ns")

        self.messageTextArea['yscrollcommand'] = self.messageScrollbar.set

        self.channelsListBox = tk.Listbox(parent, fg=self.listBoxTextColor, bg=self.backgroundListColor)
        self.channelsListBox.grid(row=1, column=4, padx=5, sticky="nsew")

        self.usersListBox = tk.Listbox(parent, fg=self.listBoxTextColor, bg=self.backgroundListColor)
        self.usersListBox.grid(row=1, column=5, padx=5, sticky="nsew")

        self.entryField = entry.BaseEntry(parent, placeholder="Enter message.", width=80)
        self.entryField.grid(row=2, column=0, padx=5, pady=10, sticky="we")

        self.send_message_button = tk.Button(parent, text="Send", width=10, bg="#CACACA", activebackground="#CACACA")
        self.send_message_button.grid(row=2, column=1, padx=5, sticky="we")

    #  Insert a message to the chat
    def update_chat_window(self, message):
        self.messageTextArea.configure(state='normal')
        self.messageTextArea.insert(tk.END, message)
        self.messageTextArea.configure(state='disabled')
        self.messageTextArea.yview_pickplace("end")

    def update_user_list(self, user_message):
        users = user_message.split(' ')

        for user in users:
            if user not in self.usersListBox.get(0, tk.END):
                self.usersListBox.insert(tk.END, user)

    def update_channel_list(self, channel_message):

        print('in update channel list')
        channels = channel_message.split(' ')
        print(channels)

        if channels[0] != '':
            for channel in channels:

                if channel not in self.channelsListBox.get(0, tk.END):
                    self.channelsListBox.insert(tk.END, channel)

        else:
            self.channelsListBox.delete(0)

    def remove_channel_list(self, channel):
        print('in remove channel list')
        index = self.channelsListBox.get(0, tk.END).index(channel)
        print('Index is:', index)
        self.channelsListBox.delete(index)



    def remove_user_from_list(self, user):
        print(user)
        index = self.usersListBox.get(0, tk.END).index(user)
        self.usersListBox.delete(index)


    def clear_chat_window(self):
        if not self.messageTextArea.compare("end-1c", "==", "1.0"):
            self.messageTextArea.configure(state='normal')
            self.messageTextArea.delete('1.0', tk.END)
            self.messageTextArea.configure(state='disabled')

        if self.usersListBox.size() > 0:
            self.usersListBox.delete(0, tk.END)

        if self.channelsListBox.size() > 0:
            self.channelsListBox.delete(0, tk.END)

    def clear_prev_messages(self):
        if not self.messageTextArea.compare("end-1c", "==", "1.0"):
            self.messageTextArea.configure(state='normal')
            self.messageTextArea.delete('1.0', tk.END)
            self.messageTextArea.configure(state='disabled')

    def send_message(self, **callbacks):
        message = self.entryField.get()
        self.set_message("")
        callbacks['send_message_to_server'](message)

    def set_message(self, message):
        self.entryField.delete(0, tk.END)
        self.entryField.insert(0, message)

    def bind_widgets(self, callback):
        self.send_message_button['command'] = lambda sendCallback = callback : self.send_message(send_message_to_server=sendCallback)
        self.entryField.bind("<Return>", lambda event, sendCallback = callback : self.send_message(send_message_to_server=sendCallback))
        self.messageTextArea.bind("<1>", lambda event: self.messageTextArea.focus_set())


class ChatGUI(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)

        self.initWindow(root)
        self.initMenu(root)

        self.ChatWindow = ChatWindow(self.parent)

        self.clientSocket = client.Client()

        self.ChatWindow.bind_widgets(self.clientSocket.send)
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

    def initWindow(self, parent):
        self.parent = parent
        self.parent.title("Chat Application")
        self.parent.config(bg="#152225")

        screenSizeX = self.parent.winfo_screenwidth()
        screenSizeY = self.parent.winfo_screenheight()

        frameSizeX = 1200
        frameSizeY = 600

        framePosX = (screenSizeX - frameSizeX) / 2
        framePosY = (screenSizeY - frameSizeY) / 2

        self.parent.geometry('%dx%d+%d+%d' % (frameSizeX, frameSizeY, framePosX, framePosY - 25))
        self.parent.resizable(True, True)

    def initMenu(self, parent):
        self.parent = parent

        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

        self.mainMenu = tk.Menu(self.parent)
        self.parent.config(menu=self.mainMenu)

        self.subMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label='File', menu=self.subMenu)
        self.subMenu.add_command(label='Connect', command=self.connect_to_server)
        self.subMenu.add_command(label='Exit', command=self.on_closing)


    def connect_to_server(self, host = None, port= None, username = None ):
        if self.clientSocket.isClientConnected:
            tk.messagebox.showwarning("Info", "Already connected to the server.")
            return

        if (host and port):
            dialogResult = ""
        else:
            dialogResult = ChatDialog(self.parent).result

        if dialogResult or (host and port):
            if host and port:
                print("Host/Port: ", host, port)
                self.clientSocket.connect(host, port)
            elif dialogResult:
                print(dialogResult[0], dialogResult[1], dialogResult[2])
                self.clientSocket.connect(dialogResult[0], dialogResult[1])
                username = dialogResult[2] if dialogResult[2] else ''
                print("Username: ", username)


            if self.clientSocket.isClientConnected:
                self.ChatWindow.clear_chat_window()
                SocketThreadedTask(self.clientSocket, update_chat_window=self.ChatWindow.update_chat_window,
                                                      update_user_list=self.ChatWindow.update_user_list,
                                                      update_channel_list=self.ChatWindow.update_channel_list,
                                                      clear_chat_window=self.ChatWindow.clear_chat_window,
                                                      remove_user_from_list=self.ChatWindow.remove_user_from_list,
                                                      remove_channel_list=self.ChatWindow.remove_channel_list,
                                                      clear_prev_messages=self.ChatWindow.clear_prev_messages).start()
                if username:
                    self.clientSocket.send(username)
            else:
                tk.messagebox.showwarning("Error", "Unable to connect to the server.")

    def on_closing(self):
        if self.clientSocket.isClientConnected:
            self.clientSocket.send('/quit')

        self.parent.quit()
        self.parent.destroy()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-h', '--hostname', help='Select the hostname')
    parser.add_argument('-u', '--username', help='Select the username')
    parser.add_argument('-p', '--port', help='Select the server port')
    parser.add_argument('-c', '--conf_file', help='Select the configuration file')
    parser.add_argument('-t', '--test_file', help='Select the test file')
    parser.add_argument('-l', '--log', help='Select the file to log file')

    root = tk.Tk()
    chatGUI = ChatGUI(root)
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if (args.hostname != None):
            hostname = args.hostname
        if (args.username != None):
            username = args.username
        if (args.port != None):
            port = int(args.port)
        if (args.conf_file != None):
            conf_file = args.conf_file
        if (args.test_file != None):
            test_file = args.test_file
        if (args.log != None):
            log = (args.log)
        chatGUI.connect_to_server(hostname, port, username)


    root.mainloop()

