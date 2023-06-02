from dotenv import dotenv_values
import inspect
import asyncio
import aiohttp
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
        nodos.append({"name": name, "url": url, "is_sequencer": is_sequencer})

async def send(destination, message):
    calling_frame = inspect.currentframe().f_back
    calling_filename = inspect.getframeinfo(calling_frame).filename
    calling_filename = os.path.basename(calling_filename)
    calling_filename = os.path.splitext(calling_filename)[0]
    
    url = next((nodo["url"] for nodo in nodos if nodo["name"] == destination), None)
    if url is None:
        print(f"Destino {destination} não encontrado.")
        return None

    payload = {
            "sender": calling_filename,
            "destination": destination,
            "message": message
        }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url + '/receive', json=payload) as response:
                print(f'Response from {url}: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Erro ao conectar com {url}: {str(e)}')

async def broadcast(message):
    calling_frame = inspect.currentframe().f_back
    calling_filename = inspect.getframeinfo(calling_frame).filename
    calling_filename = os.path.basename(calling_filename)
    calling_filename = os.path.splitext(calling_filename)[0]

    sequenciador = next((nodo for nodo in nodos if nodo["is_sequencer"]), None)
    if sequenciador is None:
        print("Nenhum sequenciador encontrado.")
        return None

    url = sequenciador["url"]

    payload = {
        "sender": calling_filename,
        "destination": sequenciador["name"],
        "message": message
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url + '/sequencer', json=payload) as response:
                print(f'Response from {url}: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Erro ao conectar com {url}: {str(e)}')
