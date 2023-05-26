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

# Lista para armazenar as mensagens recebidas
received_messages = []

# Matrizes DELIV e SENT
n = len(destinations)
DELIV = np.zeros(n, dtype=int)
SENT = np.zeros((n, n), dtype=int)

if not server:
    print("Erro: servidor não encontrado")
    raise Exception("Servidor não encontrado")

port = server["port"]
if not port:
    print("Erro: porta não definida")
    raise Exception("Porta não definida")

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
        "sender":server["name"],
        "message": message,
        "stm": STM.tolist()
    }

    destination_url = destination_info["url"]
    url = f"{destination_url}/receive"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return jsonify({"message": "Mensagem recebida pelo servidor"})

# Rota para receber mensagens
@app.route("/receive", methods=["POST", "GET"])
async def receive():

    if request.method == "GET":
        return jsonify(received_messages)
    
    data = await request.get_json()

    if data is None:
        return jsonify({"message": "Erro: dados ausentes"}), 400
    
    sender = data.get("sender")
    message = data.get("message")
    stm = np.array(data.get("stm"))

    if np.all(DELIV >= stm):
        received_messages.append({
            "sender":sender,
            "message": message
        })
        
        sender_info = next((d for d in destinations if d["name"] == sender), None)
        if not sender_info:
            return jsonify({
                "message": "Erro: remetente inválido"
            })

        sender_index = destinations.index(sender_info)

        DELIV[sender_index] += 1
        SENT[sender_index, destinations.index(server)] += 1

        if sender_info["category"] == "CLIENT":
            # Encaminhar a mensagem para os outros servidores
            for destination in destinations:
                if destination["category"] == "SERVER" and destination["name"] != server["name"]:
                    url = f"{server['url']}/send"
                    payload = {"destination": destination["name"], "message": message}

                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload) as response:
                            response_data = await response.json()
                            # Process the response data if needed

        return jsonify({
            "message": "Mensagem recebida pelo servidor"
        })

    else:
        # Aguardar um curto período de tempo antes de tentar novamente
        await asyncio.sleep(0.1)
        return await receive()

@app.route("/sequencer", methods=["POST"])
async def sequencer():

    data = await request.get_json()

    if data and "message" in data:
        message = data["message"]

        seqnum = 1

        for destination in destinations:
            if destination["category"] == "SERVER":
                payload = {"message": message, "seqnum": seqnum}
                async with aiohttp.ClientSession() as session:
                    await session.post(f"{destination['url']}/deliver", json=payload)

        seqnum += 1

        return "Sequenciador com sucesso"
    
    return "Falha no sequenciador"

@app.route("/deliver", methods=["POST"])
async def deliver():
    
    data = await request.get_json()

    if data and "message" in data and "seqnum" in data:
        message = data["message"]
        seqnum = data["seqnum"]

        nextdeliver = 1

        pending_messages = []

        pending_messages.append({
            "message": message,
            "seqnum": seqnum
        })

        while pending_messages:
            messages_to_remove = []

            for message_info in pending_messages:
                message = message_info["message"]
                seqnum = message_info["seqnum"]

                if seqnum == nextdeliver:
                    received_messages.append({
                        "message": message
                    })

                    messages_to_remove.append(message_info)

            for message_info in messages_to_remove:
                pending_messages.remove(message_info)

            nextdeliver += 1

            await asyncio.sleep(0.1)

    return jsonify({"message": "Mensagem recebida pelo servidor"})

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_task(host="localhost", port=port))
