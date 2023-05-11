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

        # Configurar o servidor de socket no contêiner
        socket_thread = threading.Thread(target=receive_messages, args=(ip_address, 5000))
        socket_thread.start()

        return jsonify({'message': 'Contêiner Docker Python criado com sucesso!', 'container_id': container_id})
    except docker.errors.APIError as e:
        return jsonify({'error': 'Erro ao criar o contêiner Docker Python', 'message': str(e)})

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    origin = data['origin']
    destination = data['destination']
    content = data['message']

    # Enviar a mensagem para o contêiner de destino
    timestamp = time.time()  # Carimbo de tempo atual
    sequence = get_next_sequence()  # Obter o próximo número de sequência
    vector_clock = get_vector_clock(origin)  # Obter o relógio vetorial atual do processo
    message = Message(timestamp, sequence, origin, destination, content, vector_clock)
    send_socket_message(destination, message)

    return jsonify({'success': True})

def send_socket_message(container_id, message):
    container = containers.get(container_id)
    if container:
        # Obter o endereço IP do contêiner
        ip_address = container.attrs['NetworkSettings']['IPAddress']

        # Definir as informações de conexão para o socket
        host = ip_address
        port = 5000  # Porta mapeada para o Flask nos contêineres

        # Criar o socket e enviar a mensagem
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            serialized_message = json.dumps(serialize_message(message))
            s.sendall(serialized_message.encode())

def get_next_sequence():
    # Implemente a lógica para obter o próximo número de sequência
    # Isso pode envolver comunicação com outros contêineres ou algoritmos de consenso distribuído
    # Neste exemplo simplificado, retornamos um número de sequência incremental
    global next_sequence
    next_sequence += 1
   
    return next_sequence

def get_vector_clock(process_id):
    # Implemente a lógica para obter o relógio vetorial atual do processo
    # Neste exemplo simplificado, retornamos um vetor de relógio vetorial com zeros
    vector_clock = {process_id: 0}
    return vector_clock

def serialize_message(message):
    # Implemente a lógica para serializar a mensagem em uma string para envio pelo socket
    # Neste exemplo simplificado, usamos um formato simples JSON
    serialized_message = {
        'timestamp': message.timestamp,
        'sequence': message.sequence,
        'origin': message.origin,
        'destination': message.destination,
        'content': message.content,
        'vector_clock': message.vector_clock
    }
    return serialized_message

def deserialize_message(serialized_message):
    # Implemente a lógica para desserializar a mensagem recebida do socket
    # Neste exemplo simplificado, assumimos que a mensagem está em formato JSON
    timestamp = serialized_message['timestamp']
    sequence = serialized_message['sequence']
    origin = serialized_message['origin']
    destination = serialized_message['destination']
    content = serialized_message['content']
    vector_clock = serialized_message['vector_clock']
    message = Message(timestamp, sequence, origin, destination, content, vector_clock)
    return message

@app.route('/get-nodes')
def get_nodes():
    node_list = list(containers.keys())
    return jsonify(node_list)

@app.route('/receive-messages', methods=['POST'])
def receive_messages():
    data = request.get_json()
    ip_address = data['ip_address']
    port = data['port']
    
    receive_thread = threading.Thread(target=start_server, args=(ip_address, port))
    receive_thread.start()

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
