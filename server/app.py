from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
nodes = []
node_id = 0
clocks = {}  # Vetores de relógio dos nós
messages = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/node', methods=['POST'])
def create_node():
    global node_id
    node_id += 1
    node = {'node_id': node_id}
    nodes.append(node)
    clocks[node_id] = 0  # Inicializa o vetor de relógio do novo nó
    return jsonify(node), 201

@app.route('/graph', methods=['GET'])
def get_graph():
    return jsonify(nodes)

@app.route('/node/<int:node_id>', methods=['DELETE'])
def remove_node(node_id):
    global nodes
    nodes = [node for node in nodes if node['node_id'] != node_id]
    del clocks[node_id]  # Remove o vetor de relógio do nó removido
    return jsonify({'message': 'Node removed'}), 200

@app.route('/remove-all-nodes', methods=['DELETE'])
def remove_all_nodes():
    global nodes
    nodes = []
    clocks.clear()  # Remove todos os vetores de relógio
    return jsonify({'message': 'All nodes removed'}), 200

def lamport_sort(message):
    return (message['clock'], message['sender'])

@app.route('/send-message', methods=['POST'])
def send_message():
    recipient = request.form.get('recipient')
    message = request.form.get('message')

    sender = int(request.form.get('sender'))  # ID do nó remetente
    sender_clock = clocks[sender]  # Vetor de relógio do nó remetente

    if recipient == 'broadcast':
        recipients = [node['node_id'] for node in nodes]
    else:
        recipients = [int(recipient)]

    for recipient_id in recipients:
        recipient_clock = clocks[recipient_id]  # Vetor de relógio do nó destinatário

        # Atualiza o vetor de relógio do remetente antes de enviar a mensagem
        sender_clock += 1
        clocks[sender] = sender_clock

        # Cria a mensagem com o vetor de relógio atualizado do remetente
        message_data = {
            'sender': sender,
            'recipient': recipient_id,
            'message': message,
            'clock': sender_clock
        }
        messages.append(message_data)

        # Atualiza o vetor de relógio do destinatário
        recipient_clock = max(recipient_clock, sender_clock)
        clocks[recipient_id] = recipient_clock

    # Ordena as mensagens utilizando o algoritmo de Lamport
    messages.sort(key=lamport_sort)

    return jsonify(messages), 200

@app.route('/get-messages/<int:node_id>', methods=['GET'])
def get_messages(node_id):
    # Ordena as mensagens utilizando o algoritmo de Lamport antes de retornar as mensagens do nó
    node_messages = [message for message in messages if message['recipient'] == node_id]
    node_messages.sort(key=lamport_sort)
    return jsonify(node_messages), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
