# pip install deep-translator
# pip install pyttsx3
# sudo apt update && sudo apt install ffmpeg
# pip install setuptools-rust
# pip install git+https://github.com/openai/whisper.git
# sudo apt install espeak

import whisper
from deep_translator import GoogleTranslator
import pyttsx3
import requests
import json
import time
import subprocess
import os

def read_msg(offset):
    data = {
        "offset": offset,
    }
    resp = requests.get(base_url+'/getUpdates', data=data)
    dataframe = resp.json()

    if dataframe["result"]:
        
        for i in dataframe["result"]:

            if "message" in i:
                user_id = i["message"]["from"]["id"]
                user_name = i["message"]["from"]["first_name"]
                try:
                    comando = [i["message"]["text"], "message"]
                except:
                    comando = ["file", "file"]
            
            elif "callback_query" in i:
                user_id = i["callback_query"]["from"]["id"]
                user_name = i["callback_query"]["from"]["first_name"]
                comando = [i["callback_query"]["data"], "callback_query"]
                
            if len(white_list) == 0 or user_id in white_list:
                print("****************************************************************************************************")
                print("PROCESSING REQUEST FROM: " + str(user_id) + " - " + user_name)

################ Open or create a database

                try: # open database, if it does not exist, use default settings
                    database = open("database.txt", "r")
                    db_settings = eval(database.readline())
                    database.close()
                except:
                    db_settings = {user_id: default_settings}
                
                try: # open user settings, if it does not exist, use default settings
                    settings = db_settings[user_id]
                    settings["first_name"] = user_name
                except:
                    settings = default_settings
                    db_settings[user_id] = settings
                    db_settings[user_id]["first_name"] = user_name

################ If the message contains an audio

                try:
                    if 'voice' in i["message"]:
                        resp_media = requests.get(base_url + '/getFile?file_id=' + i["message"]["voice"]["file_id"]) # https://api.telegram.org/bot<token>/getFile?file_id=<file_id>
                    elif 'audio' in i["message"]:
                        resp_media = requests.get(base_url + '/getFile?file_id=' + i["message"]["audio"]["file_id"])
                    elif 'video' in i["message"]:
                        resp_media = requests.get(base_url + '/getFile?file_id=' + i["message"]["video"]["file_id"])
                    elif 'document' in i["message"]:
                        resp_media = requests.get(base_url + '/getFile?file_id=' + i["message"]["document"]["file_id"])
                    result_transcription = transcribe(resp_media, db_settings[user_id])
                    with open('database.txt', 'w') as f:
                        f.write(str(db_settings))
                    print("TRANSCRIPTION: " + result_transcription["text"])
                    
                    if settings["/conversation_mode"] == "Deactivate":
                        if settings["/auto_trans"] == True:
                            message = result_transcription["text"]
                            send_message(user_id, message)
                            message = translate(result_transcription, db_settings[user_id])
                            send_message(user_id, message)
                        else:
                            message = result_transcription["text"]
                            send_message(user_id, message)
                        if settings["/auto_speech"] == True:
                            send_speech(message, db_settings[user_id], user_id)
                    else:
                        if settings["/auto_speech"] == True:
                            message = translate(result_transcription, db_settings[user_id])
                            send_speech(message, db_settings[user_id], db_settings[user_id]["/conversation_mode"])
                        else:
                            if settings["/auto_trans"] == True:
                                message = translate(result_transcription, db_settings[user_id])
                                send_message(db_settings[user_id]["/conversation_mode"], message)
                            else:
                                message = result_transcription["text"]
                                send_message(db_settings[user_id]["/conversation_mode"], message)

                    update_database(db_settings)
                    print("Job finished, db updated")

                except:
                    pass

