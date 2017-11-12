import telepot
import os
from telepot.loop import MessageLoop

from pymongo import MongoClient
import pprint
import json

import mimetypes

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
        current_user = {"_id": from_part['id'], "from": from_part, 'nv': 0, 'na': 0, 'np': 0, 'state': '/',
                        'count_file': 0}
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

        elif msg['text'] == '/list':
            show_dirs(current_user=current_user, chat_part=chat_part)

        elif msg['text'].startswith('/go@'):
            if current_user['state'] == '/':
                current_user['state'] = ''

            if msg['text'][4:].startswith('/'):
                current_user['state'] = msg['text'][4:]
            elif msg['text'][4:] == '~':
                current_user['state'] = '/'
            else:
                current_user['state'] += '/' + msg['text'][4:]

            users.update_one({'_id': current_user['_id']}, {"$set": current_user})

            show_dirs(current_user=current_user, chat_part=chat_part)

        elif msg['text'] == '/back':
            temp = ''
            dirs = current_user['state'].split('/')
            if len(dirs) > 0:
                for i in range(0, len(dirs) - 1):
                    temp += dirs[i] + '/'

            if len(temp) > 1:
                temp = temp[0: (len(temp) - 1)]

            current_user['state'] = temp

            users.update_one({'_id': current_user['_id']}, {"$set": current_user})

            show_dirs(current_user=current_user, chat_part=chat_part)

        elif msg['text'].startswith('/get@'):
            mfile_id = msg['text'][5:]

            if 'files' in current_user:
                if mfile_id in current_user['files']:
                    tempFile = current_user['files'][mfile_id]
                    dest = str(current_user['_id'])
                    make_dir(dest)
                    dest += '/' + tempFile['file_name']
                    bot.download_file(tempFile['file_id'], dest)
                    fi = open(dest, 'rb+')
                    bot.sendDocument(chat_part['id'], fi)
                    fi.close()
                    os.remove(dest)

        elif msg['text'].startswith('/del@'):
            mfile_id = msg['text'][5:]

            if 'files' in current_user:
                if mfile_id in current_user['files']:
                    resp = 'File: ' + current_user['files'][mfile_id]['file_name'] + ' deleted.\n'
                    resp += 'Path: ' + current_user['files'][mfile_id]['path']
                    bot.sendMessage(chat_part['id'], resp)
                    del current_user['files'][mfile_id]
                    users.update_one({'_id': current_user['_id']}, {"$set": current_user})

        elif msg['text'].startswith('/change_name'):
            parts = msg['text'].split(' ')
            if len(parts) == 3:
                if 'files' in current_user:
                    if parts[1] in current_user['files']:
                        mfile = current_user['files'][parts[1]]
                        mfile['file_name'] = parts[2]
                        users.update_one({'_id': current_user['_id']}, {"$set": current_user})
                        show_dirs(current_user=current_user, chat_part=chat_part)
            else:
                resp = 'invalid input\n'
                resp += '/change [file_id] [new_file_name]'
                bot.sendMessage(chat_part['id'], resp)

        elif msg['text'] == '/help':
            resp = '/start for start\n'
            resp += '/help for help\n'
            resp += '/list show list of files and directories in current directory\n'
            resp += '/back return to parent directory\n'
            resp += '/go@[dir_name] change to that directory\n'
            resp += '/get@[file_id] return that file\n'
            resp += '/del@[file_id] remove that file\n'
            resp += '/change_name [file_id] [new_file_name]\n'
            resp += 'send a document add document.\n'
            resp += 'use (path:[file_path]/[file_name]) in caption\n'
            resp += 'to put it in specific path.\n'
            resp += 'in (video, audio, photo) adding name is important because telegram don\'t pass [file_name]'
            bot.sendMessage(chat_part['id'], resp)

    else:
        send_as = None
        myFiles = None
        doc_part = None

        if 'files' in current_user:
            myFiles = current_user['files']

        if 'document' in msg:
            doc_part = msg['document']
            send_as = 'document'
            current_user['count_file'] += 1
        elif 'photo' in msg:
            doc_part = msg['photo'][len(msg['photo']) - 1]
            ext = ''
            if 'mime_type' in doc_part:
                ext = get_extension(doc_part['mime_type'])
            else:
                ext = '.jpg'
            if ext is None:
                ext = ''
            doc_part['file_name'] = 'photo_' + str(current_user['np']) + ext
            current_user['np'] += 1
            send_as = 'photo'
            current_user['count_file'] += 1
        elif 'video' in msg:
            doc_part = msg['video']
            ext = ''
            if 'mime_type' in doc_part:
                ext = get_extension(doc_part['mime_type'])
            if ext is None:
                ext = ''
            doc_part['file_name'] = 'video_' + str(current_user['nv']) + ext
            current_user['nv'] += 1
            send_as = 'video'
            current_user['count_file'] += 1
        elif 'audio' in msg:
            doc_part = msg['audio']
            ext = ''
            if 'mime_type' in doc_part:
                ext = get_extension(doc_part['mime_type'])
            if ext is None:
                ext = ''
            doc_part['file_name'] = 'audio_' + str(current_user['na']) + ext
            current_user['na'] += 1
            send_as = 'audio'
            current_user['count_file'] += 1
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
                temp = temp.replace(" ", "_")

                if temp != "":
                    dirs = temp.split('/')
                    file_name = dirs[len(dirs) - 1]

                    if temp.startswith('/'):
                        cur_file['path'] = temp
                    else:
                        cur_file['path'] = '/' + temp

                    # file name
                    if file_name != "":
                        cur_file['file_name'] = file_name
                        cur_file['path'] = cur_file['path'][:len(cur_file['path']) - len(file_name) - 1]
                    else:
                        cur_file['path'] = cur_file['path'][:len(cur_file['path']) - 1]

                    if cur_file['path'] == '':
                        cur_file['path'] = '/'


                    print(dirs)
                print(temp)

        if myFiles is None:
            myFiles = {}

        myFiles['SAMF' + str(current_user['count_file'])] = cur_file
        current_user['files'] = myFiles
        users.update_one({'_id': current_user['_id']}, {"$set": current_user})

        resp = 'This file save as:\n'
        resp += 'File name: ' + cur_file['file_name'] + '\n'
        resp += 'File path: ' + cur_file['path']
        bot.sendMessage(chat_part['id'], resp)


