from messaging import send, broadcast

destination = "exemplo.com"
message = "Olá, mundo!"

send(destination, message)

broadcast(message)