################ Looking for callback query
                
                if comando[1] == "callback_query":
                    if comando[0] == "auto_trans":
                        settings["position"] = ""
                        if settings["/auto_trans"] == True:
                            settings["/auto_trans"] = False
                            send_message(user_id, "Auto translation deactivated")
                        else:
                            settings["/auto_trans"] = True
                            send_message(user_id, "Auto translation activated")
                            
                    elif comando[0] == "auto_speech":
                        settings["position"] = ""
                        if settings["/auto_speech"] == True:
                            settings["/auto_speech"] = False
                            send_message(user_id, "Auto speech deactivated")
                        else:
                            settings["/auto_speech"] = True
                            send_message(user_id, "Auto speech activated")

                    elif comando[0] == "source_lang":
                        settings["position"] = "/source_lang"
                        keyboard = [[{"text": "Automatic"}], [{"text": "english"}]]
                        send_keyboard(user_id, "Set a source language", keyboard)
                        
                    elif comando[0] == "target_lang":
                        settings["position"] = "/target_lang"
                        keyboard = []
                        for j in GoogleTranslator().get_supported_languages():
                            new = {"text": j}
                            keyboard.append([new])
                        send_keyboard(user_id, "Set a target language", keyboard)
                        
                    elif comando[0] == "voice":
                        settings["position"] = "/voice"
                        keyboard = []
                        for j in engine.getProperty('voices'):
                            new = {"text": j.name}
                            keyboard.append([new])
                        send_keyboard(user_id, "Set a voice", keyboard)

                    elif comando[0] == "model_size":
                        settings["position"] = "/model_size"
                        keyboard = [[{"text": "tiny"}], [{"text": "base"}], [{"text": "small"}], [{"text": "medium"}], [{"text": "large"}]]
                        send_keyboard(user_id, "Set a model size", keyboard)
                        settings["position"] = "/model_size"

                    elif comando[0] == "conversation_mode":
                        settings["position"] = "/conversation_mode"
                        keyboard = [[{"text": "Deactivated"}]]
                        for j in settings["list"]:
                            new = {"text": j}
                            keyboard.append([new])
                        send_keyboard(user_id, "Select a user", keyboard)

                    update_database(db_settings)
                    print("Callback query accepted, db updated")

################ If the message is a text

                elif comando[1] == "message":
                    if i["message"]["text"] == "/settings":
                        send_inline(user_id, "->               Settings               <-", generate_inline(user_id, db_settings))
                        settings["position"] = ""

                    elif i["message"]["text"] == "/start":
                        remove_keyboard(user_id, "Hello/hola/你好")
                        settings["position"] = ""

#################### if the message is a text after a callback query

                    elif settings["position"] != "":
                        if settings["position"] == "/source_lang":
                            if i["message"]["text"] == "english":
                                settings["/source_lang"] = 'en'
                                remove_keyboard(user_id, "Source language: english")
                                settings["position"] = ""
                            else:
                                settings["/source_lang"] = 'Automatic'
                                remove_keyboard(user_id, "Source language: Automatic")
                                settings["position"] = ""

                        elif settings["position"] == "/target_lang":
                            try:
                                abb = dic_abb[i["message"]["text"]]
                                settings["/target_lang"] = abb
                                remove_keyboard(user_id, "Target language: " + i["message"]["text"])
                                settings["position"] = ""
                            except:
                                remove_keyboard(user_id, "Language not found!")

                        elif settings["position"] == "/voice":
                            dic_voices = []
                            for j in engine.getProperty('voices'):
                                dic_voices.append(j.name)
                            try:
                                settings["/voice"] = dic_voices.index(i["message"]["text"])
                                remove_keyboard(user_id, "Voice: " + i["message"]["text"])
                                settings["position"] = ""
                            except:
                                remove_keyboard(user_id, "Voice not found!")
                        
                        elif settings["position"] == "/model_size":
                            dic_models = ["tiny", "base", "small", "medium", "large"]
                            try:
                                settings["/model_size"] = i["message"]["text"]
                                remove_keyboard(user_id, "Model: " + i["message"]["text"])
                                settings["position"] = ""
                            except:
                                remove_keyboard(user_id, "Model not found!")

                        elif settings["position"] == "/conversation_mode":
                            if i["message"]["text"] in settings["list"]:
                                pass
                            elif i["message"]["text"] == "Deactivated":
                                pass
                            else:
                                settings["list"].append(i["message"]["text"])

                            settings["/conversation_mode"] = i["message"]["text"]
                            settings["position"] = ""
                            remove_keyboard(user_id, "Updated!")

                        update_database(db_settings)
                        print("Command accepted, db updated")

