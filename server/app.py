import docker
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from collections import defaultdict
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu_secret_key_aqui'
socketio = SocketIO(app)
client = docker.from_env()
containers = {}
timestamps = defaultdict(int)  # Vetor de carimbos de data/hora lógicos para cada container
votes = defaultdict(list)  # Dicionário para armazenar os votos recebidos dos containers

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-container')
def create_container():
    try:
        container = client.containers.run('python:3.9', detach=True)
        container_id = container.id
        containers[container_id] = container
        return jsonify({'message': 'Contêiner Docker Python criado com sucesso!', 'container_id': container_id})
    except docker.errors.APIError as e:
        return jsonify({'error': 'Erro ao criar o contêiner Docker Python', 'message': str(e)})

@app.route('/get-nodes')
def get_nodes():
    node_list = list(containers.keys())
    return jsonify(node_list)

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    recipient = data['recipient']
    origin = data['origin']
    message = data['message']
    timestamp = data['timestamp']

    # Emitir um evento SocketIO para processar a mensagem
    socketio.emit('message', {
        'recipient': recipient,
        'origin': origin,
        'message': message,
        'timestamp': timestamp
    })

    return jsonify({'success': True})

@socketio.on('message')
def handle_message(data):
    recipient = data['recipient']
    origin = data['origin']
    message = data['message']
    timestamp = data['timestamp']  # Carimbo de data/hora lógico da mensagem

    # Atualizar o carimbo de data/hora lógico do remetente
    timestamps[origin] += 1

    # Enviar votos para todos os containers, incluindo o próprio remetente
    for container_id in containers.keys():
        votes[container_id].append((origin, timestamps[origin]))

    # Verificar a ordem causal antes de enviar a mensagem
    if check_causal_order(origin, timestamps[origin]):
        # Verificar se todos os votos foram recebidos de todos os containers
        if check_total_order():
            # Enviar a mensagem para o recipiente específico ou para todos os recipientes (broadcast)
            if recipient == 'broadcast':
                # Enviar para todos os recipientes
                socketio.emit('message', {'sender': 'broadcast', 'message': message, 'timestamp': timestamp}, broadcast=True)
            else:
                # Encontrar o recipiente pelo ID e enviar a mensagem apenas para ele
                container = containers.get(recipient)
                if container:
                    socketio.emit('message', {'sender': recipient, 'message': message, 'timestamp': timestamp}, room=container.id)

@socketio.on('message_status')
def handle_message_status(data):
    origin = data['origin']
    recipient = data['recipient']
    message = data['message']
    status = data['status']

    emit('message_status', {'origin': origin, 'recipient': recipient, 'message': message, 'status': status})

def check_causal_order(origin, timestamp):
    # Verificar se o carimbo de data/hora lógico da mensagem é maior ou igual ao último carimbo de data/hora lógico conhecido do remetente
    if timestamp >= timestamps[origin]:
        return True
    else:
        return False

def check_total_order():
    total_votes = len(containers)  # Número total de votos esperados

    # Verificar se todos os containers enviaram seus votos
    for container_id, vote_list in votes.items():
        if len(vote_list) < total_votes:
            return False

    # Verificar se todos os votos são iguais
    for container_id, vote_list in votes.items():
        if vote_list != votes[list(containers.keys())[0]]:
            return False

    # Limpar os votos após a verificação
    votes.clear()
    return True

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
