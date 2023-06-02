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

    # O sender até aqui é o nome do arquivo
    # Vai pegar o nome do sender pelo nome do arquivo
    sender = get_name_by_filename(sender)

    # Vai pegar o destinatário
    destination = data.get("destination")
    
    # Vai pegar a mensagem
    message = data.get("message")

    asyncio.run(_send_async(sender, destination, message))

# Função send propriamente dita
async def _send_async(sender, destination, message):

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

# Para não explicitar o assíncrono no servidor, esse método chama _receive_async que vai ser o send de forma assíncrona 
# Quando um cliente envia uma mensagem para um servidor, é o receive que recebe
# Nesse caso o calling_XXX vai ser para pegar o nome do arquivo que chamou a função 
def receive(data):
    calling_frame = inspect.currentframe().f_back
    calling_filename = inspect.getframeinfo(calling_frame).filename
    calling_filename = os.path.basename(calling_filename)

    asyncio.run(_receive_async(calling_filename, data))

# Função send propriamente dita
async def _receive_async(calling_filename, data):

    # Atribui a variável sender o sender da requisição
    sender = data.get("sender")

    # Atribui a variável message o message da requisição
    message = data.get("message")
    
    # Quando o cliente envia a mensagem, envia com o sender como client_1, por exemplo
    # Aqui ele vai procurar se tem algum algum servidor com o nome do sender
    sender_found = False
    for key, value in env_variables.items():
        if key.startswith("NODO_") and value == sender:
            sender_found = True
            break

    # Ao não encontrar nos nodos um servidor com o nome que veio no sender, significa que veio de um cliente
    if not sender_found:

        # Então agora ele atribui o sender como o servidor que recebeu do cliente
        sender = calling_filename

        # Aqui ele vai chamar a função sender do servidor que recebeu do cliente para cada nodo no .env
        # Utilizando o sender como agora o servidor que recebeu
        # Destino como cada nó em .env
        # A mesma mensagem
        # Isso vai fazer com que o servidor que recebeu a mensagem do cliente
        # Envie para todos, respeitando a ordem causal
        for nodo in nodos:
            payload = {"sender": sender, "destination": nodo["name"], "message": message}
            url = get_url_by_filename(sender)
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(url + '/send', json=payload) as response:
                        print(f"Response from {url}: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {url}: {str(e)}")

    # Agora se encontrou, quer dizer que foi enviada por um servidor
    else:

        # Atribui a variável destination o destination da requisição
        destination = data.get("destination")
    
        # Reconstroi o stm da requisição
        # Atribui a variável stm o stm da requisição
        stm = np.array(data.get("stm"))

        # Um loop eterno que fica executando até a condição ser satisfeita
        while True:

            # Aqui ele vai comparar para verificar a ordem causal
            # Vai pegar o primeiro elemento do deliv e comparar com o primeiro do stm
            # E assim consecutivamente, se um deles não satisfazerm já retorna falso
            if np.all(DELIV >= stm):

                # Se atendeu a ordem causal, é adicionado nas mensagens recebidas
                received_messages.append({
                    "sender":sender,
                    "message": message
                })
                
                # Pega o index do sender
                sender_index = get_index_by_name(sender)
                
                # Pega o index do destination
                destination_index = get_index_by_name(destination)

                # Atualiza a matriz DELIV
                DELIV[sender_index] += 1
                
                # Atualiza a matriz SENT
                SENT[sender_index, destination_index] += 1

                # Retorna para sair do loop
                return json.dumps({"message": "Mensagem recebida pelo servidor"})

            # Aguarda um tempo para verificar novamente
            await asyncio.sleep(0.1)

# Para não explicitar o assíncrono no servidor, esse método chama _sequencer_async que vai ser o sequencer de forma assíncrona 
def sequencer(data):
    asyncio.run(_sequencer_async(data))

