from p2p import p2p_start, send, broadcast, receive, deliver
import time

p2p_start('node-1', 2)

send('node-2', 'mensagem 1')

# broadcast('Oi!')

time.sleep(60)

print(receive())

print(deliver())