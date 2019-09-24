import socket
import sys
import threading
import Channel
import User
import Util
import time
import os


class Server:
    SERVER_CONFIG = {"MAX_CONNECTIONS": 15}

    HELP_MESSAGE = """\n> The list of commands available are:

/help                                       - Show the instructions
/join <channel_name>                        - To create or switch to a channel.
/quit                                       - Exits the program.
/list                                       - Lists all available channels.
/version                                    - Lists current server version
/info                                       - Lists information about the server
/rules                                      - Lists the server rules
/away [<auto_response>]                     - Changes user's status to 'Away' if an 
                                              auto response is specified otherwise, 
                                              changes status to 'Online' 
/prvmsg <nickname> <message>               - Sends a private message to the user specified
/notice <nickname> <message>               - Sends a notice message to the user specified
/nick <nickname>                            - Sets  a nickname to be used
/time                                       - Displays local server time
/whois <nickname>                          - Displays queried user's information          
/who <name>                                 - Returns a list of users who match <name>
/userhost <nickname>[<space><nickname>]     - Returns a list of information about the nicknames specified
/topic <channel> [<topic]                   - Allows the client to query or set the channel topic on <channel>
/users                                      - Returns a list of users and information about those users
/invite <nickname> <channel>                - Invites <nickname> to the channel <channel>
/ison <nicknames>                           - Queries the server to see if the clients in the space-separated
                                              list <nicknames> are currently on the network
/part <channels>                            - Causes the user to leave the channels
/kick <nickname>                            - Forcibly removes the specified user from the channel 
                                              in the comma-separated list <channels>
/restart                                    - Restarts the server
/userip <nickname>                         - Requests the direct IP address of the user with the specified nickname
/mode <nickname> <a|s|c|u>                  - Sets the specified user's permissions to 
                                              (a)dmin, (s)ystem operator, (c)hannel operator or regular (u)ser
/mode <channel> <pb|pv>                     - Sets the specified channel to (pub) public or (pv) private
/pass                                       - Sets password for current user account
/die                                        - Instructs the server to shut down
/kill                                       - Forcibly removes a user from the network
/setname                                    - Allows a client to change the "real name"
/wallops                                    - Broadcasts a message to all System Operators currently on the server.
/silence <+|-><nickname>[<+|-><nickname>]   - Adds or removes the specified user(s) to/from a list of silenced
                                              users (i.e unable to send you private messages
/knock <channel> [<message>]                - Sends a notice to an private <channel> with an optional <message>, 
                                              requesting an invite
/ping <server>                              - Tests the presence of a connection
/connect <server> <port>                    - Instructs the server to connect to <server> on port <port>7
/users                                      - Displays all users currently on the server\n\n"""


    def __init__(self, host=socket.gethostbyname('localhost'), port=50000, allowReuseAddress=True, timeout=2, dbpath = './files/'):
        self.birthdate = time.strftime("%a, %d %b %Y %H:%M:%S ", time.localtime(time.time()))
        self.address = (host, port)
        self.channels = {}
        self.users_channels = {}
        self.users_curr_channel = {}
        self.client_thread_list = []  # A list of all threads that are either running or have finished their task.
        self.exit_signal = threading.Event()
        self.users = []  # A list of all the users who are connected to the server.
        self.users_file = dbpath + 'users.txt'
        self.channels_file = dbpath + 'channels.txt'
        self.banner_file = dbpath + 'banner.txt'
        self.oper_file = dbpath + "OpCredentials.txt"

        self.add_channels_to_server()

        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as errorMessage:
            sys.stderr.write("Failed to initialize the server. Error - {0}".format(errorMessage))
            raise

        self.serverSocket.settimeout(timeout)

        if allowReuseAddress:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.serverSocket.bind(self.address)
        except socket.error as errorMessage:
            sys.stderr.write('Failed to bind to address {0} on port {1}. Error - {2}'.format(self.address[0], self.address[1], errorMessage))
            raise

    def add_channels_to_server(self):

        with open(self.channels_file, 'r') as f:
            for line in f:
                if line != "":
                    channel_name = line.strip().split()[0]
                    self.channels[channel_name] = Channel.Channel(channel_name)

    def start_listening(self, defaultGreeting="\n> Welcome to our chat app!!! What is your full name?\n"):
        self.serverSocket.listen(Server.SERVER_CONFIG["MAX_CONNECTIONS"])

        try:
            while not self.exit_signal.is_set():
                try:
                    print("Waiting for a client to establish a connection\n")
                    clientSocket, clientAddress = self.serverSocket.accept()
                    print("Connection established with IP address {0} and port {1}\n".format(clientAddress[0], clientAddress[1]))
                    user = User.User(clientSocket, channel_messages={})
                    self.users.append(user)
                    self.welcome_user(user)
                    clientThread = threading.Thread(target=self.client_thread, args=(user,))
                    clientThread.start()
                    self.client_thread_list.append(clientThread)
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            self.exit_signal.set()

        for client in self.client_thread_list:
            if client.is_alive():
                client.join()

    def welcome_user(self, user):

        with open(self.banner_file, 'r') as f:
            banner = f.read()

        self.send_chat_message(user, (banner.format(self.address[0], sys.version, self.birthdate) + "\n"))


    def client_thread(self, user, size=4096):
        username = Util.generate_username(user.socket.recv(size).decode('utf8')).lower()
        while not username:
            self.send_chat_message(user, "\nPlease enter your username (no spaces)\n")
            username = Util.generate_username(user.socket.recv(size).decode('utf8')).lower()

            with open(self.users_file, 'r') as f:
                for line in f:
                    if (username == line.strip().split()[0]):
                        username = ""

        user.username = username
        with open(self.users_file, 'a') as f:
            f.write('{0} {1} {2} {3}\n'.format(user.username, '@', 'user', 'false'))


        welcomeMessage = '\n> Welcome {0}, type /help for a list of helpful commands.\n\n'.format(user.username)
        self.welcome_user(user)
        self.send_chat_message(user, welcomeMessage)

        while True:
            chatMessage = user.socket.recv(size).decode('utf8')

            if self.exit_signal.is_set():
                break

            if not chatMessage:
                break

            if '/quit' in chatMessage:
                self.quit(user)
                break
            elif '/list' in chatMessage:
                self.list_all_channels(user)
            elif '/help' in chatMessage:
                self.help(user)
            elif '/join' in chatMessage:
                self.join(user, chatMessage)
            elif '/part' in chatMessage:
                self.part(user, chatMessage)
            elif '/version' in chatMessage:
                self.version(user)
            elif '/info' in chatMessage:
                self.info(user)
            elif '/rules' in chatMessage:
                self.rules(user)
            elif '/away' in chatMessage:
                self.away(user, chatMessage)
            elif '/prvmsg' in chatMessage:
                self.prvmsg(user, chatMessage)
            elif '/notice' in chatMessage:
                self.notice(user, chatMessage)
            elif '/time' in chatMessage:
                self.time(user)
            elif '/nick' in chatMessage:
                self.nick(user, chatMessage)
            elif '/userhost' in chatMessage.lower():
                self.userhost(user, chatMessage)
            elif '/topic' in chatMessage:
                self.topic(user, chatMessage)
            elif '/whois' in chatMessage:
                self.whois(user, chatMessage)
            elif '/users' in chatMessage:
                self.userss(user)
            elif '/who' in chatMessage:
                self.who(user, chatMessage)
            elif '/ison' in chatMessage:
                self.ison(user, chatMessage)
            elif '/invite' in chatMessage:
                self.invite(user, chatMessage)
            elif '/restart' in chatMessage:
                self.restart(user)
            elif '/userip' in chatMessage:
                self.userip(user, chatMessage)
            elif '/mode' in chatMessage:
                self.mode(user, chatMessage)
            elif '/pass' in chatMessage:
                self.passs(user, chatMessage)
            elif '/setname' in chatMessage:
                self.setname(user, chatMessage)
            elif '/die' in chatMessage:
                self.die(user)
            elif '/kill' in chatMessage:
                self.kill(user, chatMessage)
            elif '/silence' in chatMessage:
                self.silence(user, chatMessage)
            elif 'wallops' in chatMessage:
                self.wallops(user, chatMessage)
            elif '/knock' in chatMessage:
                self.knock(user, chatMessage)
            elif '/ping' in chatMessage:
                self.ping(user, chatMessage)
            elif '/connect' in chatMessage:
                self.connect(user, chatMessage)
            elif '/oper' in chatMessage:
                self.oper(user, chatMessage)
            else:
                self.send_message(user, chatMessage)

        if self.exit_signal.is_set():
            user.socket.sendall('/squit'.encode('utf8'))

        user.socket.close()

    def quit(self, user):
        user.socket.sendall('/quit'.encode('utf8'))
        self.remove_user(user)

    def list_all_channels(self, user):
        if len(self.channels) == 0:
            chatMessage = "\n> No rooms available. Create your own by typing /join [channel_name]\n".encode('utf8')
            self.send_chat_message(user, chatMessage)
        else:
            chatMessage = '\n\n> Current channels available are: \n'
            for channel in self.channels:
                chatMessage += "    \n" + channel + ": " + str(len(self.channels[channel].users)) + " user(s)"
            chatMessage += "\n"
            self.send_chat_message(user, chatMessage)

    def help(self, user):
        self.send_chat_message(user, Server.HELP_MESSAGE)

    def version(self, user):
        self.send_chat_message(user,"" + sys.version)

    def away(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 1:
            auto_response = " ".join(splitMessage[1:])
            user.status = "Away"
            user.PRVMSG = auto_response
            self.send_chat_message(user, ("\n" + user.username + " is now away\n"))
        elif len(splitMessage) == 1:
            user.status = "Online"
            self.send_chat_message(user, ("\n" + user.username + " is no longer away\n"))
        else:
            self.help(user)

    def prvmsg(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 2:
            target = splitMessage[1]
            message = " ".join(splitMessage[2:])

            for auser in self.users:

                if auser.username == target:
                    self.send_chat_message(user, "\n[private_message][To: {0}]: {1}\n".format(auser.username, message))
                    if user.username in auser.block_list:
                        return
                    self.send_chat_message(auser, "\n[private_message]{0}: {1}\n".format(user.username, message))
                    if(auser.status == "Away"):
                        self.send_chat_message(auser, ("[Away]: " + auser.PRVMSG + "\n"))
        else:
            self.help(user)

    def notice(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 2:

            target = splitMessage[1]
            message = " ".join(splitMessage[2:])

            for auser in self.users:

                if auser.username == target:
                    self.send_chat_message(user, "\n[notice][To: {0}]: {1}\n".format(auser.username, message))
                    self.send_chat_message(auser, "\n[notice]{0}: {1}\n".format(user.username, message))
        else:
            self.help(user)


    def userip(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 1:
            target = splitMessage[1]
            for auser in self.users:

                if auser.username == target:
                    self.send_chat_message(user, "\n{0}'s IP Address: {1}".format(auser.username, auser.socket.getsockname()[0] + "\n"))

        else:
            self.help(user)

    def mode(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 2:

            target = splitMessage[1]
            flag = "".join(splitMessage[2:])
            text = []
            channels_text = []

            for auser in self.users:
                    if auser.username == target:
                        auser.usertype = flag

            with open(self.users_file, 'r') as f:
                for line in f:
                    if target == line.split()[0]:
                        cred = line.split()
                        if flag == "a":
                            cred[2] = "admin"
                            for auser in self.users:
                                self.send_chat_message(auser,"\n{0} is now a Server Admin \n".format(target))
                        if flag == "s":
                            cred[2] = "sysop"
                            for auser in self.users:
                                self.send_chat_message(auser,"\n{0} is now an System Operator \n".format(target))
                        if flag == "c":
                            cred[2] = "channelop"
                            for auser in self.users:
                                self.send_chat_message(auser,"\n{0} is now a Channel Operator \n".format(target))
                        if flag == "u":
                            cred[2] = "user"
                            for auser in self.users:
                                self.send_chat_message(auser,"\n{0} is now a Regular user \n".format(target))

                        text.append(" ".join(cred) + "\n")
                    else:
                        text.append(line)

            with open(self.users_file, 'w') as f:
                for line in text:
                    f.write(line)

            for achannel in self.channels:
                if achannel == target:
                    self.channels[target].mode = flag

            with open(self.channels_file, 'r') as f:
                 for line in f:
                     if target == line.split()[0]:
                        cred = line.split()
                        if flag == "pub" :
                            cred[3] = "pub"
                            for auser in self.channels[target].users:
                                self.send_chat_message(auser,"\n{0} has been switched to public \n".format(self.channels[target].channel_name))
                        if flag == "prv" :
                            cred[3] = "prv"
                            for auser in self.channels[target].users:
                                self.send_chat_message(auser,"\n{0} has been switched to private \n".format(self.channels[target].channel_name))
                        channels_text.append(" ".join(cred) + "\n")
                     else:
                        channels_text.append(line)
            with open(self.channels_file, 'w') as f:
                for line in channels_text:
                    f.write(line)

        else:
            self.help(user)

    def passs(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 1:
            password = "".join(splitMessage[1:])
            user.password = password
            self.send_chat_message(user, "\nPassword has been set to {0}\n".format(password))
            text = []

            with open(self.users_file, 'r') as f:
                for line in f:
                    if user.username == line.split()[0]:
                        cred = line.split()
                        cred[1] = password
                        text.append(" ".join(cred) + "\n")
                    else:
                        text.append(line)

            with open(self.users_file, 'w') as f:
                for line in text:
                    f.write(line)

        else:
            self.help(user)


    def kill (self, user, chatMessage):
        if user.usertype == "u" or user.usertype == "c":
            self.send_chat_message(user, "\nYou do not have permission to perform this command\n")
            return

        splitMessage = chatMessage.split()

        if len(splitMessage) > 1:

            target = splitMessage[1]

            for auser in self.users:
                if auser.username == target:
                    self.quit(auser)
                    self.send_chat_message(user,"\n{0} has been removed from the network\n".format(auser.username))

        else:
            self.help(user)

    def setname(self, user, chatMessage):
        splitMessage = chatMessage.split()

    def wallops(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 1:
            message = " ".join(splitMessage[1:])

            self.send_chat_message(user, "\n[Operator Broadcast]: {0}\n".format(message))
            for auser in self.users:
                if auser.usertype == "s":
                    self.send_chat_message(auser, "\n[Operator Broadcast]: {0}\n".format(message))
        else:
            self.help(user)

    def silence(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 1:

            for token in splitMessage:

                for auser in self.users:

                    if token[0] == '+':
                        if auser.username == token[1:]:
                            user.block_list.append(auser.username)
                            self.send_chat_message(user, "\n{0} has been silenced\n".format(auser.username))
                    elif token[0] == '-':
                        if auser.username == token[1:]:
                            user.block_list.remove(auser.username)
                            self.send_chat_message(user, "\n{0}is no longer silenced\n".format(auser.username))
        else:
            self.help(user)


    def knock (self, user, chatMessage):
        splitMessage = chatMessage.split()

        if len(splitMessage) > 2:

            targetchannel = splitMessage[1]
            message = " ".join(splitMessage[2:])

            if targetchannel in self.channels:
                self.send_chat_message(user, "\n[Knock][To: {0}]: {1}\n".format(targetchannel, message))
                for auser in self.channels[targetchannel].users:
                    self.send_chat_message(auser, "\n[Knock][{0}]{1}: {2}\n".format(targetchannel, user.username, message + "\n"))
        elif len(splitMessage) == 2:

            targetchannel = splitMessage[1]
            message = "would like an invite to this channel"

            if targetchannel in self.channels:
                self.send_chat_message(user, "\n[Knock][To: {0}]".format(targetchannel))
                for auser in self.channels[targetchannel].users:
                    self.send_chat_message(auser, "\n[Knock][{0}]{1} {2}\n".format(targetchannel, user.username, message))

        else:
            self.help(user)

    def oper(self,user,chatMessage):


        splitMessage = chatMessage.split()

        if len(splitMessage) > 2:

            username = splitMessage[1]
            password = splitMessage[2]

            f = open(self.oper_file, 'r')

            string = f.readlines()

            for i in range (0, len(string) ):

                cred = string[i].split()

                username2 = cred[0]
                password2 = cred[1]

                print(username, username2, password, password2)

                if username == username2 and password == password2:
                    user.usertype = "s"
                    self.send_chat_message(user, "\nYou are now an System Operator \n")
            f.close()
            text = []
            with open(self.users_file, 'r') as f:
                for line in f:
                    if user.username == line.split()[0]:
                        cred = line.split()
                        cred[2] = "sysop"
                        text.append(" ".join(cred) + "\n")
                    else:
                        text.append(line)
            with open(self.users_file, 'w') as f:
                for line in text:
                    f.write(line)

        else:
            self.help(user)


    def rules(self, user):
        self.send_chat_message(user, """\n 
Rules & Regulations:
====================
Rule 1: No spamming
Rule 2: No personal attacks or harassment
Rule 3: Type in normal English
Rule 4: Don't monopolize the conversation
Rule 5: No solicitation\n\n""")
    def info(self, user):
        info_str = """\n 

Server Birthdate: """ + self.birthdate + """ \nEnd of /INFO list.\n\n"""
        self.send_chat_message(user, info_str)

    def join(self, user, chatMessage):
        if len(chatMessage.split()) >= 2:
            channelName = chatMessage.split()[1]

            if channelName[0] != '#' and channelName[0] != '&':
                channelName = '#' + channelName

            if ',' in channelName or ' ' in channelName:
                self.send_chat_message(user, "\n== Invalid channel name {0}. Please try again.".format(channelName))
                return

            user_channels = self.users_channels.get(user.username)

            if user_channels and channelName in user_channels:
                if self.users_curr_channel[user.username] == channelName:

                    self.send_chat_message(user, "\n== You are already in channel: {0}".format(channelName))
                else:
                    self.users_curr_channel[user.username] = channelName
                    self.channels[channelName].welcome_user(user.username, switched=True)
                    for auser in self.channels[channelName].users:
                        self.channels[channelName].update_channels(auser, self.users_channels.get(auser.username))

            elif user_channels and channelName not in user_channels:

                if not channelName in self.channels:
                    newChannel = Channel.Channel(channelName)
                    self.channels[channelName] = newChannel

                    with open(self.channels_file, 'a') as f:
                        f.write('{0} {1} {2}\n'.format(channelName, "None", '@'))

                self.channels[channelName].users.append(user)
                self.channels[channelName].welcome_user(user.username)
                self.users_curr_channel[user.username] = channelName
                self.users_channels[user.username].append(channelName)
                for auser in self.channels[channelName].users:
                    self.channels[channelName].update_channels(auser, self.users_channels.get(auser.username))
            else:
                if not channelName in self.channels:
                    newChannel = Channel.Channel(channelName)
                    self.channels[channelName] = newChannel

                    with open(self.channels_file, 'a') as f:
                        f.write('{0} {1} {2}\n'.format(channelName, "None", '@'))


                self.channels[channelName].users.append(user)
                self.channels[channelName].welcome_user(user.username)
                self.users_curr_channel[user.username] = channelName
                self.users_channels[user.username] = [channelName]
                for auser in self.channels[channelName].users:
                    self.channels[channelName].update_channels(auser, self.users_channels.get(auser.username))

    def send_message(self, user, chatMessage):
        if user.username in self.users_curr_channel:
            self.channels[self.users_curr_channel[user.username]].broadcast_message(chatMessage, "{0}{1}:".format(Util.time_text(), user.username))
        else:
            chatMessage = """\n> You are currently not in any channels:

Use /list to see a list of available channels.
Use /join [channel name] to join a channel.\n\n"""

            self.send_chat_message(user, chatMessage)

    def send_chat_message(self, user, chatMessage):
        if self.users_curr_channel.get(user.username):
            user.socket.sendall((user.channel_messages[self.users_curr_channel[user.username]] + "&&&" + chatMessage).encode('utf8'))
            user.channel_messages[self.users_curr_channel[user.username]] = user.channel_messages[self.users_curr_channel[user.username]] + chatMessage
        else:
            user.socket.sendall(chatMessage.encode('utf8'))


    def remove_user(self, user):
        if user.username in self.users_curr_channel:
            self.channels[self.users_curr_channel[user.username]].remove_user_from_channel(user)
            del self.users_curr_channel[user.username]

        self.users.remove(user)
        print("Client: {0} has left\n".format(user.username))


    def time(self, user):
        self.send_chat_message(user, ("\nTime is: " + time.asctime()))

    def whois(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) == 2:

            username = splitMessage[1]

            for other_user in self.users:

                print(other_user.username)
                print(username)

                if other_user.username == username:
                    user_info = other_user.username + " " + other_user.nickname + " " + other_user.status + " " + other_user.usertype
                    self.send_chat_message(user, "\nUser info: " + user_info)
                    return

                self.send_chat_message(user, ("\nNo user found"))
        else:
            self.help(user)

    def userss(self, user):

        for auser in self.users:
            user_info = auser.username + " " + auser.nickname + " " + auser.status + " " + auser.usertype
            self.send_chat_message(user, ("\n User: " + user_info))

    def ison(self, user, chatMessage):
        splitMessage = chatMessage.split()
        message = '\n== '

        if len(splitMessage) > 1:

            for username in splitMessage[1:]:
                for auser in self.users:
                    if auser.username == username:
                        message += auser.username + " "

                        self.send_chat_message(user, message)

        else:
            self.help(user)

    def who(self, user, chatMessage):
        splitMessage = chatMessage.split()

        if len(splitMessage) == 2:

            username = splitMessage[1]

            for other_user in self.users:

                print(other_user.username)
                print(username)

                if other_user.username == username:
                    user_info = other_user.username + " " + other_user.nickname + " " + other_user.status + " " + other_user.usertype
                    self.send_chat_message(user,("\n== User info: " + user_info))
                    return

            self.send_chat_message(user, ("\nNo user found"))
        else:
            self.help(user)

    def userhost(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) == 2:

            username = splitMessage[1]

            for other_user in self.users:

                print(other_user.username)
                print(username)

                if other_user.username == username:
                    user_info = other_user.username + " " + other_user.nickname + " " + other_user.status + " " + other_user.usertype
                    self.send_chat_message(user, ("\n== User info: " + user_info))
                    return

                self.send_chat_message(user, ("\nNo user found"))
        else:
            self.help(user)

    def invite(self, user, chatMessage):
        splitMessage = chatMessage.split()

        if len(splitMessage) == 3:
            username = splitMessage[1]
            channel = splitMessage[2]

            for auser in self.users:

                if auser.username == username:
                    self.send_chat_message(auser, ("\n" + user.username + " invites you to join " + channel))
                    self.send_chat_message(user, ("\n" + auser.username + " " + channel))
                    return
            self.send_chat_message(user, ("\nNo such user: " + username))

        else:
            self.help(user)

    def part(self, user, chatMessage, kicked=False):

        if len(chatMessage.split()) >= 2:
            channelName = chatMessage.split()[1]

            if channelName[0] != '#' and channelName[0] != '&':
                channelName = '#' + channelName

            user_channels = self.users_channels.get(user.username)
            user_current_channel = self.users_curr_channel.get(user.username)
            if user_channels and channelName in user_channels:

                if len(user_channels) == 1:
                    del self.users_curr_channel[user.username]
                    del self.users_channels[user.username]
                    self.channels[channelName].remove_user_from_channel(user)

                    if kicked:
                        self.send_chat_message(user, "\nYou were kicked out of channel {0}.|".format(channelName))
                    else:
                        self.send_chat_message(user, "\nYou left channel {0}.|".format(channelName))

                    self.channels[channelName].update_channels(user, self.users_channels.get(user.username) or [])
                elif len(user_channels) > 1 and self.users_curr_channel[user.username] == channelName:
                    self.users_channels[user.username].remove(channelName)
                    self.channels[channelName].remove_channels(user, channelName)
                    self.users_curr_channel[user.username] = self.users_channels[user.username][0]## index1
                    self.channels[channelName].remove_user_from_channel(user)

                    if kicked:
                        self.send_chat_message(user, "\nYou were kicked out of channel {0}.|".format(channelName))
                    else:
                        self.send_chat_message(user, "\nYou left channel {0}.|".format(channelName))
                    self.channels[channelName].update_channels(user, self.users_channels.get(user.username) or [])


                elif len(self.users_channels[user.username]) > 1:
                    self.users_channels[user.username].remove(channelName)
                    self.channels[channelName].remove_channels(user, channelName)
                    self.channels[channelName].remove_user_from_channel(user)


                    if kicked:
                        self.send_chat_message(user, "\nYou were kicked out of channel {0}.|".format(channelName))
                    else:
                        self.send_chat_message(user, "\nYou left channel {0}.|".format(channelName))

                    self.channels[channelName].update_channels(user, self.users_channels.get(user.username) or [])

                if self.users_curr_channel.get(user.username):
                    self.channels[self.users_curr_channel[user.username]].update_users(user)

            elif user_channels and channelName not in user_channels:
                # print("not inside")

                if channelName in self.channels:
                    self.send_chat_message(user, "\nYou are not in this channel. You cannot part from it.")
                else:
                    self.send_chat_message(user, "\nChannel does not exist. You cannot part from it.")
            else:
                if channelName in self.channels:
                    self.send_chat_message(user, "\nYou are not in this channel. You cannot part from it.")
                else:
                    self.send_chat_message(user, "\nChannel does not exist. You cannot part from it.")


    def kick(self, user, chatMessage):


        if len(chatMessage.split()) == 3:
            username = chatMessage.split()[1]
            channelName = chatMessage.split()[2]

            if channelName[0] != '#' and channelName[0] != '&':
                channelName = '#' + channelName

            if ',' in channelName or ' ' in channelName:
                self.send_chat_message(user, "\nInvalid channel name {0}. Please try again.".format(channelName))
                return

            if not self.channels.get(channelName):
                self.send_chat_message(user, "\nChannel name {0} doesn't exist.".format(channelName))
                return

            user_found = False

            for auser in self.channels.get(channelName).users:
                if auser.username == username:
                    user_found = True

            if user_found:
                for auser in self.channels.get(channelName).users:
                    if auser.username == username:
                        self.part(auser, "/part {0}".format(channelName), kicked=True)
                    else:
                        self.send_chat_message(user, "\nUser {0} was kicked out of channel {1}.".format(username, channelName))
            else:
                self.send_chat_message(user, "\n""No user {0} found.".format(username))


        else:
            self.help(user)


    def nick(self, user, chatMessage):


        splitMessage = chatMessage.split()
        if len(splitMessage) == 2:
            user.username = chatMessage.split()[1]
            self.send_chat_message(user, ("\nYou changed your name to {0}".format(user.username)))
        else:
            self.help(user)

    def topic(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 2:
            channelName = splitMessage[1]
            topicMessage = " ".join(splitMessage[2:])
            self.channels[channelName].topic = topicMessage
            self.send_chat_message(user, "\nTopic of channel changed to: " + topicMessage)
        elif len(splitMessage) == 2:
            channelName = splitMessage[1]
            channelTopic = self.channels[channelName].topic

            self.send_chat_message(user,("\nTopic of channel " + channelName + " is: " + channelTopic))
        else:
            self.help(user)

    def die(self, user):
        if user.usertype != "a":
            self.send_chat_message(user, "\nYou do not have permission to perform this command\n")
            return
        for auser in self.users:
            self.send_chat_message(auser, "\nShutting down server in 5 seconds...\n")
            time.sleep(5)
        self.exit_signal.set()


    def restart(self, user):
        if user.usertype != "a":
            self.send_chat_message(user, "\nYou do not have permission to perform this command\n")
            return

        for auser in self.users:
            self.send_chat_message(auser, "\nRestarting server in 5 seconds...\n")
            time.sleep(5)
        for auser in self.users:
            self.quit(auser)
        main()

    def ping(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) == 2:
            hostname = splitMessage[1]

            response = os.system('ping ' + hostname)

            if response == 0:
                self.send_chat_message(user, ("\nResponse from {0}\n".format(hostname)))
            else:
                self.send_chat_message(user, ("\nNo response from {0}\n".format(hostname)))
        else:
            self.help(user)


    def connect(self, user, chatMessage):

        splitMessage = chatMessage.split()

        if len(splitMessage) > 2:

            server = splitMessage[1]
            port = "".join(splitMessage[2:])
            address = (server, port)

            self.serverSocket.bind(self.address)
        else:
            self.help(user)



    def server_shutdown(self):
        print("Shutting down chat server.\n")
        self.serverSocket.close()

def main():

    chatServer = Server()

    print("\nListening on port {0}".format(chatServer.address[1]))
    print("Waiting for connections...\n")

    chatServer.start_listening()
    chatServer.server_shutdown()

if __name__ == "__main__":
    main()
