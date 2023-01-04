from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .Telegram import Telegram
T = Telegram()

# Create your views here.
def index(request):
    return HttpResponse('opa')

def send_message(request):
    message = request.GET.get("message", "")
    chat_id = request.GET.get("chat_id", "")
    buttons = request.GET.get("buttons", "").split(',')
    disable_web_page_preview = bool(request.GET.get("disable_web_page_preview", ""))
    T.send_message(message, chat_id, buttons=buttons, disable_web_page_preview=disable_web_page_preview)
    
    return JsonResponse({'status': 'true'})