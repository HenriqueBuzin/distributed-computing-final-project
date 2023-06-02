# Importa as bibliotecas necessárias
from dotenv import dotenv_values
import inspect
import asyncio
import aiohttp
import os

# Lê o .env
env_variables = dotenv_values()

# Gera os nodos a partir do .env
# Formato:
# [
#   {'name': '1', 'url': 'http://localhost:8001', 'is_sequencer': 'True'}, 
#   {'name': '2', 'url': 'http://localhost:8002', 'is_sequencer': 'False'}, 
#   {'name': '3', 'url': 'http://localhost:8003', 'is_sequencer': 'False'}
# ]
nodos = []

for key, value in env_variables.items():
    if key.startswith("NODO_"):
        nodo = key.split("_")[1]
        name = env_variables.get(f"NODO_{nodo}_NAME")
        is_sequencer = env_variables.get(f"NODO_{nodo}_IS_SEQUENCER")
        port = env_variables.get(f"NODO_{nodo}_PORT")
        url = f"http://localhost:{port}"

        if not any(nodo["name"] == name for nodo in nodos):
            nodos.append({"name": name, "url": url, "is_sequencer": is_sequencer})

# Para não explicitar o assíncrono no cliente, esse método chama _send_async que vai ser o send de forma assíncrona 
# O calling_XXX vai ser para pegar o nome do arquivo que chamou a função
# Vai servir como identificador único e persistente do client
def send(destination, message):
    calling_frame = inspect.currentframe().f_back
    calling_filename = inspect.getframeinfo(calling_frame).filename
    calling_filename = os.path.basename(calling_filename)
    sender = os.path.splitext(calling_filename)[0]

    asyncio.run(_send_async(sender, destination, message))

# Função send propriamente dita
async def _send_async(sender, destination, message):

    # Vai pegar a url pelo nome do destino, caso contrário vai informar não encontrado
    url = next((nodo["url"] for nodo in nodos if nodo["name"] == destination), None)
    if url is None:
        print(f"Destino {destination} não encontrado.")
        return None

    # Gera a mensagem a ser enviada
    payload = {
            "sender": sender,
            "destination": destination,
            "message": message
        }

    # Envia de forma que se o servidor não for encontrado, informa o erro
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url + '/receive', json=payload) as response:
                print(f'Response from {url}: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Erro ao conectar com {url}: {str(e)}')

# Para não explicitar o assíncrono no cliente, esse método chama _broadcast_async que vai ser o broadcast de forma assíncrona 
# O calling_XXX vai ser para pegar o nome do arquivo que chamou a função
# Vai servir como identificador único e persistente do client
def broadcast(message):
    calling_frame = inspect.currentframe().f_back
    calling_filename = inspect.getframeinfo(calling_frame).filename
    calling_filename = os.path.basename(calling_filename)
    sender = os.path.splitext(calling_filename)[0]

    asyncio.run(_broadcast_async(sender, message))

# Função broadcast propriamente dita
async def _broadcast_async(sender, message):
    
    # Vai pegar as informações do nodo que é o sequenciador, caso contrário vai informar não encontrado
    sequenciador = next((nodo for nodo in nodos if nodo["is_sequencer"]), None)
    if sequenciador is None:
        print("Nenhum sequenciador encontrado.")
        return None

    # Cria a variável url a partir do sequenciador encontrado
    url = sequenciador["url"]

    # Gera a mensagem a ser enviada
    payload = {
        "sender": sender,
        "destination": sequenciador["name"],
        "message": message
    }

    # Envia de forma que se o servidor não for encontrado, informa o erro
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url + '/sequencer', json=payload) as response:
                print(f'Response from {url}: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Erro ao conectar com {url}: {str(e)}')
