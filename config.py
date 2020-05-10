from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["rideshare"]
places = open("AreaNameEnum.csv", "r")
areas = places.read()
areas = areas.split('\n')
for i in range(len(areas)):
    areas[i] = areas[i].split(',')
areas.pop(0)
areas.pop(-1)

ip_port = '127.0.0.1:5000'
