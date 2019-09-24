import Util

class User:
    def __init__(self, client_socket, username='', nickname=Util.generate_random_nickname(), password='', usertype='u', channel_messages=(dict())):
        self._client_socket = client_socket
        self._username = username
        self._nickname = nickname
        self._password = password
        self._usertype = usertype   #(a)dmin/(s)ysop/(c)hannelop/(u)ser
        self._status = "Online"
        self._PRVMSG = ""
        self._block_list = []
        self._channel_messages = channel_messages

    @property
    def socket(self):
        return self._client_socket

    @property
    def username(self):
        return self._username

    @property
    def nickname(self):
        return self._nickname

    @property
    def usertype(self):
        return self._usertype

    @property
    def password(self):
        return self._password

    @property
    def status(self):
        return self._status

    @property
    def PRVMSG(self):
        return self._PRVMSG

    @property
    def block_list(self):
        return self._block_list

    @property
    def channel_messages(self):
        return self._channel_messages

    @username.setter
    def username(self, new_username):
        self._username = new_username

    @nickname.setter
    def nickname(self, new_nickname):
        self._nickname = new_nickname

    @usertype.setter
    def usertype(self, new_usertype):
        self._usertype = new_usertype

    @password.setter
    def password(self, new_password):
        self._password = new_password

    @status.setter
    def status(self, new_status):
        self._status = new_status

    @PRVMSG.setter
    def PRVMSG(self, new_PRVMSG):
        self._PRVMSG = new_PRVMSG

    @block_list.setter
    def block_list(self, new_block_list):
        self._block_list = new_block_list

    @channel_messages.setter
    def channel_messages(self, new_channel_messages):
        self._channel_messages = new_channel_messages