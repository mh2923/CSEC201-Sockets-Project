import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = socket.gethostname()
port = 8000

client_socket.connect((host, port))

while True:
    msg = input("Enter your message, and . to stop: ")
    client_socket.send(msg.encode("utf-8"))

    if msg == ".":
        break

    msg = client_socket.recv(2024)
    print ("Server: " + msg.decode('utf-8'))