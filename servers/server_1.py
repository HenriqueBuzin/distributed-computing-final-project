# Importa as bibliotecas necessárias
from messaging import get_port_by_filename, send, receive, get_messages, sequencer, broadcast, deliver
from flask import Flask, request, jsonify
from queue import Queue
import threading
import signal
import json
import time
import sys
import os

# Necessário para o Flask, biblioteca que cria o servidor
app = Flask(__name__)

# Pega o nome do arquivo, por exemplo server_X.py
filename = os.path.basename(__file__)

# Obter a porta correta que precisa executar pelo nome do arquivo
port = get_port_by_filename(filename)

# Rota /send do servidor no método POST
# Vai pegar as informações passadas e enviar para o send da bibilioteca
# E retornar uma mensagem de confirmação
@app.route('/send', methods=['POST'])
def send_message():
    send(request.json)
    return jsonify({"message": "Mensagem enviada pelo servidor"})

# Rota /receive do servidor no método POST
# Vai pegar as informações passadas e enviar para o receive da bibilioteca
# E retornar uma mensagem de confirmação
@app.route('/receive', methods=['POST'])
def handle_receive():
    receive(request.json)
    return jsonify({"message": "Mensagem recebida pelo servidor"})

# Rota /sequencer do servidor no método POST
# Vai pegar as informações passadas e enviar para o sequencer da bibilioteca
# E retornar uma mensagem de confirmação
@app.route("/sequencer", methods=["POST"])
def process_sequencer():
    sequencer(request.json)
    return jsonify({"message": "Mensagem recebida pelo servidor"})

# Rota /deliver do servidor no método POST
# Vai pegar as informações passadas e enviar para o deliver da bibilioteca
# E retornar uma mensagem de confirmação
@app.route("/deliver", methods=["POST"])
def process_deliver():
    deliver(request.json)
    return jsonify({"message": "Mensagem recebida pelo servidor"})

# Função chamda no browser para comunicação entre servidores
@app.route('/send/<destination>/<message>', methods=['GET'])
def send_message_to_server(destination, message):
    send({"destination": destination, "message": message})
    return jsonify({"message": "Mensagem enviada com sucesso para o servidor."})

# Função chamda no browser para comunicação para todos os servidores
@app.route('/broadcast/<message>', methods=['GET'])
def send_broadcast_to_servers(message):
    broadcast(message)
    return jsonify({"message": "Mensagem enviada com sucesso para os servidores."})

# Para testes, ver as mensagens no postman
@app.route('/messages', methods=['GET'])
def messages():
    return get_messages()

# Função para escrever as mensagens no .log
def log(message_queue, stop_event):

    # Cria o arquivo filename.log
    log_file = filename.replace(".py", ".log")

    # Verifica a existência do diretório ../logs e cria se não existir
    logs_dir = "../logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log_path = os.path.join(logs_dir, log_file)

    # Verifica se o arquivo de log existe
    if not os.path.isfile(log_path):
        # Cria o arquivo de log se não existir
        open(log_path, 'w').close()
    
    while not stop_event.is_set():
        messages = json.loads(get_messages())
        print(messages)
        with open(log_path, "w") as log_file:
            for message in messages:
                if "message" in message:
                    if "sender" in message:
                        log_message = f"sender: {message['sender']}, message: {message['message']}"
                    else:
                        log_message = f"message: {message['message']}"
                    
                    log_file.write(log_message + "\n")
            
        time.sleep(1)

# Para poder encerar o terminal
def handle_sigint(signal, frame):
    stop_event.set()
    sys.exit(0)

# Código que vai executar ao instanciar o servidor
if __name__ == '__main__':

    # Cria uma fila para armazenar as mensagens
    message_queue = Queue()

    # Cria um evento para sinalizar o encerramento da execução da função log()
    stop_event = threading.Event()

    # Registra o sinal de interrupção (Ctrl+C)
    signal.signal(signal.SIGINT, handle_sigint)

    # Inicia a função log em uma thread separada
    log_thread = threading.Thread(target=log, args=(message_queue, stop_event))
    log_thread.start()

    # Inicia o Flask na thread principal
    app.run(port=port)

    # Sinaliza o encerramento do log
    stop_event.set()

    # Aguarda a finalização da thread de log
    log_thread.join()
