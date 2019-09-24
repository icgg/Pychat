class Channel:
    def __init__(self, name, topic="no topic set"):
        self.users = []
        self.channel_name = name
        self.topic = topic
        self.mode = "pub"

    def update_channels(self, user, all_channels):
        print('update_channels')
        print(' '.join(all_channels))
        user.socket.sendall('[update channel]|{0}|'.format(' '.join(all_channels)).encode('utf8'))

    def remove_channels(self, user, channel):
        print('remove_channel')
        user.socket.sendall('[remove channel]|{0}'.format(channel).encode('utf8'))

    def update_users(self, user):
        print("UPDATE USERS")

        all_users = self.get_all_users_in_channel()
        user.socket.sendall('[update users]|{0}'.format(all_users).encode('utf8'))

    def welcome_user(self, username, switched=False):
        all_users = self.get_all_users_in_channel()

        print("Users: " + str(self.users))

        for user in self.users:

            print("Before saving chat message for user " + user.username + ":")
            print(user.channel_messages)

            if user.username is username:

                if switched:
                    chatMessage = ''
                else:
                    chatMessage = '\n== {0} have joined the channel {1}'.format("You", self.channel_name)

                if user.channel_messages.get(self.channel_name):
                    user.socket.sendall((user.channel_messages[self.channel_name] + "&&&" + chatMessage + "|users:{0}".format(all_users)).encode('utf8'))
                    user.channel_messages[self.channel_name] = user.channel_messages[self.channel_name] + chatMessage
                else:
                    user.socket.sendall(("" + "&&&" + chatMessage + "|users:{0}".format(all_users)).encode('utf8'))
                    user.channel_messages[self.channel_name] = chatMessage

            else:
                if switched:
                    chatMessage = ''
                else:
                    chatMessage = '\n== {0} has joined the channel {1}'.format(username, self.channel_name)

                if user.channel_messages.get(self.channel_name):
                    user.socket.sendall((user.channel_messages[self.channel_name] + "&&&" + chatMessage + "|users:{0}".format(all_users)).encode('utf8'))
                    user.channel_messages[self.channel_name] = user.channel_messages[self.channel_name] + chatMessage
                else:
                    user.socket.sendall(("" + "&&&" + chatMessage + "|users:{0}".format(all_users)).encode('utf8'))
                    user.channel_messages[self.channel_name] = chatMessage

            print("Channel messages for user " + user.username + ":\n")
            print(user.channel_messages)


    def broadcast_message(self, message, username=''):
        for user in self.users:
            if user.username is username:

                chatMessage = "\nYou: {0}".format(message)

                if user.channel_messages.get(self.channel_name):
                    user.socket.sendall((user.channel_messages[self.channel_name] + "&&&" + chatMessage).encode('utf8'))
                    user.channel_messages[self.channel_name] = user.channel_messages[self.channel_name] + chatMessage
                else:
                    user.socket.sendall(("" + "&&&" + chatMessage).encode('utf8'))
                    user.channel_messages[self.channel_name] = chatMessage


            else:
                chatMessage = "\n{0} {1}".format(username, message)

                if user.channel_messages.get(self.channel_name):
                    user.socket.sendall((user.channel_messages[self.channel_name] + "&&&" + chatMessage).encode('utf8'))
                    user.channel_messages[self.channel_name] = user.channel_messages[self.channel_name] + chatMessage
                else:
                    user.socket.sendall(("" + "&&&" + chatMessage).encode('utf8'))
                    user.channel_messages[self.channel_name] = chatMessage


    def get_all_users_in_channel(self):
        return ' '.join([user.username for user in self.users])

    def remove_user_from_channel(self, user):
        self.users.remove(user)
        leave_message = "\n== {0} has left the channel {1}\n".format(user.username, self.channel_name)
        self.broadcast_message(leave_message)
