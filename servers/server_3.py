from flask import Flask, request, jsonify
import numpy as np
import requests
import asyncio

app = Flask(__name__)

# Dicionário para mapear os destinos para servidores e portas correspondentes
destinations = {
    "server-1": "http://localhost:8001",
    "server-2": "http://localhost:8002",
    "server-3": "http://localhost:8003"
}

port = 8003
server = "server-3"

# Lista para armazenar as mensagens recebidas
received_messages = []

# Matrizes DELIV e SENT
n = len(destinations)
DELIV = np.zeros(n, dtype=int)
SENT = np.zeros((n, n), dtype=int)

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    destination = data.get("destination")
    message = data.get("message")

    if not destination or not message:
        return "Erro: parâmetros ausentes", 400

    if destination not in destinations:
        return "Erro: destino inválido", 400

    STM = SENT[destinations[destination]].copy()

    payload = {
        "sender": server,
        "message": message,
        "stm": STM.tolist()
    }

    url = f"{destinations[destination]}/receive"
    response = requests.post(url, json=payload)

    return jsonify({
        "message": "Mensagem recebida pelo servidor"
    })

# Rota para receber mensagens
@app.route("/receive", methods=["POST"])
def receive():
    data = request.get_json()
    sender = data.get("sender")
    message = data.get("message")
    stm = np.array(data.get("stm"))

    asyncio.create_task(process_message(sender, message, stm))

    return jsonify({
        "message": "Mensagem recebida pelo servidor"
    })
    
# Função assíncrona para processar a entrega de mensagens
async def process_message(sender, message, stm):
    if np.all(DELIV >= stm):
        received_messages.append({
            "sender": sender,
            "message": message
        })
                
        DELIV[destinations[sender]] += 1
        SENT[destinations[sender], destinations[server]] += 1

        return jsonify({
            "message": "Mensagem recebida pelo servidor"
        })

    else:
        # Aguardar um curto período de tempo antes de tentar novamente
        await asyncio.sleep(0.1)
        await process_message(sender, message, stm)
    
@app.route("/broadcast", methods=["POST"])
def broadcast():
    data = request.get_json()
    if data and "message" in data:
        message = data["message"]

        for destination, url in destinations.items():
            if destination != server:
                payload = {"sender": server, "message": message}
                response = requests.post(f"{url}/receive", json=payload)

        return "Broadcast realizado com sucesso"
    
    return "Erro: mensagem ausente"

if __name__ == "__main__":
    app.run(host="localhost", port=port)
