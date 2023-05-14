from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Dicionário para mapear os destinos para servidores e portas correspondentes
destinations = {
    "server-1": "http://localhost:8001",
    "server-2": "http://localhost:8002",
    "server-3": "http://localhost:8003"
}

port = 8002
server = "server-2"

# Lista para armazenar as mensagens recebidas
received_messages = []

# Dicionário para rastrear os relógios lógicos dos servidores
logical_clocks = {
    "server-1": 0,
    "server-2": 0,
    "server-3": 0
}


@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    destination = data.get("destination")
    message = data.get("message")

    if not destination or not message:
        return "Erro: parâmetros ausentes", 400

    if destination not in destinations:
        return "Erro: destino inválido", 400

    # Incrementa o relógio lógico do servidor atual
    logical_clocks[server] += 1

    # Adiciona o relógio lógico à mensagem
    payload = {
        "sender": server,
        "message": message,
        "logical_clock": logical_clocks[server]
    }

    url = f"{destinations[destination]}/receive"
    response = requests.post(url, json=payload)

    # Retorna a resposta com o relógio lógico
    return jsonify({
        "message": "Mensagem recebida pelo servidor",
        "logical_clock": logical_clocks[server]
    })

@app.route("/receive", methods=["GET", "POST"])
def get_received_messages():
    if request.method == "GET":
        return jsonify(received_messages)
    elif request.method == "POST":
        data = request.get_json()
        sender = data.get("sender")
        message = data.get("message")
        logical_clock = data.get("logical_clock")

        # Atualiza o relógio lógico do servidor atual
        logical_clocks[server] = max(logical_clocks[server], logical_clock) + 1

        received_messages.append({
            "sender": sender,
            "message": message,
            "logical_clock": logical_clock
        })

        # Retorna a resposta com o relógio lógico
        return jsonify({
            "message": "Mensagem recebida pelo servidor",
            "logical_clock": logical_clocks[server]
        })

@app.route("/broadcast", methods=["POST"])
def broadcast():
    data = request.get_json()
    if data and "message" in data:
        message = data["message"]

        # Incrementa o relógio lógico do servidor atual
        logical_clocks[server] += 1

        for destination, url in destinations.items():
            if destination != server:
                payload = {"sender": server, "message": message, "logical_clock": logical_clocks[server]}
                response = requests.post(f"{url}/receive", json=payload)

                if response.status_code == 200:
                    # Atualiza o relógio lógico do servidor atual com base no relógio lógico do destinatário
                    logical_clocks[server] = max(logical_clocks[server], response.json()["logical_clock"]) + 1

        return "Broadcast realizado com sucesso"
    
    return "Erro: mensagem ausente"

if __name__ == "__main__":
    app.run(host="localhost", port=port)
