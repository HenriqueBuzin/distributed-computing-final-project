from p2p import p2p_start, send, broadcast, receive, deliver
import time

p2p_start('node-3', 2)

time.sleep(60)

print(receive())

print(deliver())