################ request completed

                return dataframe["result"][-1]["update_id"] + 1
    else:
        return offset


def transcribe(resp_media, settings):
    dataframe_media = resp_media.json()
    url_media = 'https://api.telegram.org/file/bot' + token + '/' + dataframe_media['result']["file_path"] # https://api.telegram.org/file/bot<token>/<file_path>

    if settings["/source_lang"] == 'en' and settings["/model_size"] != "large":
        model = whisper.load_model(settings["/model_size"] + ".en")
    else:
        model = whisper.load_model(settings["/model_size"])

    result_transcription = model.transcribe(url_media)

    settings["requests"][len(settings["requests"])] = {}
    settings["requests"][len(settings["requests"])-1]["transcription"] = result_transcription["text"]
    settings["requests"][len(settings["requests"])-1]["source_lang"] = settings["/source_lang"]
    settings["requests"][len(settings["requests"])-1]["target_lang"] = settings["/target_lang"]
    settings["requests"][len(settings["requests"])-1]["auto_trans"] = settings["/auto_trans"]
    settings["requests"][len(settings["requests"])-1]["auto_speech"] = settings["/auto_speech"]
    settings["requests"][len(settings["requests"])-1]["conversation_mode"] = settings["/conversation_mode"]
    settings["requests"][len(settings["requests"])-1]["voice"] = settings["/voice"]
    settings["requests"][len(settings["requests"])-1]["model_size"] = settings["/model_size"]
    settings["requests"][len(settings["requests"])-1]["time"] = time.time()

    return result_transcription

def translate(result, settings):
    if result["language"] == settings["/target_lang"]:
        text = result["text"]
    
    else:
        try:
            text = ""
            parts = len(result["text"])/5000 # 5000 characters google translator limit
            part = 0
            while part < parts:
                text_trans = result["text"][part*5000:(part+1)*5000]
                text_trans = GoogleTranslator(source='auto', target=settings["/target_lang"]).translate(text_trans)
                text = text + text_trans
                part = part + 1
        except:
            text = result["text"]
    
    return text

def send_message(user, message):
    base_url_message = base_url + '/sendMessage'
    headers = {"Content-Type": "application/json"}

    parts = len(message)/4096 # 4096 characters send message limit
    part = 0
    while part < parts:
        data = {
            "chat_id": user,
            "text": message,
            }

        data = json.dumps(data)
        resp = requests.post(base_url_message, data=data, headers=headers)
        part = part + 1

def send_keyboard(user, text, keyboard):
    base_url_download = base_url + '/sendMessage'
    headers = {"Content-Type": "application/json"}
    data = {
        "chat_id": user,
        "text": text,
        "reply_markup": {
            "keyboard": keyboard,
            "resize_keyboard": True,
            "one_time_keyboard": True,
            }
        }
    data = json.dumps(data)
    resp = requests.post(base_url_download, data=data, headers=headers)

def remove_keyboard(user, text):
    base_url_download = base_url + '/sendMessage'
    headers = {"Content-Type": "application/json"}
    data = {
        "chat_id": user,
        "text": text,
        "reply_markup": {
            "remove_keyboard": True,
            }
        }
    data = json.dumps(data)
    resp = requests.post(base_url_download, data=data, headers=headers)

def send_inline(user, message, inline):
    base_url_download = base_url + '/sendMessage'
    headers = {"Content-Type": "application/json"}
    data = {
        "chat_id": user,
        "text": message,
        "reply_markup": {
            "inline_keyboard": inline,
            },
        }
    data = json.dumps(data)
    resp = requests.post(base_url_download, data=data, headers=headers)

