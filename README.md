# Application
The server waiting to receive messages via send or broadcast, if received, will check if it meets the required requirements and persists.

## Start the servers
python server_1.py

## To send the client message
python client_1.py

## Messages between servers
In the browser, you can access the address of the node you want to send, for example http://localhost:8001 by adding /send/<destination>/<message> to the end, like /send/2/hi, to send the hello message from the node 1 for node 2.

## Messages to all servers
In the browser, you can access the address of the node you want to send, for example http://localhost:8001 by adding /broadcast/<message> to the end, like /broadcast/hello, to send the hi message to all servers.