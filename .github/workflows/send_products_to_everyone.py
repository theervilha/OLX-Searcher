###############################
# Scraper OLX
###############################
import scrapy
from scrapy import signals
from scrapy.crawler import Crawler, CrawlerProcess
from scrapy.exceptions import CloseSpider

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from datetime import datetime, timedelta
import time
import re

class OLXSpider(scrapy.Spider):
    name = "products"
    headers= {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}

    product_l = ".sc-12rk7z2-1.huFwya"
    title_l = 'h2::text'
    img_l = 'img::attr(src)'
    price_l = '.sc-1kn4z61-1.dGMPPn span::text'
    date_l = '.sc-11h4wdr-0.javKJU::text'

    def __init__(self, urls, **kwargs):
        self.urls = urls
        self.get_until_this_date = kwargs.get('get_until_this_date')
    
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.get_products_in_page, headers=self.headers)

    def get_products_in_page(self, response): 
        for self.element in self.get_products(response):
            product_date = self.get_product_date()

            # If passed a limit date to get products, verify.
            if self.get_until_this_date:
                if product_date <= self.get_until_this_date:
                    raise CloseSpider('All products were taken by the deadline.')

            yield {
                'product_link': self.element.css('::attr(href)').get(),
                'title': self.element.css(self.title_l).get(),
                'img': self.element.css(self.img_l).get(),
                'date': product_date,
                'price': self.get_product_price(),
            }
    
    def get_products(self, response):
        return response.css(self.product_l)

    def get_product_date(self):
        self.date = self.element.css(self.date_l).get()
        self.clean_date()
        return self.date

    def get_product_price(self):
        price = self.element.css(self.price_l).get()[3:].replace('.', '')
        return float(price) if price != '' else price

    def clean_date(self):
        date_str_from_brazil_to_usa = {
            "dez": "Dec",
            "nov": "Nov",
            "out": "Oct",
            "set": "Sep",
            "ago": "Aug",
            "jul": "Jul",
            "jun": "Jun",
            "mai": "May",
            "abr": "Apr",
            "mar": "Mar",
            "fev": "Feb",
            "jan": "Jan",
        }
        if "Hoje" in self.date:
            self.date = datetime.strptime(datetime.now().strftime('%d %b') + self.date[4:], '%d %b, %H:%M')
        elif "Ontem" in self.date:
            yesterday = datetime.now() - timedelta(1)
            self.date = datetime.strptime(yesterday.strftime('%d %b') + self.date[5:], '%d %b, %H:%M')
        else:
            for br_month, usa_month in date_str_from_brazil_to_usa.items():
                if br_month in self.date:
                    self.date = re.sub(br_month, usa_month, self.date)        
            self.date = datetime.strptime(self.date, '%d %b, %H:%M')



def generate_next_five_pages_from_url(url, num_pages=2):
    start_i = url.find('?')+1
    if "o=" not in url and start_i != '-1':
        return [f'{url[:start_i]}o={i}&{url[start_i:]}' for i in range(1, num_pages+1 )]
    elif "o=" not in url and start_i == '-1':
        return [f'{url}?o={i}' for i in range(1, num_pages+1 )]
    elif "o=" in url:
        return [re.sub('o=.*?&', f'o={i}&' , url, flags=re.DOTALL) for i in range(1, num_pages+1 )]

def get_products(url, **kwargs):
    urls = generate_next_five_pages_from_url(url)
    print('urls geradas:',urls)

    items = []
    def collect_items(item, response, spider):
        items.append(item)

    configure_logging()
    settings = get_project_settings()
    
    crawler = Crawler(OLXSpider)
    crawler.signals.connect(collect_items, signals.item_scraped)
    
    runner = CrawlerRunner(settings)
    runner.crawl(crawler, urls=urls,  **kwargs)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())
    reactor.run() 

    return items


###############################
# Main program       
###############################
import requests

def send_message(message, chat_id, buttons='', disable_web_page_preview=''):
  return requests.get(f'''https://olx-seacher.vercel.app/api/send_message?message={message}&chat_id={chat_id}&buttons={buttons}&disable_web_page_preview={disable_web_page_preview}''')

if __name__ == '__main__':
  print('Started action')
  
  message = 'teste'
  chat_id = 800673480
  qtd_products = 60
  url = "https://rn.olx.com.br/moveis?pe=300&ps=100&q=mesa"
  
  products = get_products(url)[:qtd_products]
  print('qtd products:',len(products))
  if products:
    send_message(f'Olá mais uma vez!! Hoje eu extraí {len(products)} novos produtos. Dá uma olhada:', chat_id)
    for i, product in enumerate(products):
      product_price = f"R$ {product['price']}" if product['price'] > 0 else "Preço não informado"
      send_message(f"""
          {i+1}° - {product_price} - <a href="{product['product_link']}">{product['title']}</a>
        """, 
        chat_id,
        disable_web_page_preview=True
      )
    send_message('Por hoje é só. Espero que esteja gostando de receber novos produtos diariamente!\n\nLembrando que se você não deseja mais receber mensagens como essa, digite /cancelar :)', chat_id)
  else:
    send_message('Poxa, eu não encontrei nenhuma novidade de ontem para hoje. Mas pode deixar que se eu encontrar alguma amanhã, eu lhe aviso!!', chat_id)
    send_message('Lembrando que se você não deseja mais receber mensagens como essa, digite /cancelar :)', chat_id)
    

  print('Finished action')