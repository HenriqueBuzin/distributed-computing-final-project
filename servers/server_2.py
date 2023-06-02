from messaging import get_port, receive, get_messages
from flask import Flask, request, jsonify
import asyncio
import os

app = Flask(__name__)

nome_arquivo = os.path.basename(__file__)
port = get_port(nome_arquivo)

@app.route('/send', methods=['POST'])
async def send():
    await send(request.form)

@app.route('/receive', methods=['POST'])
async def handle_receive():
    await receive(request.form)
    return jsonify({"message": "Mensagem recebida pelo servidor"})

@app.route('/messages', methods=['GET'])
async def messages():
    return get_messages()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run(port=port))
