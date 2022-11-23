### Requirements:
* pip install deep-translator
* pip install pyttsx3
* sudo apt update && sudo apt install ffmpeg
* pip install setuptools-rust
* pip install git+https://github.com/openai/whisper.git
* sudo apt install espeak

### Setup:
* Create a telegram bot
* Insert the telegram bot token into "transcriber.py", in the line 367

### Commands menu usage:
* Source language: There are two options: automatic and english
* Target language: The translation language according to google translator
* Auto translation: Activated or deactivated
* Auto speech: When activated, the bot sends an audio of the transcription or translation
* Conversation mode: Select a chat_id where the bot will send the speech, this mode can be used to have a conversation with someone using the bot
* Model size: Select the model size according to your system hardware:

### Hardware requirements:
A total ammount of 5G of RAM will be used.
* Tiny and base models use 1G of VRAM
* small model: 2G VRAM
* medium model: 5G VRAM
* large model: 10G VRAM
