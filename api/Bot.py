from datetime import datetime
from .Telegram import Telegram

from .Database import Database
from .utils import find_url_in_text, is_olx_url

import requests
import os
APP_HOST = os.environ.get('APP_HOST')

class Bot:
    def __init__(self):
        self.DB = Database()
        self.T = Telegram()
        self.bot_responses = []
        self.context = ''
    
    def get_data_from_response(self, response):
        self.response = response
        self.chat_id = self.response['message']['chat']['id']
        self.created_at_user_message = datetime.now()
        self.get_user_message()

    def get_user_message(self):
        try:
            self.user_message = self.response['message']['text']
        except KeyError:
            self.user_message = ''
            self.context = ''
            print('erro ao pegar resposta')
            
    def get_bot_response(self):
        self.user_history = self.DB.get_messages_by_chat_id(self.chat_id)

        if self.user_history and self.user_history[-1]['context'] in ['ask_link_to_search_products', 'not_handled - not_found_link', 'not_handled - wrong_url', 'gived_up_to_search_products_in_link']:
            self.url = find_url_in_text(self.user_message)
            if self.url:            
                if is_olx_url(self.url):
                    self.context = 'confirm_search_link'
                    self.send_message(f'Você confirma que eu lhe envie os produtos postados diariamente do site {self.url}?', buttons=['Sim', 'Não'], disable_web_page_preview=True)
                else:
                    self.context = 'not_handled - wrong_url'
                    self.send_message('Parece que o link que você enviou não é do site da OLX.')
                    self.send_message('Faça assim: \n1. Entre no site da OLX: https://olx.com.br/\n2. Pesquise o produto\n3.Aplique os filtros do site, se você desejar.\n4. Lá em cima da janela do navegador, copie o link e me envie aqui. \n\nEstou aguardando! :D')

            else:
                self.context = 'not_handled - not_found_link'
                self.send_message('Parece que você não me enviou o link corretamente!')
                self.send_message('Faça assim: \n1. Entre no site da OLX: https://olx.com.br/\n2. Pesquise o produto\n3.Aplique os filtros do site, se você desejar.\n4. Lá em cima da janela do navegador, copie o link e me envie aqui. \n\nEstou aguardando! :D')
                
        elif self.user_history and self.user_history[-1]['context'] == 'confirm_search_link':
            if self.user_message == 'Sim':
                print('context:',self.context)
                if self.context:
                    self.context = ''
                    requests.get(f'{APP_HOST}/api/search/insert_search?chat_id={self.chat_id}&url={self.url}')
                    self.send_message('Perfeito! Amanhã, cerca de 12h, estou lhe enviando os produtos')
            else:
                self.context = 'gived_up_to_search_products_in_link'
                self.send_message('Tudo bem. Se você ainda quiser prosseguir, siga as dicas:')
                self.send_message('1. Entre no site da OLX: https://olx.com.br/\n2. Pesquise o produto\n3.Aplique os filtros do site, se você desejar.\n4. Lá em cima da janela do navegador, copie o link e me envie aqui. \n\nEstou aguardando! :D')

        
        elif not self.user_history or 'buscar' in self.user_message or '/start' in self.user_message:
            self.send_message('Olá! Eu sou o OLX Searcher, minha função é buscar produtos da OLX baseado nas suas pesquisas e enviar para você todos os dias os novos produtos postados no site!')
            self.send_message('Para buscar produtos, me envie o link da pesquisa que você procura os produtos. \nExemplo: https://rn.olx.com.br/moveis?pe=300&ps=100&q=mesa')
            self.context = 'ask_link_to_search_products'
            
        elif self.user_message == '/cancelar':
            links = requests.get(f'{APP_HOST}/api/search/get_links_per_user?chat_id={self.chat_id}&url={self.url}').json()
            if links:
                self.send_message('Você tem as seguintes URLs cadastradas:')
                [self.send_message(i, '-', data['url']) for i, data in enumerate(links)]
            else:
                self.send_message('Você não tem URLs cadastradas :(')
        elif self.context == 'user_sent_photo':
            self.send_message('Desculpe, só sei ler textos')
            self.context = ''
        else:    
            self.send_message('Desculpe, não entendi.')
            
    def store_data(self):
        bot_responses_str = '\n\n\n'.join(self.bot_responses)
        self.DB.insert_messages((
            self.chat_id, self.context, self.user_message, bot_responses_str, self.created_at_user_message
        ))
        self.bot_responses = []
        
    def send_message(self, message, buttons=[], **kwargs):
        self.T.send_message(message, self.chat_id, buttons=buttons, **kwargs)
        self.bot_responses.append(message)
        