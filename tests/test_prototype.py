import plexapi
import json

server = plexapi.Server('http://192.168.1.101', 32400)
library = server.library()
out = library.get_recently_added()
print out

