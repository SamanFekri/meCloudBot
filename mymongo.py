from pymongo import MongoClient
import pprint

client = MongoClient('localhost', 27017)
db = client.meCloud
collection = db.users

test_user = {'_id': 8, 'name': 'salam', 'state': '/',
             'files': {'43920': {'path': '/', 'file_name': 'salam.txt'}}}

# user = collection.replace_one({'_id': 5}, {"name": 'salam2'})
# pprint.pprint(user)

collection.insert_one(test_user)
client.close()
