from p2p import p2p_start, send, broadcast, receive, deliver
import time
import os

p2p_start('node-2', 2)

#send('node-1', 'mensagem 1')

time.sleep(60)

def process_txt_file():
    # Obtém o nome do arquivo Python em execução
    file_name = os.path.splitext(__file__)[0] + ".txt"

    # Chama as funções receive() e deliver() para obter as listas de mensagens
    received_messages = receive()
    delivered_messages = deliver()

    # Cria uma lista para armazenar as mensagens formatadas
    formatted_messages = []

    # Formata as mensagens recebidas e adiciona na lista
    for message in received_messages:
        sender = message["sender"]
        destination = message["destination"]
        text = message["message"]
        formatted_message = f"Mensagem recebida: Remetente: {sender}, Destinatário: {destination}, Mensagem: {text}\n"
        formatted_messages.append(formatted_message)

    # Formata as mensagens entregues e adiciona na lista
    for message in delivered_messages:
        sender = message["sender"]
        text = message["message"]
        formatted_message = f"Mensagem recebida: Remetente: {sender}, Mensagem: {text}\n"
        formatted_messages.append(formatted_message)

    # Escreve as mensagens formatadas no arquivo de saída
    with open(file_name, "w", encoding="utf-8") as output_file:
        output_file.writelines(formatted_messages)

process_txt_file()

print(deliver())
print(receive())
