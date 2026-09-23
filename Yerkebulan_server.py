#Yerkebulan_server.py
import socket
import subprocess
from Izhan_protocol import parse_packet, create_packet, validate_packet, SS, CC, CM

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


    # Operation Phase
    while True:
        req = clientsocket.recv(2024)
        msg = req.decode("utf-8")

        print("C: " + msg)

        # Parse and validate the received packet
        packet_type, fields = parse_packet(msg)
        validate_packet(packet_type, fields)

        # Handle prompt command packets
        if packet_type == CM and fields[0] == "prompt":

            command = fields[1]

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            output = result.stdout

            if output == "":
                output = "Command executed successfully"

            clientsocket.send(output.encode("utf-8"))

    clientsocket.close()