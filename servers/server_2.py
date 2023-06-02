from messaging import get_port, send, receive, get_messages, sequencer
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

nome_arquivo = os.path.basename(__file__)
port = get_port(nome_arquivo)

@app.route('/send', methods=['POST'])
def send_message():
    send(request.json)
    return jsonify({"message": "Mensagem enviada pelo servidor"})

@app.route('/receive', methods=['POST'])
def handle_receive():
    receive(request.json)
    return jsonify({"message": "Mensagem recebida pelo servidor"})

@app.route("/sequencer", methods=["POST"])
def process_sequencer():
    sequencer(request.json)
    return jsonify({"message": "Mensagem recebida pelo servidor"})

@app.route('/messages', methods=['GET'])
def messages():
    return get_messages()

if __name__ == '__main__':
    app.run(port=port)
