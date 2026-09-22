# Usman_client.py

import socket
from Izhan_protocol import create_packet, SS, PROTOCOL_NAME, PROTOCOL_VERSION

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = socket.gethostname()
port = 8000

client_socket.connect((host, port))

# Create and send the RFMP non-secure Start Packet
start_packet = create_packet(SS, PROTOCOL_NAME, PROTOCOL_VERSION, 0)
client_socket.send(start_packet.encode("utf-8"))

# Receive the server's confirmation
response = client_socket.recv(2024)
print("Server: " + response.decode("utf-8"))

while True:
    msg = input("Enter your message, and . to stop: ")
    client_socket.send(msg.encode("utf-8"))

    if msg == ".":
        break

    msg = client_socket.recv(2024)
    print ("Server: " + msg.decode('utf-8'))