from flask import Flask, request
import threading
import numpy as np
import asyncio
import aiohttp
import json

app = Flask(__name__)

DB_FILE = "p2p_nodes.json"

received_sent_messages = []

received_broadcast_messages = []

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_node_count():
    data = load_db()
    nodes = data["nodes"]
    return len(nodes)

n =  get_node_count()
DELIV = np.zeros(n, dtype=int)
SENT = np.zeros((n, n), dtype=int)

def get_port_by_name(node_name):
    data = load_db()
    nodes = data["nodes"]
    for node in nodes:
        if node["name"] == node_name:
            return node["port"]
    return None

def get_index_by_name(node_name):
    data = load_db()
    nodes = data["nodes"]
    for i, node in enumerate(nodes):
        if node["name"] == node_name:
            return i
    return None

def start_flask(port):
    app.run(host='localhost', port=port)

def p2p_start(node_name, is_replication=None):
    global node
    node = node_name
    global replication
    replication = is_replication
    port = get_port_by_name(node_name)
    threading.Thread(target=start_flask, kwargs={'port': port}).start() 

def get_server_nodes():
    nodes = load_db()["nodes"]
    server_nodes = []
    for node in nodes:
        if node.get("is_server"):
            server_nodes.append(node)
    return server_nodes

def send(destination, message):
    if replication == 1:
        asyncio.run(_broadcast_servers_async(node, message))
    else:
        asyncio.run(_send_async(node, destination, message))

def broadcast_servers(sender, message):
    asyncio.run(_broadcast_servers_async(node, message))

async def _broadcast_servers_async(sender, message):
        
    seqnum = 1

    nodos = get_server_nodes()

    for nodo in nodos:
        if nodo["name"] != sender:
            payload = {
                "sender": sender,
                "message": message,
                "seqnum": seqnum
            }

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(f"http://localhost:{nodo['port']}/deliver_messages", json=payload) as response:
                        print(f"Response from {nodo['name']}: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {nodo['name']}: {str(e)}")

    seqnum += 1

    return json.dumps({"message": "Sequenciador com sucesso"})

async def _send_async(sender, destination, message, sd=None):

    sender_index = get_index_by_name(sender)
    destination_index = get_index_by_name(destination)

    if destination_index is None:
        print(f"Destino {destination} não encontrado.")
        return None

    STM = SENT[destination_index].copy()

    payload = {
        "sender": sender,
        "message": message,
        "destination": destination,
        "sd": sd,
        "stm": STM.tolist()
    }

    destination_port = str(get_port_by_name(destination))
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"http://localhost:{destination_port}/receive_messages", json=payload) as response:
                print(f"Response from {destination}: {response.status}")
        except aiohttp.ClientError as e:
            print(f"Error connecting to {destination}: {str(e)}")

    SENT[destination_index, sender_index] += 1

@app.route('/receive_messages', methods=['POST'])
def receive_messages():
    if replication == 2:
        asyncio.run(receive_and_send(request.json))
    else:
        asyncio.run(_receive_async(request.json))
    return json.dumps({"message": "Recebendo mensagem..."})

async def _receive_async(data):

    
    
    sender = data.get("sender")
    message = data.get("message")
    destination = data.get("destination")
    stm = np.array(data.get("stm"))        

    while True:

        if np.all(DELIV >= stm):

            received_sent_messages.append({
                "sender":sender,
                "message": message,
                "destination": destination
            })

            # if(node == destination):
                # print(f"Mensagem recebida: Remetente: {sender}, Mensagem: {message}, STM: {stm}")
            
            sender_index = get_index_by_name(sender)
            
            destination_index = get_index_by_name(destination)

            DELIV[sender_index] += 1
                
            SENT[sender_index, destination_index] += 1

            return json.dumps({"message": "Mensagem recebida pelo servidor"})

        await asyncio.sleep(0.1)

def get_nodes():
    nodos = load_db()["nodes"]
    return nodos

@app.route('/sequencer', methods=['POST'])
def sequencer():
    asyncio.run(_sequencer_async(request.json))
    return json.dumps({"message": "Recebendo mensagem..."})

async def _sequencer_async(data):

    sender = data.get("sender")
    message = data.get("message")
        
    seqnum = 1

    nodos = get_nodes()

    for nodo in nodos:
        if nodo["name"] != sender:
            payload = {
                "sender": sender,
                "message": message,
                "seqnum": seqnum
            }

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(f"http://localhost:{nodo['port']}/deliver_messages", json=payload) as response:
                        print(f"Response from {nodo['name']}: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {nodo['name']}: {str(e)}")

    seqnum += 1

    return json.dumps({"message": "Sequenciador com sucesso"})

@app.route('/deliver_messages', methods=['POST'])
def deliver_messages():
    asyncio.run(_deliver_async(request.json))
    return json.dumps({"message": "Recebendo mensagem..."})

async def _deliver_async(data):

    sender = data.get("sender")
    message = data.get("message")
    seqnum = data.get("seqnum")
    
    nextdeliver = 1

    pending_messages = []

    pending_messages.append({
        "sender": sender,
        "message": message,
        "seqnum": seqnum
    })

    while pending_messages:

        messages_to_remove = []

        for message_info in pending_messages:
            sender = message_info["sender"]
            message = message_info["message"]
            seqnum = message_info["seqnum"]

            if seqnum == nextdeliver:
                received_broadcast_messages.append({
                    "sender": sender,
                    "message": message
                })

                # if(node != sender):
                    # print(f"Mensagem recebida: Remetente: {sender}, Mensagem: {message}")

                messages_to_remove.append(message_info)

        for message_info in messages_to_remove:
            pending_messages.remove(message_info)

        nextdeliver += 1

        await asyncio.sleep(0.1)

    return json.dumps({"message": "Falha ao receber a mensagem"})

def get_sequencer_info():
    data = load_db()
    nodes = data["nodes"]
    for node in nodes:
        if node["is_sequencer"]:
            return node["name"], node["port"]
    return None, None

def broadcast(message):
    sequencer_name, sequencer_port = get_sequencer_info()
    asyncio.run(_broadcast_async(message, sequencer_name, sequencer_port))

async def _broadcast_async(message, sequencer_name, sequencer_port):
    
    payload = {
        "sender": node,
        "message": message
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"http://localhost:{sequencer_port}/sequencer", json=payload) as response:
                print(f'Response from {sequencer_name}: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Erro ao conectar com {sequencer_name}: {str(e)}')

def receive():
    return received_sent_messages

def deliver():
    return received_broadcast_messages

async def receive_and_send(data):
    await _receive_and_send_async(data)

async def _receive_and_send_async(data):

    tasks = []

    receive_task = asyncio.create_task(_receive_async(data))
    tasks.append(receive_task)

    sender = data.get("sender")
    destination = data.get("destination")
    message = data.get("message")

    servers = get_server_nodes()

    if data.get('sd') is None:
        for server in servers:
            if server['name'] != sender and server['name'] != destination:
                send_task = asyncio.create_task(_send_async(sender, server['name'], message, True))
                tasks.append(send_task)

    await asyncio.gather(*tasks)

    return json.dumps({"message": "Mensagem recebida e enviada para os nós do servidor"})
