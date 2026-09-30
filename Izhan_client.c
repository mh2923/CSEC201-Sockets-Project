// Izhan_client.c
// Non-secure RFMP client: connects, confirms the connection, then reads one file.

#include <stdio.h>
#include <string.h>
#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")

int main() {
    WSAStartup(MAKEWORD(2, 2), &(WSADATA){0});  // turn on Windows networking

    SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in server;
    server.sin_family = AF_INET;
    server.sin_port = htons(5555);
    server.sin_addr.s_addr = inet_addr("127.0.0.1");

    if (connect(sock, (struct sockaddr *)&server, sizeof(server)) < 0) {
        printf("Could not connect to server.\n");
        return 1;
    }
    printf("Connected to server.\n");

    char buffer[4096];
    char packet[512];
    int received;

    // send the Start Packet and wait for (CC)
    send(sock, "(SS,RFMP,v1.0,0)", 16, 0);
    received = recv(sock, buffer, sizeof(buffer) - 1, 0);
    buffer[received] = '\0';
    printf("Server: %s\n", buffer);

    // ask which file to read, then send (CM,openRead,filename)
    char filename[256];
    printf("Enter file name to read: ");
    scanf("%255s", filename);

    sprintf(packet, "(CM,openRead,%s)", filename);
    send(sock, packet, strlen(packet), 0);

    // print whatever the server sends back
    received = recv(sock, buffer, sizeof(buffer) - 1, 0);
    buffer[received] = '\0';
    printf("Server: %s\n", buffer);

    send(sock, "(End)", 5, 0);  // tell the server we're done

    closesocket(sock);
    WSACleanup();
    return 0;
}