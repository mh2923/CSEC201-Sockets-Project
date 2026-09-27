# Yerkebulan_server.py

import socket
import subprocess
import base64

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES

from Izhan_protocol import (
    parse_packet,
    create_packet,
    validate_packet,
    make_success_packet,
    make_error_packet,
    SS,
    CC,
    EC,
    CM,
    DP
)


# AES encryption function
def aes_encrypt(text, key):
    # Create AES cipher using the session key
    cipher = AES.new(key, AES.MODE_EAX)

    # Encrypt the text
    ciphertext, tag = cipher.encrypt_and_digest(
        text.encode("utf-8")
    )

    # Combine nonce, tag and encrypted text
    encrypted_data = cipher.nonce + tag + ciphertext

    # Convert binary data to Base64 text
    return base64.b64encode(encrypted_data).decode("utf-8")


# AES decryption function
def aes_decrypt(encrypted_text, key):
    # Convert Base64 text back to bytes
    encrypted_data = base64.b64decode(encrypted_text)

    # Separate nonce, tag and encrypted text
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]

    # Create AES cipher using the session key and nonce
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    # Decrypt and verify the data
    decrypted_data = cipher.decrypt_and_verify(
        ciphertext,
        tag
    )

    return decrypted_data.decode("utf-8")


# Generate the server RSA public and private keys
server_rsa_key = RSA.generate(2048)
server_private_key = server_rsa_key
server_public_key = server_rsa_key.publickey()


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

    # Parse and validate the Start Packet
    packet_type, fields = parse_packet(start_message)

    secure_mode = False
    algorithm = None
    session_key = None
    client_public_key = None

    if packet_type == SS and validate_packet(packet_type, fields):

        secure_flag = fields[2]

        # Secure RFMP connection
        if secure_flag == "1":
            secure_mode = True

            # Convert server public key to Base64 text
            server_public_key_text = base64.b64encode(
                server_public_key.export_key()
            ).decode("utf-8")

            # Send server public key in Confirm Connection Packet
            confirm_packet = create_packet(
                CC,
                server_public_key_text
            )

            clientsocket.send(
                confirm_packet.encode("utf-8")
            )

            print("Secure RFMP connection requested")

            # Receive Encryption Packet from client
            encryption_message = clientsocket.recv(4096).decode("utf-8")
            print("C: " + encryption_message)

            # Parse and validate Encryption Packet
            encryption_type, encryption_fields = parse_packet(
                encryption_message
            )

            validate_packet(
                encryption_type,
                encryption_fields
            )

            if encryption_type == EC:

                algorithm = encryption_fields[0]
                encrypted_session_key_text = encryption_fields[1]
                client_information = encryption_fields[2]

                # Convert encrypted session key back to bytes
                encrypted_session_key = base64.b64decode(
                    encrypted_session_key_text
                )

                # Decrypt session key using server private RSA key
                rsa_cipher = PKCS1_OAEP.new(
                    server_private_key
                )

                session_key = rsa_cipher.decrypt(
                    encrypted_session_key
                )

                # Separate username and client public key
                username, client_public_key_text = (
                    client_information.split(":", 1)
                )

                # Convert client public key back into RSA key
                client_public_key = RSA.import_key(
                    base64.b64decode(
                        client_public_key_text
                    )
                )

                print(
                    "Secure RFMP setup completed using "
                    + algorithm
                )

        # Non-secure RFMP connection
        else:
            confirm_packet = create_packet(CC)

            clientsocket.send(
                confirm_packet.encode("utf-8")
            )

            print("RFMP connection confirmed")


    # Operation Phase
    while True:
        req = clientsocket.recv(2024)

        if not req:
            break

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

                success_packet = make_success_packet(
                    output
                )

                clientsocket.send(
                    success_packet.encode("utf-8")
                )

            # Command failed
            else:
                error_message = result.stderr.strip()

                if error_message == "":
                    error_message = (
                        "Invalid command or arguments"
                    )

                error_packet = make_error_packet(
                    "E3",
                    error_message
                )

                clientsocket.send(
                    error_packet.encode("utf-8")
                )


        # Handle openRead
        elif packet_type == CM and fields[0] == "openRead":

            filename = fields[1]

            try:
                with open(filename, "r") as file:
                    file_contents = file.read()

                # Encrypt file contents in secure AES mode
                if secure_mode and algorithm == "AES":
                    file_contents = aes_encrypt(
                        file_contents,
                        session_key
                    )

                clientsocket.send(
                    file_contents.encode("utf-8")
                )

            except FileNotFoundError:
                error_packet = make_error_packet(
                    "E1",
                    "File not found: " + filename
                )

                clientsocket.send(
                    error_packet.encode("utf-8")
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


        # Handle openWrite
        elif packet_type == CM and fields[0] == "openWrite":

            filename = fields[1]

            # Receive Data Packet from client
            data_message = clientsocket.recv(4096).decode("utf-8")
            print("C: " + data_message)

            # Parse and validate Data Packet
            data_type, data_fields = parse_packet(
                data_message
            )

            validate_packet(
                data_type,
                data_fields
            )

            if data_type == DP:
                text = data_fields[0]

                try:

                    # Decrypt file contents in secure AES mode
                    if secure_mode and algorithm == "AES":
                        text = aes_decrypt(
                            text,
                            session_key
                        )

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