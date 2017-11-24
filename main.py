import telepot
import os
from telepot.loop import MessageLoop

from pymongo import MongoClient
import pprint
import json

import mimetypes
import requests

import _thread
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

        elif msg['text'] == '/whereami':
            resp = 'Your current directory is: <b>' + current_user['state'] + '</b>'
            bot.sendMessage(chat_part['id'], resp, parse_mode='html')

        elif msg['text'].startswith('/go@'):
            if current_user['state'] == '/':
                current_user['state'] = ''
            if len(msg['text'][4:]) > 0:
                if msg['text'][4:].startswith('/'):
                    current_user['state'] = msg['text'][4:]
                elif msg['text'][4:] == '~':
                    current_user['state'] = '/'
                else:
                    current_user['state'] += '/' + msg['text'][4:]

                if current_user['state'] != '/' and current_user['state'][-1] == '/':
                    current_user['state'] = current_user['state'][:-1]

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
            mfile_id = msg['text'][5:].upper()

            if 'files' in current_user:
                if mfile_id in current_user['files']:
                    tempFile = current_user['files'][mfile_id]
                    dest = str(current_user['_id'])
                    make_dir(dest)
                    dest += '/' + tempFile['file_name']
                    bot.download_file(tempFile['file_id'], dest)
                    fi = open(dest, 'rb+')

                    if tempFile['send_as'] == 'photo':
                        bot.sendPhoto(chat_part['id'], fi)
                    elif tempFile['send_as'] == 'audio':
                        bot.sendAudio(chat_part['id'], fi)
                    elif tempFile['send_as'] == 'video':
                        bot.sendVideo(chat_part['id'], fi)
                    else:
                        bot.sendDocument(chat_part['id'], fi)

                    fi.close()
                    os.remove(dest)

        elif msg['text'].startswith('/del@'):
            mfile_id = msg['text'][5:].upper()

            if 'files' in current_user:
                if mfile_id in current_user['files']:
                    resp = 'File: ' + current_user['files'][mfile_id]['file_name'] + ' deleted.\n'
                    resp += 'Path: <b>' + current_user['files'][mfile_id]['path'] + '</b>'
                    bot.sendMessage(chat_part['id'], resp, parse_mode='html')
                    del current_user['files'][mfile_id]
                    users.update_one({'_id': current_user['_id']}, {"$set": current_user})

        elif msg['text'].startswith('/change_name'):
            parts = msg['text'].split(' ')
            if len(parts) == 3:
                if 'files' in current_user:
                    parts[1] = parts[1].upper()
                    if parts[1] in current_user['files']:
                        mfile = current_user['files'][parts[1]]
                        mfile['file_name'] = parts[2]
                        users.update_one({'_id': current_user['_id']}, {"$set": current_user})
                        show_dirs(current_user=current_user, chat_part=chat_part)
            else:
                resp = 'invalid input\n'
                resp += '/change_name [file_id] [new_file_name]'
                bot.sendMessage(chat_part['id'], resp)

        elif msg['text'].startswith('/mov'):
            parts = msg['text'].split(' ')
            if len(parts) == 3:
                if 'files' in current_user:
                    parts[1] = parts[1].upper()
                    if parts[1] in current_user['files']:
                        mfile = current_user['files'][parts[1]]

                        path = parts[2]
                        if len(path) > 0:

                            if not path.startswith('/'):
                                if current_user['state'] == '/':
                                    path = '/' + path
                                else:
                                    path = current_user['state'] + '/' + path

                            if path != '/' and path[-1] == '/':
                                path = path[:-1]

                            mfile['path'] = path
                            users.update_one({'_id': current_user['_id']}, {"$set": current_user})

                            resp = 'This file moves to <b>' + mfile['path'] + '</b>.\n'
                            resp += 'File Info:\n'
                            resp += 'File name: <b>' + mfile['file_name'] + '</b>\n'
                            resp += 'File path: <b>' + mfile['path'] + '</b>\n'
                            resp += 'File ID: <b>' + 'SAMF' + str(current_user['count_file']) + '</b>'
                            bot.sendMessage(chat_part['id'], resp, parse_mode='html')
                            return
                        else:
                            resp = 'invalid input\n'
                            resp += '/mov [file_id] [new_file_path]'
                            bot.sendMessage(chat_part['id'], resp)
                            return
            else:
                resp = 'invalid input\n'
                resp += '/mov [file_id] [new_file_path]'
                bot.sendMessage(chat_part['id'], resp)

        elif msg['text'].startswith('/dl'):
            parts = msg['text'].split(' ')
            _thread.start_new_thread(dl_command, (parts, from_part, chat_part, current_user, ))

        elif msg['text'] == '/help':
            resp = '/start for start\n'
            resp += '/help for help\n'
            resp += '/list show list of files and directories in current directory\n'
            resp += '/whereami show current directory\n'
            resp += '/back return to parent directory\n'
            resp += '/go@[dir_name] change to that directory\n'
            resp += '/get@[file_id] return that file\n'
            resp += '/del@[file_id] remove that file\n'
            resp += '/change_name [file_id] [new_file_name]\n'
            resp += '/mov [file_id] [new_file_path]\n'
            resp += '/dl [file_url]. download that file in downloads folder\n'
            resp += 'send a document for adding document.\n'
            resp += 'use (<b>path:[file_path]/[file_name]</b>) in caption to path from <i>current location</i>.\n'
            resp += 'use (<b>path:/[file_path]/[file_name]</b>) in caption to path from <i>root</i>.\n'
            resp += 'in (video, audio, photo) adding name is important because telegram don\'t pass [file_name]'
            bot.sendMessage(chat_part['id'], resp, parse_mode='html')

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
                        cur_file['path'] = current_user['state'] + '/' + temp

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
        else:
            cur_file['path'] = current_user['state']

        if myFiles is None:
            myFiles = {}

        myFiles['SAMF' + str(current_user['count_file'])] = cur_file
        current_user['files'] = myFiles
        users.update_one({'_id': current_user['_id']}, {"$set": current_user})

        resp = 'This file save as:\n'
        resp += 'File name: <b>' + cur_file['file_name'] + '</b>\n'
        resp += 'File path: <b>' + cur_file['path'] + '</b>\n'
        resp += 'File ID: <b>' + 'SAMF' + str(current_user['count_file']) + '</b>'
        bot.sendMessage(chat_part['id'], resp, parse_mode='html')


