from quart import Quart, request, jsonify
from dotenv import load_dotenv
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

# Rota para enviar mensagens
@app.route("/send", methods=["POST"])
async def send():
    return jsonify({"text":"ok"})

# Rota para enviar mensagens
@app.route("/broadcast", methods=["POST"])
async def broadcast():
    return jsonify({"text":"ok"})

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_task(host="localhost", port=port))
