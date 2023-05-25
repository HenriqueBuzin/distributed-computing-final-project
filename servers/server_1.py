from quart import Quart, request, jsonify
from dotenv import load_dotenv
import numpy as np
import aiohttp
import asyncio
import os

app = Quart(__name__)

load_dotenv()

# Constrói a lista de destinos a partir das variáveis do arquivo .env
destinations = []

# Assuming the maximum number of servers is known or can be determined
max_servers = int(os.getenv("MAX_SERVERS"))
server=None

for i in range(1, max_servers + 1):
    name = os.getenv(f"SERVER_{i}_NAME")
    url = os.getenv(f"SERVER_{i}_URL")
    is_sequencer = os.getenv(f"SERVER_{i}_IS_SEQUENCER") == "True"
    port = int(os.getenv(f"SERVER_{i}_PORT"))
    category = os.getenv(f"SERVER_{i}_CATEGORY")
    is_server = False
    
    # Verifica o nome do arquivo para definir is_server=True no servidor correspondente
    if os.path.basename(__file__) == f"server_{i}.py":
        is_server = True
        server = {
            "name": name,
            "url": url,
            "is_sequencer": is_sequencer,
            "port": port,
            "category": category,
            "is_server": is_server
        }

    destination = {
        "name": name,
        "url": url,
        "is_sequencer": is_sequencer,
        "port": port,
        "category": category,
        "is_server": is_server
    }
    
    destinations.append(destination)

if not server:
    print("Erro: servidor não encontrado")
    raise Exception("Servidor não encontrado")

port = server["port"]
if not port:
    print("Erro: porta não definida")
    raise Exception("Porta não definida")

# Matrizes DELIV e SENT
n = len(destinations)
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

    destination_info = next((d for d in destinations if d["name"] == destination), None)
    if not destination_info:
        return "Erro: destino inválido", 400


    destination_index = next((i for i, d in enumerate(destinations) if d["name"] == destination_info["name"]), None)
    if destination_index is None:
        return "Erro: índice do destino não encontrado", 500

    STM = SENT[destination_index].copy()

    payload = {
        "sender": server["name"],
        "message": message,
        "stm": STM.tolist()
    }
    
    print(payload)
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
            for destination in destinations:
                if destination["is_sequencer"]:
                    url = f"{destination['url']}/sequencer"
                    payload = {"message": message}

                    tasks.append(session.post(url, json=payload))

            await asyncio.gather(*tasks)

        return "Mensagem enviada com sucesso para os sequenciadores"

    return "Erro: mensagem ausente"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_task(host="localhost", port=port))