def start_bot():
    MessageLoop(bot, handle_message).run_forever()


def make_dir(user_id):
    if not os.path.exists(user_id):
        os.makedirs(user_id)


def show_dirs(current_user, chat_part):
    resp = "Files in " + current_user['state'] + ":\n"
    if current_user['state'] != '/':
        resp += "/back \n"

    if 'files' in current_user:
        myFiles = current_user['files']
        dirs = set([])
        for key in myFiles:
            file = myFiles[key]
            if current_user['state'] == file['path']:
                resp += file['file_name'] + " get: " + "/get@" + key + " delete: " + "/del@" + key + " \n"
            elif file['path'].startswith(current_user['state']):
                if current_user['state'] == '/':
                    next_dir = file['path'][len(current_user['state']):].split('/')[0]
                else:
                    next_dir = file['path'][len(current_user['state']) + 1:].split('/')[0]
                dirs.add(next_dir)

        for dir in dirs:
            resp += dir + " " + "/go@" + dir + " \n"

        bot.sendMessage(chat_part['id'], resp)
    else:
        bot.sendMessage(chat_part['id'], resp)


def get_extension(mime_type):
    for i in range(len(mime_type)):
        temp = mimetypes.guess_all_extensions(mime_type[:len(mime_type) - i], False)
        print(temp)
        if temp != []:
            for t in temp:
                if t[-1] == mime_type[-1]:
                    return t
            return temp[0]
    return None


start_bot()
