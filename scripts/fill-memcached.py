from pymemcache.client.base import Client
import time
import math

print("filling memcache")
servers = ("localhost", "11211")
mc = Client(servers)
rand = open("/dev/urandom", "rb")

interval = 3600
now = int(math.floor(time.time()))
for i in range(-50, 4):
    epoch = int((math.floor(now/interval)+i)*interval)
    key = "/nts/nts-keys/%s"%epoch
    print(key)  # FIXME Remove me
    mc.set(key, rand.read(16))
