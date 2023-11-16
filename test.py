import pymongo
import os


client = pymongo.MongoClient(os.environ.get("MONGODB_URI"))

print(client["anti-cheat"]["keys"].find_one({}))

client.close()