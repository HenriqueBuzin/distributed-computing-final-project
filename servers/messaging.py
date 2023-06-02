from dotenv import dotenv_values
import numpy as np
import asyncio
import aiohttp
import inspect
import json
import os

env_variables = dotenv_values()

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

n = len(nodos)
DELIV = np.zeros(n, dtype=int)
SENT = np.zeros((n, n), dtype=int)

received_messages = []

async def send(data):
    if 'sender' not in data:
        calling_frame = inspect.currentframe().f_back
        calling_filename = inspect.getframeinfo(calling_frame).filename
        sender = os.path.basename(calling_filename)

        if sender is None:
            print(f"Remetende para o {calling_filename} não encontrado.")
            return None
    else:
        sender = data.get("sender")
    
    sender = get_name_by_filename(sender)
    destination = data.get("destination")
    message = data.get("message")

    destination_index = get_index_by_name(destination)
    print("XXX")
    print(destination_index)
    print("XXX")


    if destination_index is None:
        print(f"Destino {destination} não encontrado.")
        return None

    STM = SENT[destination_index].copy()

    payload = {
        "sender": sender,
        "message": message,
        "destination": destination,
        "stm": STM.tolist()
    }

    url = nodos[destination_index]["url"]
    print(payload)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url + '/receive', json=payload) as response:
                print(f'Response from {url}: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Error connecting to {url}: {str(e)}')

async def receive(data):

    sender = data.get("sender")    
    destination = data.get("destination")
    message = data.get("message")
    
    sender_found = False
    for key, value in env_variables.items():
        if key.startswith("NODO_") and value == sender:
            sender_found = True
            break

    if not sender_found:
        calling_frame = inspect.currentframe().f_back
        calling_filename = inspect.getframeinfo(calling_frame).filename
        sender = os.path.basename(calling_filename)

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

async def get_messages():
    return json.dumps(received_messages)

def get_port(filename):
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