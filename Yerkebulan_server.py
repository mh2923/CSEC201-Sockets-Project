#Yerkebulan_server.py
import socket
from Izhan_protocol import parse_packet, create_packet, validate_packet, SS, CC

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
port = 8000
serverSocket.bind((host, port))
serverSocket.listen(5)

print("Server is listening at port " + str(port))

while True:
    clientsocket, addr = serverSocket.accept()
    print("Got a connection from %s" % str(addr))

    start_message = clientsocket.recv(2024).decode("utf-8")
    print("C: " + start_message)

    # Parse the Start Packet
    packet_type, fields = parse_packet(start_message)

    # Validate the Start Packet and send confirmation
    if packet_type == SS and validate_packet(packet_type, fields):
        confirm_packet = create_packet(CC)
        clientsocket.send(confirm_packet.encode("utf-8"))
        print("RFMP connection confirmed")


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