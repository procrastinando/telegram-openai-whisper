### Requirements:
* pip install deep-translator
* pip install pyttsx3
* sudo apt update && sudo apt install ffmpeg
* pip install setuptools-rust
* pip install git+https://github.com/openai/whisper.git
* sudo apt install espeak

### Hardware requirements:
Up to 5G of RAM will be used.
* Tiny and base models use 1G of VRAM
* small model: 2G VRAM
* medium model: 5G VRAM
* large model: 10G VRAM

### Setup:
* Create a telegram bot https://telegram.me/BotFather
* Insert the telegram bot token into "transcriber.py", in the line 367

### Commands menu usage:
* Source language: There are two options: automatic and english
* Target language: The translation language according to google translator
* Auto translation: Activated or deactivated
* Auto speech: When activated, the bot sends an audio of the transcription or translation
* Conversation mode: Select a chat_id where the bot will send the speech, this mode can be used to have a conversation with someone using the bot. Use this bot to get your ID: https://telegram.me/myidbot
* Model size: Select the model size according to your system hardware:

### Bot usage:
* The bot will transcribe voice messages, audio files or video files that are sent to it, for example a song or a video.
* The bot uses google translator, hence a maximum of 5000 characters can be translated at the same time, likewise, a maximum of 4096 characters can be send at the same time, by a single message; if the audio file is large, several messages will be sent.
* The bot can receibe requests from any user by default, to create a white list, add the user_id into "transcriber.py", in the line 365
