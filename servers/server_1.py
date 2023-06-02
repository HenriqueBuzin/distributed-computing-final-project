from messaging import get_port, send, receive, get_messages
from flask import Flask, request, jsonify
import asyncio
import os

app = Flask(__name__)

nome_arquivo = os.path.basename(__file__)
port = get_port(nome_arquivo)

@app.route('/send', methods=['POST'])
async def send_message():
    await send(request.json)
    return jsonify({"message": "Mensagem enviada pelo servidor"})

@app.route('/receive', methods=['POST'])
async def handle_receive():
    await receive(request.json)
    return jsonify({"message": "Mensagem recebida pelo servidor"})

@app.route('/messages', methods=['GET'])
async def messages():
    return await get_messages()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run(port=port))
