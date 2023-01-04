from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .Database import Database

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


def get_links_per_user(request):
    DB = Database()
    chat_id = request.GET.get("chat_id", "")
    return JsonResponse(DB.get_links_per_user(chat_id=chat_id),  safe=False)

def insert_search(request):
    DB = Database()
    chat_id = request.GET.get("chat_id", "")
    url = request.GET.get("url", "")
    DB.insert_search(chat_id, url)
    return HttpResponse('Inserido!')

def update_last_time_runned_link(request):
    DB = Database()
    chat_id = request.GET.get("chat_id", "")
    url = request.GET.get("url", "")
    DB.update_last_time_runned_search(chat_id, url)
    return HttpResponse('Atualizado!')

def delete_search(request):
    DB = Database()
    chat_id = request.GET.get("chat_id", "")
    url = request.GET.get("url", "")
    DB.delete_search(chat_id, url)
    return HttpResponse('Deletado!')