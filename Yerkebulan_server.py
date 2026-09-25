# Yerkebulan_server.py

import socket
import subprocess
from Izhan_protocol import (
    parse_packet,
    create_packet,
    validate_packet,
    make_success_packet,
    make_error_packet,
    SS,
    CC,
    CM,
    DP
)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = socket.gethostname()
port = 8000

serverSocket.bind((host, port))
serverSocket.listen(5)

print("Server is listening at port " + str(port))

while True:
    clientsocket, addr = serverSocket.accept()

    print("Got a connection from %s" % str(addr))

    # Receive RFMP Start Packet
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

        # Handle normal prompt commands
        if packet_type == CM and fields[0] == "prompt":

            command = fields[1]

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            # Command was successful
            if result.returncode == 0:
                output = result.stdout.strip()

                if output == "":
                    output = "Command executed successfully"

                success_packet = make_success_packet(output)
                clientsocket.send(success_packet.encode("utf-8"))

            # Command failed
            else:
                error_message = result.stderr.strip()

                if error_message == "":
                    error_message = "Invalid command or arguments"

                error_packet = make_error_packet(
                    "E3",
                    error_message
                )
                clientsocket.send(error_packet.encode("utf-8"))

        # Handle openRead
        elif packet_type == CM and fields[0] == "openRead":

            filename = fields[1]

            try:
                with open(filename, "r") as file:
                    file_contents = file.read()

                clientsocket.send(file_contents.encode("utf-8"))

            except FileNotFoundError:
                error_packet = make_error_packet(
                    "E1",
                    "File not found: " + filename
                )
                clientsocket.send(error_packet.encode("utf-8"))

            except PermissionError:
                error_packet = make_error_packet(
                    "E2",
                    "Permission denied: " + filename
                )
                clientsocket.send(error_packet.encode("utf-8"))

            except Exception as e:
                error_packet = make_error_packet(
                    "E4",
                    str(e)
                )
                clientsocket.send(error_packet.encode("utf-8"))

        # Handle openWrite
        elif packet_type == CM and fields[0] == "openWrite":

            filename = fields[1]

            # Receive the Data Packet from the client
            data_message = clientsocket.recv(2024).decode("utf-8")
            print("C: " + data_message)

            # Parse and validate the Data Packet
            data_type, data_fields = parse_packet(data_message)
            validate_packet(data_type, data_fields)

            if data_type == DP:
                text = data_fields[0]

                try:
                    with open(filename, "w") as file:
                        file.write(text)

                    success_packet = make_success_packet(
                        "File written successfully"
                    )
                    clientsocket.send(
                        success_packet.encode("utf-8")
                    )

                except PermissionError:
                    error_packet = make_error_packet(
                        "E2",
                        "Permission denied: " + filename
                    )
                    clientsocket.send(
                        error_packet.encode("utf-8")
                    )

                except Exception as e:
                    error_packet = make_error_packet(
                        "E4",
                        str(e)
                    )
                    clientsocket.send(
                        error_packet.encode("utf-8")
                    )

    clientsocket.close()