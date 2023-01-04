from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

def index(request):
    return HttpResponse('opa')

from .Bot import Bot
Bot = Bot()

@csrf_exempt
def handle_message(request):
    print('Recebeu')
    if request.method =='POST':
        print('Recebeu POST')
        response = json.loads(request.body)
        
        print('RESPOSTA:\n',response)
        Bot.get_data_from_response(response)
        Bot.get_bot_response()
        Bot.store_data()
        
        return JsonResponse({'status': 'true'})
    
    
from .Telegram import Telegram
T = Telegram()    

def send_message(request):
    message = request.GET.get("message", "")
    chat_id = request.GET.get("chat_id", "")
    buttons = request.GET.get("buttons", "").split(',')
    disable_web_page_preview = bool(request.GET.get("disable_web_page_preview", ""))
    T.send_message(message, chat_id, buttons=buttons, disable_web_page_preview=disable_web_page_preview)
    
    return JsonResponse({'status': 'true'})