def send_speech(text, settings, chat_id):
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[settings["/voice"]].id)
    engine.setProperty('rate', 150)

    characters = ['/', ':', '*', '?', '"', '<', '>', '|']
    speech_title = text[:25]
    for j in characters:
        speech_title = speech_title.replace(j, '')

    engine.save_to_file(text, speech_title + '__.mp3')
    engine.runAndWait()
    engine.stop()
    subprocess.call(["ffmpeg", "-i", speech_title + '__.mp3', "-b:a", "32k", speech_title + '_.mp3', "-loglevel", "quiet", "-y"])

    base_url_audio = base_url + '/sendAudio'
    audio = open(speech_title + '_.mp3', 'rb')
    if settings["/conversation_mode"] == "Deactivated":
        data = {
            "chat_id": chat_id,
            }
    else:
        data = {
            "chat_id": chat_id,
            "caption": settings["first_name"],
            }
    files = {
        "audio": audio
    }
    resp = requests.get(base_url_audio, data=data, files=files)
    audio.close()

    os.remove(speech_title + '__.mp3')
    os.remove(speech_title + '_.mp3')
    print("Speech sent!")

def set_commands():
    base_url_download = base_url + '/setMyCommands'
    headers = {"Content-Type": "application/json"}
    data = {
        "commands": [{"command": "/settings", "description": ""}, {"command": "/start", "description": "procrastinator.me"}],
        }
    data = json.dumps(data)
    resp = requests.post(base_url_download, data=data, headers=headers)

def generate_inline(user, db_settings):
    inline_array = [[{"text": "Source: ", "callback_data": "source_lang"}, {"text": "Target: ", "callback_data": "target_lang"}], [{"text": "Translate: ", "callback_data": "auto_trans"}, {"text": "Speech: ", "callback_data": "auto_speech"}], [{"text": "Conversation: ", "callback_data": "conversation_mode"}, {"text": "Model: ", "callback_data": "model_size"}], [{"text": "", "callback_data": "voice"}]]
    
    inline_array[0][0]["text"] = inline_array[0][0]["text"] + inverted_dic_abb[db_settings[user]["/source_lang"]]
    inline_array[0][1]["text"] = inline_array[0][1]["text"] + inverted_dic_abb[db_settings[user]["/target_lang"]]
    
    if db_settings[user]["/auto_trans"] == True:
        inline_array[1][0]["text"] = inline_array[1][0]["text"] + "Activated"
    else:
        inline_array[1][0]["text"] = inline_array[1][0]["text"] + "Deactivated"

    if db_settings[user]["/auto_speech"] == True:
        inline_array[1][1]["text"] = inline_array[1][1]["text"] + "Activated"
    else:
        inline_array[1][1]["text"] = inline_array[1][1]["text"] + "Deactivated"

    inline_array[2][0]["text"] = inline_array[2][0]["text"] + db_settings[user]["/conversation_mode"]
    inline_array[2][1]["text"] = inline_array[2][1]["text"] + db_settings[user]["/model_size"]

    dic_voices = []
    for j in engine.getProperty('voices'):
        dic_voices.append(j.name)
    inline_array[3][0]["text"] = inline_array[3][0]["text"] + dic_voices[db_settings[user]["/voice"]]

    return inline_array

def update_database(db_settings):
    with open('database.txt', 'w') as database:
        database.write(str(db_settings))

##################################################################################################################################

default_settings = {"first_name": "", "requests": {}, "/source_lang": "Automatic", "/target_lang": "en", "/auto_trans": True, "/conversation_mode": "Deactivate", "list": [], "/auto_speech": True, "/voice": 0, "/model_size": "medium", "position": ""}

white_list = []

token = 'xxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
base_url = 'https://api.telegram.org/bot' + token
offset = 0

dic_abb = GoogleTranslator().get_supported_languages(as_dict=True)
dic_abb["Automatic"] = "Automatic"
inverted_dic_abb = {}
for i in dic_abb:
    inverted_dic_abb[dic_abb[i]] = i

engine = pyttsx3.init()

set_commands()

while True:
    try:
        offset = read_msg(offset)
        time.sleep(0)
    except:
        time.sleep(10) # If network fails, wait 10 seconds and try again
