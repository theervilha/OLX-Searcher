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
import re
import requests

APP_HOST = 'https://olx-seacher.vercel.app'
def send_message(message, chat_id, buttons='', disable_web_page_preview=''):
    return requests.get(f'''{APP_HOST}/api/send_message?message={message}&chat_id={chat_id}&buttons={buttons}&disable_web_page_preview={disable_web_page_preview}''')


class OLXSpider(scrapy.Spider):
    name = "products"
    headers= {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}

    product_l = ".sc-12rk7z2-1.huFwya"
    title_l = 'h2::text'
    img_l = 'img::attr(src)'
    price_l = '.sc-1kn4z61-1.dGMPPn span::text'
    date_l = '.sc-11h4wdr-0.javKJU::text'

    def __init__(self, data, **kwargs):
        self.data = data
    
    def start_requests(self):
        for row in self.data:
            chat_id, main_url, last_runned_date = row.values()
            last_runned_date = datetime.strptime(last_runned_date[:-4], '%Y-%m-%dT%H:%M:%S')
            
            for url in self.generate_next_pages_from_url(main_url):
                yield scrapy.Request(
                    url=url, callback=self.get_products_in_page, headers=self.headers,
                    meta={
                        'chat_id': chat_id,
                        'main_url': main_url,
                        'last_runned_date': last_runned_date
                    }
                )
                
    def get_products_in_page(self, response): 
        chat_id = response.meta.get('chat_id')
        main_url = response.meta.get('main_url')
        last_runned_date = response.meta.get('last_runned_date')
        
        for self.element in self.get_products(response):
            product_date = self.get_product_date()

            
            # If passed a limit date to get products, verify.
            if last_runned_date:
                if product_date <= last_runned_date:
                    return
                    
            yield {
                'chat_id': chat_id,
                'main_url': main_url,
                
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

    def generate_next_pages_from_url(self, url, num_pages=2):
        start_i = url.find('?')+1
        if "o=" not in url and start_i != '-1':
            return [f'{url[:start_i]}o={i}&{url[start_i:]}' for i in range(1, num_pages+1 )]
        elif "o=" not in url and start_i == '-1':
            return [f'{url}?o={i}' for i in range(1, num_pages+1 )]
        elif "o=" in url:
            return [re.sub('o=.*?&', f'o={i}&' , url, flags=re.DOTALL) for i in range(1, num_pages+1 )]

def get_products(links_per_user):
    
    items = []
    def collect_items(item, response, spider):
        items.append(item)
    
    crawler = Crawler(OLXSpider)
    crawler.signals.connect(collect_items, signals.item_scraped)
    
    process = CrawlerProcess()
    process.crawl(crawler, data=links_per_user)
    process.start()

    return items


###############################
# Main program       
###############################
import requests

def send_message(message, chat_id, buttons='', disable_web_page_preview=''):
    return requests.get(f'''https://olx-seacher.vercel.app/api/send_message?message={message}&chat_id={chat_id}&buttons={buttons}&disable_web_page_preview={disable_web_page_preview}''')

if __name__ == '__main__':
    links_per_user = requests.get(f'{APP_HOST}/api/search/get_links_per_user').json()
    print('links per user:',links_per_user)
    products = get_products(links_per_user)

    def get_products_associated(chat_id, url):
        return list(filter(
            lambda product: product['main_url'] == url and product['chat_id'] == chat_id,
            products
        ))

    data_by_chat_id = {}
    for row in links_per_user:
        url, chat_id = row['url'], row['chat_id']
        products_by_url = get_products_associated(chat_id, url)
        
        try:
            data_by_chat_id[chat_id].append({'url': url, 'products': products_by_url})
        except KeyError:
            data_by_chat_id[chat_id] = [{'url': url, 'products': products_by_url}]
            
        requests.get(f'{APP_HOST}/api/search/update_last_time_runned_link', params={'chat_id': chat_id, 'url': url})

    def send_products(data_by_chat_id):
        for chat_id, data in data_by_chat_id.items():
            send_message(f'Olá 😁!! Vou te passar as informações que consegui hoje:', chat_id)
            for row in data:
                url = row['url']
                products = row['products']
                                
                if products:
                    send_message(f'No link {url}, eu <b>extraí {len(products)}</b> novos produtos. Dá uma olhada 🤗:'.replace('&', '%26'), chat_id, disable_web_page_preview=True)
                    for i, product in enumerate(products):
                        product_price = f"R$ {product['price']}" if product['price'] > 0 else "Preço não informado"
                        send_message(f"""
                                {i+1}° - {product_price} - <a href="{product['product_link']}">{product['title']}</a>
                            """, 
                            chat_id,
                            disable_web_page_preview=True
                        )
                else:
                    send_message(f'Poxa 😕, <b>não encontrei</b> nenhuma novidade no link {url}'.replace('&', '%26'), chat_id, disable_web_page_preview=True)
                    
            send_message('Por hoje é só. Espero que esteja gostando que eu monitore os produtos para você todos os dias!', chat_id)
            send_message('Lembrando que se você não deseja mais receber mensagens como essa, digite /cancelar :)', chat_id)
            
            
    send_products(data_by_chat_id)