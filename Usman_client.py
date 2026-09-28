# Usman_client.py

import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
import base64
from Izhan_protocol import create_packet, parse_packet, caesar_encrypt, caesar_decrypt, caesar_shift_from_key, SS, EC, CM, DP, SC, EE, END, PROTOCOL_NAME, PROTOCOL_VERSION

def handle_response(response):
    packet_type, fields = parse_packet(response)

    if packet_type == SC:
        if len(fields) > 0:
            print("Success: " + fields[0])
        else:
            print("Success")

    elif packet_type == EE:
        print("Error " + fields[0] + ": " + fields[1])

    else:
        print("Server: " + response)

def aes_encrypt(text, key):
    # Create an AES cipher using the session key
    cipher = AES.new(key, AES.MODE_EAX)

    # Encrypt the text
    ciphertext, tag = cipher.encrypt_and_digest(
        text.encode("utf-8")
    )

    # Combine nonce, tag and encrypted text
    encrypted_data = cipher.nonce + tag + ciphertext

    # Convert binary data to text so it can be sent in an RFMP packet
    return base64.b64encode(encrypted_data).decode("utf-8")


def aes_decrypt(encrypted_text, key):
    # Convert the received Base64 text back to bytes
    encrypted_data = base64.b64decode(encrypted_text)

    # Separate the nonce, tag and encrypted text
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]

    # Create the AES cipher using the same session key and nonce
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    # Decrypt and verify the data
    decrypted_data = cipher.decrypt_and_verify(
        ciphertext,
        tag
    )

    return decrypted_data.decode("utf-8")

# Generate the client's RSA public and private keys
client_rsa_key = RSA.generate(2048)
client_private_key = client_rsa_key
client_public_key = client_rsa_key.publickey()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = socket.gethostname()
port = 8000

client_socket.connect((host, port))

# Ask the user whether the RFMP connection should be secured
print("\nRFMP Connection")
print("1. Non-secure")
print("2. Secure")

security_choice = input("Choose connection type: ")

if security_choice == "2":
    secure_mode = True
    secure_flag = 1
else:
    secure_mode = False
    secure_flag = 0

# Create and send the RFMP Start Packet (SS)
start_packet = create_packet(SS, PROTOCOL_NAME, PROTOCOL_VERSION, secure_flag)
client_socket.send(start_packet.encode("utf-8"))

# Receive the server's confirmation (CC)
response = client_socket.recv(2024).decode("utf-8")
if secure_mode:
    print("Server: Secure connection confirmation received")
else:
    print("Server: " + response)

packet_type, fields = parse_packet(response)

if packet_type != "CC":
    print("Connection confirmation was not received.")

server_public_key = None

if secure_mode:
    if len(fields) == 1:
        server_public_key_text = fields[0]

        # Convert the received public key back into an RSA key
        server_public_key_text = base64.b64decode(
            server_public_key_text
        )

        server_public_key = RSA.import_key(
            server_public_key_text
        )

    else:
        print("Server public key was not received.")
        client_socket.close()
        exit()

# Select encryption algorithm for secure mode
algorithm = None
session_key = None

if secure_mode:
    print("\nEncryption Algorithm")
    print("1. AES")
    print("2. Caesar")

    algorithm_choice = input("Choose encryption algorithm: ")

    if algorithm_choice == "1":
        algorithm = "AES"

    elif algorithm_choice == "2":
        algorithm = "Caesar"

    else:
        print("Invalid encryption choice.")
        client_socket.close()
        exit()

if secure_mode:

    # Generate a random 16-byte session key
    session_key = get_random_bytes(16)

    # Encrypt the session key using the server's RSA public key
    rsa_cipher = PKCS1_OAEP.new(server_public_key)
    encrypted_session_key = rsa_cipher.encrypt(session_key)

    # Convert encrypted session key to text for the EC packet
    encrypted_session_key_text = base64.b64encode(
        encrypted_session_key
    ).decode("utf-8")

    # Convert client public key to text for the EC packet
    client_public_key_text = base64.b64encode(
        client_public_key.export_key()
    ).decode("utf-8")

    # Create and send the Encryption Packet
    encryption_packet = create_packet(
        EC,
        algorithm,
        encrypted_session_key_text,
        "Usman:" + client_public_key_text
    )

    client_socket.send(
        encryption_packet.encode("utf-8")
    )

    print("Secure RFMP setup information sent to server.")

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

        response = client_socket.recv(2024).decode("utf-8")

        if response.startswith("(EE,"):
            handle_response(response)

        else:
            # Decrypt file contents when secure mode is being used
            if secure_mode and algorithm == "AES":
                response = aes_decrypt(response, session_key)

            elif secure_mode and algorithm == "Caesar":
                shift = caesar_shift_from_key(session_key)
                response = caesar_decrypt(response, shift)

            print("File contents: " + response)

        continue

    elif choice == "8":
        filename = input("Enter file name to write: ")

        # Tell the server which file should be opened
        command_packet = create_packet(CM, "openWrite", filename)
        client_socket.send(command_packet.encode("utf-8"))

        # Enter the data that will be written to the file
        text = input("Enter text to write: ")

        # Encrypt file contents when secure mode is being used
        if secure_mode and algorithm == "AES":
            text = aes_encrypt(text, session_key)

        elif secure_mode and algorithm == "Caesar":
            shift = caesar_shift_from_key(session_key)
            text = caesar_encrypt(text, shift)

        data_packet = create_packet(DP, text)
        client_socket.send(data_packet.encode("utf-8"))

        response = client_socket.recv(2024).decode("utf-8")
        handle_response(response)

        continue

    elif choice == "9":
        end_packet = create_packet(END)
        client_socket.send(end_packet.encode("utf-8"))

        print("RFMP connection closed.")
        break

    else:
        print("Invalid option.")
        continue

    command_packet = create_packet(CM, "prompt", command)
    client_socket.send(command_packet.encode("utf-8"))

    response = client_socket.recv(2024).decode("utf-8")
    handle_response(response)

client_socket.close()