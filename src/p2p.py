from flask import Flask, request
import threading
import numpy as np
import asyncio
import aiohttp
import json

app = Flask(__name__)

DB_FILE = "p2p_nodes.json"

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

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
    app.run(host='localhost', port=port, debug=False, use_reloader=False)

def p2p_start(node_name, is_replication=None):
    global node
    node = node_name
    global replication
    replication = is_replication
    port = get_port_by_name(node_name)
    threading.Thread(target=start_flask, kwargs={'port': port}).start() 

def get_node_count():
    data = load_db()
    nodes = data["nodes"]
    return len(nodes)

n = get_node_count()
DELIV = np.zeros(n, dtype=int)
SENT = np.zeros((n, n), dtype=int)

def send(message, destination):
    if replication == 1:
        broadcast(message)
    else:
        asyncio.run(_send_async(node, destination, message))

async def _send_async(sender, destination, message):

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
        "stm": STM.tolist()
    }

    destination_port = str(get_port_by_name(destination))
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"http://localhost:{destination_port}/receive", json=payload) as response:
                print(f"Response from {destination}: {response.status}")
        except aiohttp.ClientError as e:
            print(f"Error connecting to {destination}: {str(e)}")

    SENT[destination_index, sender_index] += 1

@app.route('/receive', methods=['POST'])
def receive():
    asyncio.run(_receive_async(request.json))
    return json.dumps({"message": "Recebendo mensagem..."})

received_messages = []

async def _receive_async(data):

    sender = data.get("sender")
    message = data.get("message")
    destination = data.get("destination")
    stm = np.array(data.get("stm"))        

    while True:

        if np.all(DELIV >= stm):

            received_messages.append({
                "sender":sender,
                "message": message,
                "destination": destination,
                "stm": stm
            })

            if(node == destination):
                print(f"Mensagem recebida: Remetente: {sender}, Mensagem: {message}, STM: {stm}")
            
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
                    async with session.post(f"http://localhost:{nodo['port']}/deliver", json=payload) as response:
                        print(f"Response from {nodo['name']}: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {nodo['name']}: {str(e)}")

    seqnum += 1

    return json.dumps({"message": "Sequenciador com sucesso"})

@app.route('/deliver', methods=['POST'])
def deliver():
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
                received_messages.append({
                    "sender": sender,
                    "message": message
                })

                if(node != sender):
                    print(f"Mensagem recebida: Remetente: {sender}, Mensagem: {message}")

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
