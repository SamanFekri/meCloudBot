import telepot
import os
from telepot.loop import MessageLoop

from pymongo import MongoClient
import pprint
import json

# bot initial
token = '498968923:AAF2JRak8zPQDqbDRbIJHaYyFi0T5KlxZWw'
bot = telepot.Bot(token)

# mongo initial
client = MongoClient('localhost', 27017)
db = client.meCloud
users = db.users


def handle_message(msg):
    print("message:", msg)

    from_part = msg['from']
    chat_part = msg['chat']

    current_user = users.find_one({"_id": from_part['id']})
    if current_user is None:
        current_user = {"_id": from_part['id'], "from": from_part, 'nv': 0, 'na': 0, 'np': 0}
        users.insert_one(current_user)
        current_user = users.find_one({"_id": from_part['id']})
    pprint.pprint(current_user)

    if 'text' in msg:
        if msg['text'] == '/start':
            user_id = from_part['id']
            make_dir(user_id=str(user_id))

            tempFile = open(str(user_id) + '/info.sam', 'wb+')
            tempFile.write(bytes(json.dumps(current_user).encode('utf-8')))
            tempFile.close()

            resp = 'Hey ' + from_part['first_name'] + '!'
            bot.sendMessage(chat_part['id'], resp)

        # elif msg['text'] == '/list':
        #     if 'files' in current_user:
        #         if(current_user)
    else:
        send_as = None
        myFiles = None
        doc_part = None

        if 'files' in current_user:
            myFiles = current_user['files']

        if 'document' in msg:
            doc_part = msg['document']
            send_as = 'document'
        elif 'photo' in msg:
            doc_part = msg['photo'][1]
            doc_part['file_name'] = 'photo_' + str(current_user['np'])
            current_user['np'] += 1
            send_as = 'photo'
        elif 'video' in msg:
            doc_part = msg['video']
            doc_part['file_name'] = 'video_' + str(current_user['nv'])
            current_user['nv'] += 1
            send_as = 'video'
        elif 'audio' in msg:
            doc_part = msg['audio']
            doc_part['file_name'] = 'audio_' + str(current_user['na'])
            current_user['na'] += 1
            send_as = 'audio'
        else:
            bot.sendMessage(chat_part['id'], 'Unsupported type')
            return

        # todo: must use caption to re write names and path (path not supported yet)
        cur_file = {'send_as': send_as, 'path': '/'}
        cur_file.update(doc_part)

        if 'caption' in msg:
            msg['caption'] = msg['caption'].lower()
            if msg['caption'].startswith("path:"):
                temp = msg['caption'][5:]
                temp = temp.strip()
                temp = temp.replace("@", "_")

                if temp != "":
                    dirs = temp.split('/')
                    file_name = dirs[len(dirs) - 1]

                    # file name
                    if file_name != "":
                        cur_file['file_name'] = file_name

                    print(dirs)
                print(temp)

        if myFiles is None:
            myFiles = {}

        myFiles[str(cur_file['file_id'])] = cur_file
        current_user['files'] = myFiles
        users.update_one({'_id': current_user['_id']}, {"$set": current_user})

        resp = 'This file save as:\n'
        resp += 'File name: ' + cur_file['file_name'] + '\n'
        resp += 'File path: ' + cur_file['path']
        bot.sendMessage(chat_part['id'], resp)
        # print(document_part)
        # dest = str(from_part['id']) + "/"
        # # if 'caption' in msg:
        # #     dest += msg['caption']
        # #     make_dir(dest)
        # dest += "/" + document_part['file_name']
        # bot.download_file(document_part['file_id'], dest)
        #
        # fi = open(dest, 'rb+')
        # bot.sendDocument(chat_part['id'], fi)
        # fi.close()
        # os.remove(dest)


def start_bot():
    MessageLoop(bot, handle_message).run_forever()


def make_dir(user_id):
    if not os.path.exists(user_id):
        os.makedirs(user_id)


start_bot()
