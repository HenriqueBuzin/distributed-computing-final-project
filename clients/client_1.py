# Importa a bibilioteca
from messaging import send, broadcast

# Define o destino pelo nome, no caso 1,2 ou 3
destination = "1"

# Define a mensagem
message = "Olá, mundo!"

# Chama o método send(destino, mensagem)
#send(destination, message)

# Chama o broadcast(mensagem)
broadcast(message)