# Função sequencer propriamente dita
async def _sequencer_async(data):
    
    # Verifica se tem a mensagem, se não retorna uma mensagem de erro
    if data and "message" in data:

        # Atribui a variável message a message recebida
        message = data["message"]

        # Cria o seqnum, igual em defago
        seqnum = 1

        # Ele envia a mensagem para todos os nodos na rota deliver
        for nodo in nodos:
            payload = {"message": message, "seqnum": seqnum}
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(nodo['url'] + '/deliver', json=payload) as response:
                        print(f"Response from {url}: {response.status}")
                except aiohttp.ClientError as e:
                    print(f"Error connecting to {url}: {str(e)}")

        # Aumento o seqnum, igual em defago
        seqnum += 1

        # Retorno de êxito
        return json.dumps({"message": "Sequenciador com sucesso"})
    
    return json.dumps({"message": "Falha no sequenciador"})

# Para não explicitar o assíncrono no servidor, esse método chama _deliver_async que vai ser o deliver de forma assíncrona 
def deliver(data):
    asyncio.run(_deliver_async(data))

# Deliver propriamente dito
async def _deliver_async(data):

    # Verifica se tem a mensagem e o seqnum na mensagem, se não retorna mensagem de erro
    if data and "message" in data and "seqnum" in data:
        
        # Atribui a variável message a message recebida
        message = data["message"]
        
        # Atribui a variável seqnum a seqnum recebida
        seqnum = data["seqnum"]

        # Inicia o nextdeliver como defago
        nextdeliver = 1

        # Guarda as mensagens pendentes
        pending_messages = []

        # Adiciona a mensagem pendende e o seqnum as mensagens pendentrs
        pending_messages.append({
            "message": message,
            "seqnum": seqnum
        })

        # Loop enquanto existir mensagens em mensagens pendentes
        while pending_messages:

            # Armazena as mensagens para remover de mensagens pendentes
            messages_to_remove = []

            # Para cada mensagem pendente pega a mensagem e o seqnum
            for message_info in pending_messages:
                message = message_info["message"]
                seqnum = message_info["seqnum"]

                # Verifica se o seqnum é igual ao nextdeliver
                # Se for adiciona em mensagens recebidas
                if seqnum == nextdeliver:
                    received_messages.append({
                        "message": message
                    })

                    # Adiciona em mensagens a remover de mensagens pendentes
                    messages_to_remove.append(message_info)

            # Remove as mensagens pendentes marcadas para serem removida
            for message_info in messages_to_remove:
                pending_messages.remove(message_info)

            # Atualiza o nextdeliver
            nextdeliver += 1

            # Em caso que não satisfaça, aguarde para tentar novamente
            await asyncio.sleep(0.1)

    # Retorno de  êxito
    return json.dumps({"message": "Falha ao receber a mensagem"})

# Para não explicitar o assíncrono no servidor, esse método chama _broadcast_async que vai ser o broadcast de forma assíncrona 
# O calling_XXX vai ser para pegar o nome do arquivo que chamou a função
# Vai servir como identificador único e persistente do servidor
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

# Retorna as mensagens recebidas
def get_messages():
    return json.dumps(received_messages)

# Retorna a porta do nodo pelo nome do arquivo
def get_port_by_filename(filename):
    numero = filename.split("_")[1].split(".")[0]
    chave_porta = f"NODO_{numero}_PORT"
    porta = env_variables.get(chave_porta)
    if porta:
        return porta
    return None

# Retorna o índice do nodo em nodos pelo nome do nodo
def get_index_by_name(name):
    for index, nodo in enumerate(nodos):
        if nodo['name'] == name:
            return index
    return None

# Retorna o nome pelo nome do arquivo
def get_name_by_filename(filename):
    for key, value in env_variables.items():
        if key == f"NODO_{filename.split('_')[1].split('.')[0]}_NAME":
            return value
    return None

# Retorna a url pelo nome do arquivo
def get_url_by_filename(filename):
    server_number = filename.split("_")[1].split(".")[0]
    for nodo in nodos:
        if nodo['name'] == server_number:
            return nodo['url']
    return None
