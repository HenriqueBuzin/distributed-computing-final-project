import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, help='Port number')
args = parser.parse_args()

def receive_message(conn):
    data = conn.recv(1024).decode()
    print(f'Message received: {data}')

def start_server(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', port))
        s.listen()
        print(f'Server listening on port {port}...')
        while True:
            conn, addr = s.accept()
            with conn:
                print(f'Connected by {addr}')
                receive_message(conn)

if __name__ == '__main__':
    start_server(args.port)
