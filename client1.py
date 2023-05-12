from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Dicionário para mapear os destinos para servidores e portas correspondentes
destinations = {
    "server-1": "http://localhost:8001",
    "server-2": "http://localhost:8002",
    "server-3": "http://localhost:8003"
}

# Lista para armazenar as mensagens recebidas
received_messages = []

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    destination = data.get("destination")
    message = data.get("message")

    if not destination or not message:
        return "Erro: parâmetros ausentes", 400

    if destination not in destinations:
        return "Erro: destino inválido", 400

    url = f"{destinations[destination]}/message"
    payload = {"sender": destination, "message": message}
    response = requests.post(url, json=payload)

    return "Mensagem enviada com sucesso"

@app.route("/message", methods=["POST"])
def receive_message():
    data = request.get_json()
    sender = data.get("sender")
    message = data.get("message")
    received_messages.append({sender: message})
    return "Mensagem recebida pelo servidor"

@app.route("/receive", methods=["GET"])
def get_received_messages():
    return jsonify(received_messages)

if __name__ == "__main__":
    app.run(host="localhost", port=8001)
