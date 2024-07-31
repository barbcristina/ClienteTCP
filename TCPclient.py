# Description: Este é um cliente TCP que se conecta a um servidor TCP e envia mensagens para ele.
import socket
import threading
import time

keepalive_interval = 5

peer_client_sockets = {}  # Dicionário q guarda peer sockets e seus endereços
peer_client_timestamps = {}  # Dicionário q guarda o tempo das conexões
peer_server = None
active_peer = None  
client = None  
latest_peer = None

def receive_messages(client):
    global peer_client_sockets
    global peer_client_timestamps
    global peer_server
    global active_peer
    global latest_peer

    while True:
        try:
            msg = client.recv(1024).decode('utf-8')
            if msg.startswith("ADDR"):
                ip, port = msg[5:].split(':')
                port = int(port)
                print(f'Conectando ao peer {ip}:{port}')
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_client_sockets[(ip, port)] = s
                peer_client_timestamps[(ip, port)] = time.time()  
                s.connect((ip, port))
                active_peer = (ip, port) 
                latest_peer = (ip, port)  
                threading.Thread(target=handle_peer, args=(s,)).start()
            elif msg == "":
                break
            elif msg:
                print(msg)
        except ConnectionResetError:
            break

def handle_peer(peer_client):
    while True:
        try:
            message = peer_client.recv(1024).decode('utf-8')
            if message.startswith('DISC'):
                print("O outro peer solicitou desconexão.")
                peer_client.close()
                break
            elif message == "":
                break
            else:
                print(f"{message}")
        except Exception as e:
            break

def accept_peer_connections():
    global peer_client_sockets
    global peer_client_timestamps
    global peer_server
    global active_peer
    global latest_peer

    peer_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_server.bind(('0.0.0.0', 1060))
    peer_server.listen(5)
    peer_port = peer_server.getsockname()[1]

    while True:
        s, peer_address = peer_server.accept()
        peer_client_sockets[peer_address] = s
        peer_client_timestamps[peer_address] = time.time()  # Guarda o tempo para saber quem foi + recente
        active_peer = peer_address  # Coloca o novo peer como ativo
        latest_peer = peer_address  # Atualiza o último peer
        print(f"Conexão peer aceita de {peer_address}")
        threading.Thread(target=handle_peer, args=(s,)).start()

def send_keepalive(client):
    while True:
        try:
            client.send("KEEP\r\n".encode('utf-8'))
            time.sleep(keepalive_interval)
        except:
            break

def main():
    global peer_client_sockets
    global peer_client_timestamps
    global client
    global peer_server
    global active_peer
    global latest_peer

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip = "200.235.131.66"
    client.connect((ip, 10001))

    name = "ana julia"
    port = 1060
    client.send(f"USER {name}:{port}\r\n".encode('utf-8'))


    threading.Thread(target=receive_messages, args=(client,)).start()
    threading.Thread(target=send_keepalive, args=(client,), daemon=True).start()
    threading.Thread(target=accept_peer_connections, daemon=True).start()
   
    while True:
        cmd = input()
    
        if cmd.lower() == '/list':
            print("Ativos (além de você):")
            client.send("LIST\r\n".encode('utf-8'))

        elif cmd.startswith('/chat'):        
            target_nick = cmd[5:].strip()
            client.send(f'ADDR {target_nick}\r\n'.encode('utf-8'))

        elif cmd == "/exit":
            if peer_server:
                peer_server.close()
            if client:
                client.send(f"DISC\r\n".encode('utf-8'))
                time.sleep(1)
                client.close()
            break

        elif cmd.lower() == '/bye':
            if latest_peer and latest_peer in peer_client_sockets:
                peer_client_sockets[latest_peer].send("DISC".encode('utf-8'))
                peer_client_sockets[latest_peer].close()
                print(f"Desconectando do peer mais recente {latest_peer}.")
                del peer_client_sockets[latest_peer]
                del peer_client_timestamps[latest_peer]
                latest_peer = None

                # Depois de desconectar do ultimo peer, atualiza o peer
                if peer_client_sockets:
                    # Acha a conexão remanescente + recente
                    latest_timestamp = max(peer_client_timestamps.values())
                    latest_peer = [addr for addr, time in peer_client_timestamps.items() if time == latest_timestamp][0]
                    active_peer = latest_peer
            else:
                print("Nenhum peer ativo para desconectar.")

        elif active_peer and active_peer in peer_client_sockets:
            peer_client_sockets[active_peer].send(cmd.encode('utf-8'))

        else: 
            print(f"Comando desconhecido ou nenhum peer ativo para enviar a mensagem: {cmd}")
       
if __name__ == "__main__":
    main()
