from p2p import p2p_start, send, broadcast, receive, deliver
import time
import os

p2p_start('node-2', 2)

time.sleep(60)

def process_txt_file():
    file_name = os.path.splitext(__file__)[0] + ".txt"

    received_messages = receive()
    delivered_messages = deliver()

    formatted_messages = []

    for message in received_messages:
        sender = message["sender"]
        destination = message["destination"]
        text = message["message"]
        formatted_message = f"Mensagem recebida: Remetente: {sender}, Destinatário: {destination}, Mensagem: {text}\n"
        formatted_messages.append(formatted_message)

    for message in delivered_messages:
        sender = message["sender"]
        text = message["message"]
        formatted_message = f"Mensagem recebida: Remetente: {sender}, Mensagem: {text}\n"
        formatted_messages.append(formatted_message)

    with open(file_name, "w", encoding="utf-8") as output_file:
        output_file.writelines(formatted_messages)

process_txt_file()

print(deliver())
print(receive())
