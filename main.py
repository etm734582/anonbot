import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import json
from credits import maintoken
from settings import MAX_USERS_AMOUNT

vk_session = vk_api.VkApi(token = maintoken)
session_api = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

COMMAND_LIST = ["add_chat", "say", "anon", "help"]

def commandDetector(msg = None, command_list = None):
    ret = {"command": False, "args": None}

    if msg[0] == "/":
        msg = msg.replace("/", "")
        msg_words = msg.split(" ")
        command = msg_words[0]

        for com in command_list:
            if command == com:
                ret["command"] = com

        args = msg_words[1:len(msg_words)]
        ret["args"] = args

        return ret

    else:
        return ret

def send_to_chat(id = None, msg = None):
    vk_session.method("messages.send", {"chat_id": id, "message": msg, "random_id": 0})

def send_to_user(id = None, msg = None):
    vk_session.method("messages.send", {"user_id": id, "message": msg, "random_id": 0})

def send(id = None, msg = None):
    try:
        vk_session.method("messages.send", {"chat_id": id, "message": msg, "random_id": 0})
    except:
        vk_session.method("messages.send", {"user_id": id, "message": msg, "random_id": 0})

def help_cmd(id = None):
    send(id=id, msg="Список команд:\n"
                    " - /help - посмотреть список команд\n\n"
                    " - /say {сообщение} - отправляет сообщение от имени бота в чат из которого была вызвана эта команда\n\n"
                    " - /add_chat {ключ} - создаёт или меняет ключ для беседы, из которой была вызвана эта команда\n\n"
                    " - /anon {ключ беседы} {текст} - отправляет сообщение в чат с указанным ключом от имени бота (анонимное сообщение)")

def setkey_cmd(id=None, args=None):
    with open('chats_info.json', 'r') as file:
        jsons = json.load(file)
    if jsons["users_amount"] < MAX_USERS_AMOUNT:
        if not id in jsons["chats"].values():
            if len(args) == 1:
                key = args[0]
                jsons["chats"][key] = id
                jsons["users_amount"] += 1
                send_to_chat(id=id, msg=f"Для данной беседы установлен ключ - {key}")
            else:
                send_to_chat(id=id, msg="Ошибка. Вы указали неверные аргументы. Тут должен быть один аргумент - ключ беседы")
        else:
            if len(args) == 1:
                for i in jsons["chats"].keys():
                    if jsons["chats"][i] == id:
                        del jsons["chats"][i]
                        break

                key = args[0]
                jsons["chats"][key] = id
                send_to_chat(id=id, msg=f"Для данной беседы установлен ключ - {key}")
            else:
                send_to_chat(id=id, msg="Ошибка. Вы указали неверные аргументы. Тут должен быть один аргумент - ключ беседы")

        with open('chats_info.json', 'w') as file:
            json.dump(jsons, file, indent=3)
    else:
        send_to_chat(id=id, msg="Просим прощения, но уже зарегистрировано максимальное количество групп")

def say_cmd(id = None, args = None, isFromUser = None):
    if len(args) > 0:
        msg = " ".join(args)
        if isFromUser:
            send_to_user(id=id, msg=msg)
        else:
            send_to_chat(id=id, msg=msg)
    else:
        send(id=id, msg="Ошибка. Не указан аргумент")

def anon_cmd(senderid=None, args = None):
    if len(args) < 2:
        send(id=senderid, msg="Ошибка. Указаны неверные аргументы")
        return

    key = args[0]
    msg = args[1:]

    with open('chats_info.json', 'r') as file:
        jsons = json.load(file)
    if key in jsons["chats"].keys():
        id = jsons["chats"][key]
        msg = " ".join(msg)
        msgtosend = f"анон\n---------\n{msg}"

        send_to_chat(id=id, msg=msgtosend)
    else:
        send(id=senderid, msg=f"Несуществует беседы с ключом {key}")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            msg = event.text
            isFromUser = False
            if event.from_user:
                isFromUser = True
                id = event.user_id
            else:
                id = event.chat_id

            command = commandDetector(msg=msg, command_list=COMMAND_LIST)

            if command["command"] == "say":
                say_cmd(id=id, args=command["args"], isFromUser=isFromUser)

            elif command["command"] == "anon":
                anon_cmd(senderid=id, args=command["args"])

            elif command["command"] == "add_chat" and not isFromUser:
                setkey_cmd(id=id, args=command["args"])
            elif command["command"] == "help":
                help_cmd(id=id)

