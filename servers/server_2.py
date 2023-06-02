# Importa as bibliotecas necessárias
from messaging import get_port_by_filename, send, receive, get_messages, sequencer, broadcast
from flask import Flask, request, jsonify
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

# Função chamda no browser para comunicação entre servidores
@app.route('/send/<destination>/<message>', methods=['GET'])
def send_message_to_server(destination, message):
    send({"destination": destination, "message": message})
    return jsonify({"message": "Mensagem enviada com sucesso para o servidor."})

# Função chamda no browser para comunicação para todos os servidores
@app.route('/broadcast/<message>', methods=['GET'])
def send_broadcast_to_servers(message):
    broadcast({"message": message})
    return jsonify({"message": "Mensagem enviada com sucesso para os servidores."})

# Rota /messages do servidor no método GET
# Vai retornar as mensagens recebidas, uso para fins de teste
@app.route('/messages', methods=['GET'])
def messages():
    return get_messages()

# Necessário para o Flask criar o servidor na porta correta
if __name__ == '__main__':
    app.run(port=port)
