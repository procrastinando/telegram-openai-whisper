# pip install deep-translator
# pip install pyttsx3
# sudo apt update && sudo apt install ffmpeg
# pip install setuptools-rust
# pip install git+https://github.com/openai/whisper.git

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
            
            if len(white_list) == 0 or i["message"]["from"]["id"] in white_list:
                print("PROCESSING REQUEST FROM: " + str(i["message"]["from"]["id"]))

                try: # open database, if it does not exist, use default settings
                    database = open("database.txt")
                    db_settings = eval(database.readline())
                    database.close()
                except:
                    db_settings = {i["message"]["from"]["id"]: default_settings}
                
                try: # open user settings, if it does not exist, use default settings
                    settings = db_settings[i["message"]["from"]["id"]]
                except:
                    settings = default_settings
                    db_settings[i["message"]["from"]["id"]] = settings
                
                try:
                    if 'voice' in i["message"]:
                        resp_media = requests.get(base_url + '/getFile?file_id=' + i["message"]["voice"]["file_id"]) # https://api.telegram.org/bot<token>/getFile?file_id=<file_id>
                    if 'audio' in i["message"]:
                        resp_media = requests.get(base_url + '/getFile?file_id=' + i["message"]["audio"]["file_id"])

                    result_transcription = transcribe(resp_media, db_settings[i["message"]["from"]["id"]])
                    print("TRANSCRIPTION: " + result_transcription["text"])
                    
                    if settings["/auto_trans"] == True:
                        message = result_transcription["text"]
                        send_message(i["message"]["from"]["id"], message)
                        message = translate(result_transcription, db_settings[i["message"]["from"]["id"]])
                        send_message(i["message"]["from"]["id"], message)
                    else:
                        message = result_transcription["text"]
                        send_message(i["message"]["from"]["id"], message)

                    if settings["/auto_speech"] == True:
                        send_speech(i["message"]["from"]["id"], message, db_settings[i["message"]["from"]["id"]])

                except:
                    pass # No voice or audio was found

                if "text" in i["message"]:
                    if i["message"]["text"] in settings: # If is a command

                        if i["message"]["text"] == "/auto_trans":
                            settings["position"] = ""
                            if settings["/auto_trans"] == True:
                                settings["/auto_trans"] = False
                                send_message(i["message"]["from"]["id"], "Auto translation deactivated")
                            else:
                                settings["/auto_trans"] = True
                                send_message(i["message"]["from"]["id"], "Auto translation activated")
                                
                        elif i["message"]["text"] == "/auto_speech":
                            settings["position"] = ""
                            if settings["/auto_speech"] == True:
                                settings["/auto_speech"] = False
                                send_message(i["message"]["from"]["id"], "Auto speech deactivated")
                            else:
                                settings["/auto_speech"] = True
                                send_message(i["message"]["from"]["id"], "Auto speech activated")

                        elif i["message"]["text"] == "/source_lang":
                            settings["position"] = "/source_lang"
                            keyboard = [[{"text": "Automatic"}], [{"text": "English"}]]
                            send_keyboard(i["message"]["from"]["id"], "Set a source language", keyboard)
                            
                        elif i["message"]["text"] == "/target_lang":
                            settings["position"] = "/target_lang"
                            keyboard = []
                            for j in GoogleTranslator().get_supported_languages():
                                new = {"text": j}
                                keyboard.append([new])
                            send_keyboard(i["message"]["from"]["id"], "Set a source language", keyboard)
                            
                        elif i["message"]["text"] == "/voice":
                            settings["position"] = "/voice"
                            keyboard = []
                            for j in engine.getProperty('voices'):
                                new = {"text": j.name}
                                keyboard.append([new])
                            send_keyboard(i["message"]["from"]["id"], "Set a voice", keyboard)

                        elif i["message"]["text"] == "/model_size":
                            settings["position"] = "/model_size"
                            keyboard = [[{"text": "tiny"}], [{"text": "base"}], [{"text": "small"}], [{"text": "medium"}], [{"text": "large"}]]
                            send_keyboard(i["message"]["from"]["id"], "Set a model size", keyboard)
                            settings["position"] = "/model_size"

                        update_menu(i["message"]["from"]["id"], db_settings)

                    else:

                        if settings["position"] == "/source_lang":
                            if i["message"]["text"] == "english":
                                settings["/source_lang"] = 'en'
                                send_message(i["message"]["from"]["id"], "Source language: english")
                                settings["position"] = ""
                            else:
                                settings["/source_lang"] = 'auto'
                                send_message(i["message"]["from"]["id"], "Source language: Automatic")
                                settings["position"] = ""

                        elif settings["position"] == "/target_lang":
                            dic_abb = GoogleTranslator().get_supported_languages(as_dict=True)
                            try:
                                abb = dic_abb[i["message"]["text"]]
                                settings["/target_lang"] = abb
                                send_message(i["message"]["from"]["id"], "Target language: " + i["message"]["text"])
                                settings["position"] = ""
                            except:
                                send_message(i["message"]["from"]["id"], "Language not found!")

                        elif settings["position"] == "/voice":
                            dic_voices = []
                            for j in engine.getProperty('voices'):
                                dic_voices.append(j.name)
                            try:
                                settings["/voice"] = dic_voices.index(i["message"]["text"])
                                send_message(i["message"]["from"]["id"], "Voice: " + i["message"]["text"])
                                settings["position"] = ""
                            except:
                                send_message(i["message"]["from"]["id"], "Voice not found!")
                        
                        elif settings["position"] == "/model_size":
                            dic_models = ["tiny", "base", "small", "medium", "large"]
                            try:
                                settings["/model_size"] = i["message"]["text"]
                                send_message(i["message"]["from"]["id"], "Model: " + i["message"]["text"])
                                settings["position"] = ""
                            except:
                                send_message(i["message"]["from"]["id"], "Model not found!")

                        update_menu(i["message"]["from"]["id"], db_settings)
                        print("DATABASE UPDATED")

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

    return model.transcribe(url_media)

