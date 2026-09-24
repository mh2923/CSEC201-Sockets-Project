# Usman_client.py

import socket
from Izhan_protocol import create_packet, SS, CM, DP, PROTOCOL_NAME, PROTOCOL_VERSION

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
    print("\nRFMP Client")
    print("1. Create directory")
    print("2. Change directory")
    print("3. Remove directory")
    print("4. Delete file")
    print("5. Rename file/folder")
    print("6. Enter another system command")
    print("7. Read file")
    print("8. Write file")
    print("9. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        folder = input("Enter directory name: ")
        command = "mkdir " + folder

    elif choice == "2":
        path = input("Enter directory path: ")
        command = "cd " + path

    elif choice == "3":
        folder = input("Enter directory name: ")
        command = "rmdir " + folder

    elif choice == "4":
        filename = input("Enter file name: ")
        command = "del " + filename

    elif choice == "5":
        old_name = input("Enter current name: ")
        new_name = input("Enter new name: ")
        command = "ren " + old_name + " " + new_name

    elif choice == "6":
        command = input("Enter system command: ")

    elif choice == "7":
        filename = input("Enter file name to read: ")

        command_packet = create_packet(CM, "openRead", filename)
        client_socket.send(command_packet.encode("utf-8"))

        response = client_socket.recv(2024)
        print("File contents: " + response.decode("utf-8"))

        continue

    elif choice == "8":
        filename = input("Enter file name to write: ")

        # Tell the server which file should be opened
        command_packet = create_packet(CM, "openWrite", filename)
        client_socket.send(command_packet.encode("utf-8"))

        # Enter the data that will be written to the file
        text = input("Enter text to write: ")

        data_packet = create_packet(DP, text)
        client_socket.send(data_packet.encode("utf-8"))

        response = client_socket.recv(2024)
        print("Server: " + response.decode("utf-8"))

        continue

    elif choice == "9":
        break

    else:
        print("Invalid option.")
        continue

    command_packet = create_packet(CM, "prompt", command)
    client_socket.send(command_packet.encode("utf-8"))

    response = client_socket.recv(2024)
    print("Server: " + response.decode("utf-8"))