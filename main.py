import telepot
import os
from telepot.loop import MessageLoop

token = '498968923:AAF2JRak8zPQDqbDRbIJHaYyFi0T5KlxZWw'
bot = telepot.Bot(token)

help_msg = '/search [name]\n/remove [file path]'


def handle_message(msg):
    print("message:", msg)

    from_part = msg['from']
    chat_part = msg['chat']

    if 'text' in msg:
        if msg['text'] == '/start':
            user_id = from_part['id']
            make_dir(user_id=str(user_id))

            resp = 'Hey ' + from_part['first_name'] + '!'
            bot.sendMessage(chat_part['id'], resp)
            bot.sendMessage(chat_part['id'], help_msg)
    else:
        if 'document' in msg:
            document_part = msg['document']
            print(document_part)
            dest = str(from_part['id']) + "/" + document_part['file_name']
            bot.download_file(document_part['file_id'], dest)


def start_bot():
    MessageLoop(bot, handle_message).run_forever()


def make_dir(user_id):
    if not os.path.exists(user_id):
        os.makedirs(user_id)


start_bot()