def translate(result, settings):
    if result["language"] == "zh":
        result["language"] = "zh-CN"

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

def send_speech(user, text, settings):
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[settings["/voice"]].id)
    engine.setProperty('rate', 150)
    speech_title = text[:25]
    engine.save_to_file(text, speech_title + '__.mp3')
    engine.runAndWait()
    engine.stop()

    subprocess.call(["ffmpeg", "-i", speech_title + '__.mp3', "-b:a", "32k", speech_title + '_.mp3', "-loglevel", "quiet", "-y"])

    base_url_audio = base_url + '/sendAudio'
    audio = open(speech_title + '_.mp3', 'rb')
    data = {
        "chat_id": user
        }
    files = {
        "audio": audio
    }
    resp = requests.get(base_url_audio, data=data, files=files)

    os.remove(speech_title + '__.mp3', speech_title + '_.mp3')

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

def update_menu(user, db_settings):
    commands_array = [{"command": "/source_lang", "description": "Automatic"}, {"command": "/target_lang", "description": ""}, {"command": "/auto_trans", "description": "Deactivated"}, {"command": "/auto_speech", "description": "Deactivated"}, {"command": "/voice", "description": ""}, {"command": "/model_size", "description": ""}]
    
    for j in dic_abb:
        if db_settings[user]["/source_lang"] == dic_abb[j]:
            commands_array[0]["description"] = j
            break
    for j in dic_abb:
        if db_settings[user]["/target_lang"] == dic_abb[j]:
            commands_array[1]["description"] = j
            break
    
    if db_settings[user]["/auto_trans"] == True:
        commands_array[2]["description"] = "Activated"
    if db_settings[user]["/auto_speech"] == True:
        commands_array[3]["description"] = "Activated"

    dic_voices = []
    for j in engine.getProperty('voices'):
        dic_voices.append(j.name)
    commands_array[4]["description"] = dic_voices[db_settings[user]["/voice"]]

    commands_array[5]["description"] = db_settings[user]["/model_size"]

    base_url_download = base_url + '/setMyCommands'
    headers = {"Content-Type": "application/json"}
    data = {
        "commands": commands_array,
        }
    data = json.dumps(data)
    resp = requests.post(base_url_download, data=data, headers=headers)
    
    with open('database.txt', 'w') as f:
        f.write(str(db_settings))

##################################################################################################################################

default_settings = {"/source_lang": "auto", "/target_lang": "en", "/auto_trans": True, "/auto_speech": True, "/voice": 0, "/model_size": "small", "position": ""}
white_list = []

token = '5613461586:AAGcER2cXarZ7yzulu0cZ8clrOG8Y4t_wSg'
base_url = 'https://api.telegram.org/bot' + token
offset = 0

dic_abb = GoogleTranslator().get_supported_languages(as_dict=True)
engine = pyttsx3.init()

while True:
    try:
        offset = read_msg(offset)
        time.sleep(0.5)
    except:
        time.sleep(10) # If network fails, wait 10 seconds and try again
