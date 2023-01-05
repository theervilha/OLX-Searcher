import requests, json
import os
from dotenv import load_dotenv
load_dotenv()

class Telegram:
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    URL = f"https://api.telegram.org/bot{TOKEN}"
    send_message_url = f"{URL}/sendMessage"
    send_button_url = f"{URL}/replyInlineMarkup"

    def send_message(self, message, chat_id, buttons=[], **kwargs):
        data = {'text': message, 'chat_id': chat_id, "parse_mode": "HTML"}
        data.update(kwargs)
        
        if buttons:
            data['reply_markup'] = json.dumps({
                'keyboard': [
                    [
                        {'text': button} for button in buttons
                    ]
                ]
            })
        else:  
            data['reply_markup'] = json.dumps({
                'hide_keyboard': True
            })
            
        return requests.post(self.send_message_url, data=data)