def start_bot():
    MessageLoop(bot, handle_message).run_forever()


def make_dir(user_id):
    if not os.path.exists(user_id):
        os.makedirs(user_id)


def show_dirs(current_user, chat_part):
    resp = "Files in <b>" + current_user['state'] + "</b>:\n"
    if current_user['state'] != '/':
        resp += "/back \n"

    if 'files' in current_user:
        myFiles = current_user['files']
        dirs = set([])
        for key in myFiles:
            file = myFiles[key]
            if current_user['state'] == file['path']:
                resp += '<b>' + file['file_name'] + '</b>' \
                        + " <i>get: </i> /get@" + key \
                        + " <i>delete: </i>" + "/del@" + key + " \n"
            elif file['path'].startswith(current_user['state']):
                if current_user['state'] == '/':
                    next_dir = file['path'][len(current_user['state']):].split('/')[0]
                else:
                    next_dir = file['path'][len(current_user['state']) + 1:].split('/')[0]
                dirs.add(next_dir)

        for dir in dirs:
            resp += '<b>' + dir + '</b>' + " " + "/go@" + dir + " \n"

    bot.sendMessage(chat_part['id'], resp, parse_mode='html')


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


def download(url, file_name):
    # open in binary mode
    with open(file_name, "wb") as file:
        # get request
        response = requests.get(url)
        # write to file
        file.write(response.content)
        file.close()


def dl_command(parts, from_part, chat_part, current_user):
    if len(parts) == 2:
        try:
            url = parts[1]
            make_dir(str(from_part['id']))
            name = str(from_part['id']) + '/' + parts[1].split('/')[-1].replace(' ', '_')
            download(url, name)

            file = open(name, 'rb+')
            tempFile = bot.sendDocument(chat_part['id'], file)

            send_as = ''
            if 'document' in tempFile:
                send_as = 'document'
                tempFile = tempFile[send_as]
            elif 'photo' in tempFile:
                send_as = 'photo'
                tempFile = tempFile[send_as]
            elif 'video' in tempFile:
                send_as = 'video'
                tempFile = tempFile[send_as]
            elif 'audio' in tempFile:
                send_as = 'audio'
                tempFile = tempFile[send_as]

            file.close()

            os.remove(name)

            if 'files' not in current_user:
                current_user['files'] = {}

            current_user['count_file'] += 1
            tempFile['send_as'] = send_as
            tempFile['file_name'] = parts[1].split('/')[-1].replace(' ', '_')
            tempFile['path'] = '/downloads'
            current_user['files']['SAMF' + str(current_user['count_file'])] = tempFile

            users.update_one({'_id': current_user['_id']}, {"$set": current_user})

            resp = 'This file save as:\n'
            resp += 'File name: <b>' + tempFile['file_name'] + '</b>\n'
            resp += 'File path: <b>' + tempFile['path'] + '</b>\n'
            resp += 'File ID: <b>' + 'SAMF' + str(current_user['count_file']) + '</b>'
            bot.sendMessage(chat_part['id'], resp, parse_mode='html')

        except Exception as e:
            make_dir(str(from_part['id']))
            file = open(str(from_part['id']) + '/log.sam', 'wb+')
            file.write(bytes(str(e), 'utf-8'))
            file.close()

    else:
        resp = 'invalid input\n'
        resp += '/dl [file_url]'
        bot.sendMessage(chat_part['id'], resp)


start_bot()
