import pymongo
import os


client = pymongo.MongoClient("mongodb://admin:password@localhost:27017/")

print(client["anti-cheat"]["keys"].find_one({}))

client.close()