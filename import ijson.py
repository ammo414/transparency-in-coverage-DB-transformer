import ijson
import os

dir = "/home/anmol/VSCodeProjects/coverage/2024-04-01_KFHP_NC-COMMERCIAL_in-network-rates.zip/"
filename = os.listdir(dir)[0]
jsonpath = os.path.join(dir, filename)
f = open(jsonpath)

i = 0
for x,y,z in ijson.parse(f):
    print([x,y,z])
    i += 1
    if i >= 40:
        break
    
