import docker
from flask import Flask, render_template, jsonify, request
import socket
import threading
import time
import json

app = Flask(__name__)
client = docker.from_env()
containers = {}
next_sequence = 0  # Próximo número de sequência disponível
base_port = 8000  # Porta base para o primeiro servidor de socket

class Message:
    def __init__(self, timestamp, sequence, origin, destination, content, vector_clock):
        self.timestamp = timestamp
        self.sequence = sequence
        self.origin = origin
        self.destination = destination
        self.content = content
        self.vector_clock = vector_clock

    def update_vector_clock(self, process_id):
        self.vector_clock[process_id] += 1

def receive_message(ip_address, port):
    # Lógica para receber e processar mensagens em um socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ip_address, port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                if data:
                    try:
                        serialized_message = data.decode()
                        message = deserialize_message(json.loads(serialized_message))
                        process_id = message.destination
                        message.update_vector_clock(process_id)
                        print(f"Mensagem recebida: {message.content}")
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Erro ao processar a mensagem: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-container')
def create_container():
    try:
        # Criação do contêiner Docker Python
        container = client.containers.run('python:3.9', detach=True)
        container_id = container.id
        containers[container_id] = container

        # Obter o endereço IP do contêiner
        ip_address = container.attrs['NetworkSettings']['IPAddress']

        # Calcular a porta para o servidor de socket
        port = base_port + len(containers)

        # Configurar o servidor de socket no contêiner
        socket_thread = threading.Thread(target=receive_message, args=(ip_address, port))
        socket_thread.start()

        return jsonify({'message': 'Contêiner Docker Python criado com sucesso!', 'container_id': container_id})
    except docker.errors.APIError as e:
        return jsonify({'error': 'Erro ao criar o contêiner Docker Python', 'message': str(e)})

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    if not validate_message_data(data):
        return jsonify({'error': 'Dados de mensagem inválidos'})

    origin = data['origin']
    destination = data['destination']
    content = data['message']

    # Enviar a mensagem para o contêiner de destino
    timestamp = time.time()  # Carimbo de tempo atual
    sequence = get_next_sequence()  # Obter o próximo número de sequência
    vector_clock = get_vector_clock(origin)  # Obter o relógio vetorial atual do processo
    message = Message(timestamp, sequence, origin, destination, content, vector_clock)

    serialized_message = serialize_message(message)

    try:
        container = containers[destination]
        ip_address = container.attrs['NetworkSettings']['IPAddress']

        # Enviar a mensagem para o contêiner de destino
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_address, 5000))
            s.sendall(serialized_message.encode())
            print(f"Mensagem enviada para o destino: {message.content}")
    except KeyError:
        return jsonify({'error': 'Destino inválido'})

    return jsonify({'message': 'Mensagem enviada com sucesso'})

def validate_message_data(data):
    required_fields = ['origin', 'destination', 'message']
    for field in required_fields:
        if field not in data or not data[field]:
            return False
    return True

def get_next_sequence():
    global next_sequence
    next_sequence += 1
    return next_sequence

def get_vector_clock(process_id):
    vector_clock = {}
    for container_id, container in containers.items():
        ip_address = container.attrs['NetworkSettings']['IPAddress']
        vector_clock[ip_address] = 0
    vector_clock[process_id] = 1
    return vector_clock

def serialize_message(message):
    return json.dumps(message.__dict__)

def deserialize_message(data):
    timestamp = data['timestamp']
    sequence = data['sequence']
    origin = data['origin']
    destination = data['destination']
    content = data['content']
    vector_clock = data['vector_clock']
    return Message(timestamp, sequence, origin, destination, content, vector_clock)

@app.route('/get-nodes')
def get_nodes():
    node_list = list(containers.keys())
    return jsonify(node_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
