# distributed-computing-final-project
 Distributed Computing Final Project

## Enviar
Método: POST
URL: http://localhost:8001/send
JSON:
{
  "destination": "server-2",
  "message": "Olá, servidor 2222!"
}

## Receber
Método: GET
URL: http://localhost:8002/receive
JSON:
[
    {
        "server-2": "Olá, servidor 2!"
    }
]