import socket

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
port = 8000
serverSocket.bind((host, port))
serverSocket.listen(5)

print("Server is listening at post " + str(port))

while True:
    clientsocket, addr = serverSocket.accept()

    print("Got a connection from %s" % str(addr))

    while True:
        req = clientsocket.recv(2024)
        msg = req.decode("utf-8")  #binary->string
        print("C: " + msg)

        if msg == ".":
            print("client:%s has ended connection" %str(addr))
            break

        msg = input("Enter message: ")
        clientsocket.send(msg.encode('utf-8'))

    clientsocket.close()