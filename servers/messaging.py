# Importa as bibliotecas necessárias
from dotenv import dotenv_values
import numpy as np
import asyncio
import aiohttp
import inspect
import json
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

# Pega o tamanho dos nodos, no caso 3
n = len(nodos)

# Cria o array de DELIV do raynal
DELIV = np.zeros(n, dtype=int)

# Cria a matriz sent do raynal
SENT = np.zeros((n, n), dtype=int)

# Armazena o log
received_messages = []

# Para não explicitar o assíncrono no servidor, esse método chama _send_async que vai ser o send de forma assíncrona 
# Vai verificar se no envio tem o sender
# Se não tiver, quer dizer que é de servidor para servidor
# Nesse caso o calling_XXX vai ser para pegar o nome do arquivo que chamou a função
# E vai servir como identificador único e persistente do servidor
# Já se tiver o sender, vai ser quando o cliente envia
# E define o sender pelo que foi enviado
def send(data):
    if 'sender' not in data:
        calling_frame = inspect.currentframe().f_back
        calling_filename = inspect.getframeinfo(calling_frame).filename
        sender = os.path.basename(calling_filename)

        if sender is None:
            print(f"Remetende para o {calling_filename} não encontrado.")
            return None
    else:
        sender = data.get("sender")

    asyncio.run(_send_async(sender, data))

# Função send propriamente dita
async def _send_async(sender, data):
    
    # O sender até aqui é o nome do arquivo
    # Vai pegar o nome do sender pelo nome do arquivo
    sender = get_name_by_filename(sender)

    # Vai pegar o destinatário
    destination = data.get("destination")
    
    # Vai pegar a mensagem
    message = data.get("message")

    # Aqui o destino é enviado pelo nome dele
    # Vai pegar o índice no nodos pelo nome,caso contrário vai informar não encontrado
    destination_index = get_index_by_name(destination)

    if destination_index is None:
        print(f"Destino {destination} não encontrado.")
        return None

    # Copia a matriz SENT na linha do índice do destino
    STM = SENT[destination_index].copy()

    # Gera a mensagem a ser enviada
    payload = {
        "sender": sender,
        "message": message,
        "destination": destination,
        "stm": STM.tolist()
    }

    # Pega a url para qual vai ser enviada a mensagem
    url = nodos[destination_index]["url"]
    
    # Envia de forma que se o servidor não for encontrado, informa o erro
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url + '/receive', json=payload) as response:
                print(f'Response from {url}: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Error connecting to {url}: {str(e)}')

def receive(data):
    calling_frame = inspect.currentframe().f_back
    calling_filename = inspect.getframeinfo(calling_frame).filename
    calling_filename = os.path.basename(calling_filename)

    asyncio.run(_receive_async(calling_filename, data))

async def _receive_async(calling_filename, data):
    sender = data.get("sender")
    message = data.get("message")
    
    sender_found = False
    for key, value in env_variables.items():
        if key.startswith("NODO_") and value == sender:
            sender_found = True
            break

    if not sender_found:
        sender = calling_filename

        for nodo in nodos:
            payload = {"sender": sender, "destination": nodo["name"], "message": message}
            url = get_url_by_filename(sender)
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(url + '/send', json=payload) as response:
                        print(f"Response from {url}: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {url}: {str(e)}")

    else:

        destination = data.get("destination")
        stm = np.array(data.get("stm"))

        while True:
            if np.all(DELIV >= stm):
                received_messages.append({
                    "sender":sender,
                    "message": message
                })
                
                sender_index = get_index_by_name(sender)
                destination_index = get_index_by_name(destination)

                DELIV[sender_index] += 1
                SENT[sender_index, destination_index] += 1

                return "Mensagem recebida pelo servidor"

            await asyncio.sleep(0.1)

def sequencer(data):
    asyncio.run(_sequencer_async(data))

async def _sequencer_async(data):
    if data and "message" in data:
        message = data["message"]

        seqnum = 1

        for nodo in nodos:
            payload = {"message": message, "seqnum": seqnum}
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(url + '/deliver', json=payload) as response:
                        print(f"Response from {url}: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {url}: {str(e)}")

        seqnum += 1

        return "Sequenciador com sucesso"
    
    return "Falha no sequenciador"

def deliver(data):
    asyncio.run(_deliver_async(data))

async def _deliver_async(data):
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

    return json.dumps({"message": "Mensagem recebida pelo servidor"})

def get_messages():
    return json.dumps(received_messages)

def get_port_by_filename(filename):
    numero = filename.split("_")[1].split(".")[0]
    chave_porta = f"NODO_{numero}_PORT"
    porta = env_variables.get(chave_porta)
    if porta:
        return porta
    return None

def get_index_by_name(name):
    for index, nodo in enumerate(nodos):
        if nodo['name'] == name:
            return index
    return None

def get_name_by_filename(filename):
    for key, value in env_variables.items():
        if key == f"NODO_{filename.split('_')[1].split('.')[0]}_NAME":
            return value
    return None

def get_url_by_filename(filename):
    server_number = filename.split("_")[1].split(".")[0]
    for nodo in nodos:
        if nodo['name'] == server_number:
            return nodo['url']
    return None