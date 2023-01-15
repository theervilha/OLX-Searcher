from datetime import datetime
from .Telegram import Telegram

from .Database import Database
from .utils import find_url_in_text, is_olx_url, format_url_to_get_most_recent_products

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
        
        if not self.user_history or '/start' in self.user_message:
            self.send_message(f"Olá {self.response['message']['chat']['first_name']}! Eu sou o OLX Searcher. Minha função é monitorar e enviar para você, diariamente, os novos produtos postados na OLX!")
            self.send_message(
                'Para começar o monitoramento, me envie o link da pesquisa que você procura os produtos. \nExemplo: https://rn.olx.com.br/moveis?pe=400&ps=100&q=mesa\n\nEstou aguardando 😊', 
                buttons=['Como achar o link?'],
                disable_web_page_preview=True
            )
            self.context = 'ask_link_to_search_products'

        elif 'monitorar' in self.user_message.lower():
            self.send_message(
                'Opa!! Para começar o monitoramento, me envie o link da pesquisa que você procura os produtos. \nExemplo: https://rn.olx.com.br/moveis?pe=400&ps=100&q=mesa\n\nEstou aguardando 😊', 
                buttons=['Como achar o link?'],
                disable_web_page_preview=True
            )
            self.context = 'ask_link_to_search_products'
            
        elif self.user_message == 'Falar com o desenvolvedor':
            self.send_message(
                'E aí, tudo bem? <a href="https://api.whatsapp.com/send/?phone=+5584981480220&text=Olá, Ueniry! Estou entrando em contato com você através do chatbot OLX Searcher.">Clique aqui para conversar comigo</a>. Estou lhe esperando! 😁', 
                disable_web_page_preview=True
            )   
            self.context = ''
            
            
        elif self.user_message in ['/cancelar', 'Cancelar monitoramento']:
            links = requests.get(f'{APP_HOST}/api/search/get_links_per_user', params={'chat_id': self.chat_id}).json()
            if links:
                buttons = [data['url'] for data in links] + ["Não quero cancelar"]
                self.send_message(
                    'Você pode <b>cancelar o monitoramento</b> de um link clicando nos botões. Selecione qual dos links você deseja cancelar.',
                    buttons=buttons
                )
                self.context = 'want_cancel_url'
            else:
                self.send_message('Você ainda não cadastrou uma URL :(. Digite "Monitorar" que você pode cadastrar uma URL.')
            
        elif self.context == 'want_cancel_url':
            if self.user_message == "Não quero cancelar":
                self.send_message('Que bom!! Então é só aguardar que estarei sempre lhe enviando mais produtos :).')
            else:
                try:
                    requests.get(f'{APP_HOST}/api/search/delete_search', params={'chat_id': self.chat_id, 'url': self.user_message})
                    self.send_message(f'Cancelei o link {self.user_message}. Caso você queira adicionar outro, digite "Monitorar" 😉.', disable_web_page_preview=True)
                except:
                    self.send_message(f'Ocorreu um erro ao cancelar seu link. Por favor, <a href="https://api.whatsapp.com/send/?phone=+5584981480220&text=Olá, Ueniry! Estou entrando em contato com você através do chatbot OLX Searcher porque tive problemas ao cancelar um monitoramento.">clique aqui</a> para entrar em contato com o desenvolvedor.')
            self.context = ''
        
        elif self.user_history and self.user_history[-1]['context'] in ['ask_link_to_search_products', 'how_to_find_link', 'not_handled - not_found_link', 'not_handled - wrong_url', 'gived_up_to_search_products_in_link']:
            if self.user_message == 'Como achar o link?':
                self.send_message('Faça assim: \n1. Entre no site da OLX pelo navegador: https://olx.com.br/\n2. Pesquise o produto\n3.Aplique os filtros do site, se você desejar.\n4. Lá em cima, copie o endereço do link e me envie aqui. \n\nEstou aguardando! :D')
                self.context = 'how_to_find_link'
            else:    
                self.url = find_url_in_text(self.user_message)
                if self.url:            
                    if is_olx_url(self.url):
                        self.context = 'confirm_search_link'
                        self.send_message(f'Você confirma que eu lhe envie os novos produtos postados diariamente do site {self.url}?', buttons=['Sim', 'Não'], disable_web_page_preview=True)
                        self.url = format_url_to_get_most_recent_products(self.url)
                    else:
                        self.context = 'not_handled - wrong_url'
                        self.send_message('Parece que o link que você enviou não é do site da OLX.')
                        self.send_message('Faça assim: \n1. Entre no site da OLX pelo navegador: https://olx.com.br/\n2. Pesquise o produto\n3.Aplique os filtros do site, se você desejar.\n4. Lá em cima, copie o endereço do link e me envie aqui. \n\nEstou aguardando! :D')

                else:
                    self.context = 'not_handled - not_found_link'
                    self.send_message('Parece que você não me enviou o link corretamente!')
                    self.send_message('Faça assim: \n1. Entre no site da OLX pelo navegador: https://olx.com.br/\n2. Pesquise o produto\n3.Aplique os filtros do site, se você desejar.\n4. Lá em cima, copie o endereço do link e me envie aqui. \n\nEstou aguardando! :D')
                
        elif self.user_history and self.user_history[-1]['context'] == 'confirm_search_link':
            if self.user_message.lower() == 'sim':
                if self.context:
                    self.context = ''
                    requests.get(f'{APP_HOST}/api/search/insert_search', params={'chat_id': self.chat_id, 'url':self.url})
                    self.send_message('Perfeito! Todos os dias, por volta das 12h, estou lhe enviando os produtos. \n\nLembrando que se você quiser cancelar a qualquer momento, é só digitar /cancelar. \nE se você quiser monitorar outro link, digite /monitorar 😉')
            else:
                self.context = ''
                self.send_message('Tudo bem. Se você ainda quiser prosseguir, digite "Monitorar" nessa conversa e siga o passo a passo! 😉')

            
        elif self.context == 'user_sent_photo':
            self.send_message('Desculpe, só sei ler textos')
            self.context = ''
        else:    
            self.send_message('Desculpe, não entendi. Por favor, selecione nos botões o que você deseja fazer:', buttons=['Monitorar produtos', 'Cancelar monitoramento', 'Falar com o desenvolvedor'])
            
    def store_data(self):
        bot_responses_str = '\n\n\n'.join(self.bot_responses)
        self.DB.insert_messages((
            self.chat_id, self.context, self.user_message, bot_responses_str, self.created_at_user_message
        ))
        self.bot_responses = []
        
    def send_message(self, message, buttons=[], **kwargs):
        self.T.send_message(message, self.chat_id, buttons=buttons, **kwargs)
        self.bot_responses.append(message)
        