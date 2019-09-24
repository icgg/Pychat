import ChatClient as client
import time
import threading

class SocketThreadedTask(threading.Thread):
    def __init__(self, socket, **callbacks):
        threading.Thread.__init__(self)
        self.socket = socket
        self.callbacks = callbacks

    def run(self):
        while True:
            try:
                message = self.socket.receive()

                if '&&&' in message:
                    split_history = message.split("&&&")
                    message = split_history[1]

                if message == '/quit':
                    self.socket.disconnect()
                    break
                elif 'joined the channel' in message or '|users:' in message:
                    split_message = message.split('|')
                    print(split_message[0])
                elif '[update channel]' in message:
                    continue
                elif message == '/squit':
                    self.socket.disconnect()
                    break
                else:
                    print(message)
            except OSError:
                break

def hello():
    print('hello')

def send_message(self, **callbacks):
    message = 'hello'
    callbacks['send_message_to_server'](message)

if __name__ == '__main__':
    clientSocket = client.Client()
    clientSocket.connect('localhost', 50000)
    keepServer = True

    threadedTask = SocketThreadedTask(clientSocket, hello=hello)

    if clientSocket.isClientConnected:
        threadedTask.start()

    with open('./files/testfile1.txt', 'r') as f:

        for line in f:
            time.sleep(1)
            clientSocket.send(line)



#
