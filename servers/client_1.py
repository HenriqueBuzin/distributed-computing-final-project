from quart import Quart, request, jsonify
from dotenv import load_dotenv
import numpy as np
import aiohttp
import asyncio
import os

app = Quart(__name__)

load_dotenv()

port = int(os.getenv("CLIENT_1_PORT"))

# Constrói a lista de réplicas a partir das variáveis do arquivo .env
replicas = []

for i in range(1, 4):
    name = os.getenv(f"SERVER_{i}_NAME")
    url = os.getenv(f"SERVER_{i}_URL")
    is_sequencer = os.getenv(f"SERVER_{i}_IS_SEQUENCER") == "True"
    
    replica = {
        "name": name,
        "is_sequencer": is_sequencer,
        "url": url
    }
    
    replicas.append(replica)

# Matrizes DELIV e SENT
n = len(replicas)
DELIV = np.zeros(n, dtype=int)
SENT = np.zeros((n, n), dtype=int)

# Rota para enviar mensagens
@app.route("/send", methods=["POST"])
async def send():
    data = await request.get_json()
    destination = data.get("destination")
    message = data.get("message")

    if not destination or not message:
        return "Erro: parâmetros ausentes", 400

    destination_info = next((d for d in replicas if d["name"] == destination), None)
    if not destination_info:
        return "Erro: destino inválido", 400


    destination_index = next((i for i, d in enumerate(replicas) if d["name"] == destination_info["name"]), None)
    if destination_index is None:
        return "Erro: índice do destino não encontrado", 500

    STM = SENT[destination_index].copy()

    payload = {
        "message": message,
        "stm": STM.tolist()
    }

    destination_url = destination_info["url"]
    url = f"{destination_url}/receive"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return jsonify({"message": "Mensagem recebida pelo servidor"})

# Rota para enviar mensagens
@app.route("/broadcast", methods=["POST"])
async def broadcast():
    data = await request.get_json()

    if data and "message" in data:
        message = data["message"]

        tasks = []
        async with aiohttp.ClientSession() as session:
            for replica in replicas:
                if replica["is_sequencer"]:
                    url = f"{replica['url']}/sequencer"
                    payload = {"message": message}

                    tasks.append(session.post(url, json=payload))

            await asyncio.gather(*tasks)

        return "Mensagem enviada com sucesso para os sequenciadores"

    return "Erro: mensagem ausente"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_task(host="localhost", port=port))
