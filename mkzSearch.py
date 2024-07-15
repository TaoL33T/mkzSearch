import argparse
import requests
from lxml import html
from html import unescape
import concurrent.futures
import time
from colorama import init, Fore, Style

# We need colors in terminal
init(autoreset=True)

class Scraper:
    def __init__(self, url, user_agent):
        self.url = url
        self.headers = {
            'User-Agent': user_agent
        }

    def fetch_page(self, url, session):
        """Extragem datele"""
        try:
            response = session.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.content
            else:
                print(f'Nu au putut fi extrase datele. Status: {response.status_code} pentru: {url}')
        except requests.RequestException as e:
            print(f'Eroare pentru {url}: {e}')
        return None

    def fetch_and_parse_detail(self, content, search_word, url, verbose=False):
        """Extrage detaliile și caută genul"""
        tree = html.fromstring(content)
        detail_div = tree.xpath('/html/body/div[1]/aside[1]/div[2]/div/div[8]/div[2]')
        if detail_div:
            inner_html = html.tostring(detail_div[0], encoding='unicode')
            decoded_html = unescape(inner_html)
            if search_word.lower() in decoded_html.lower():
                if verbose:
                    print(Fore.GREEN + f'Am găsit "{search_word}" aici: {url}')
                return (tree.xpath('//title/text()')[0].strip(), url)
        else:
            if verbose:
                print(f'Nu s-au găsit detalii pentru: {url}')
        return None, None

    def fetch_and_parse_anime(self, href, search_word, session, verbose=False):
        """Extrage detalii pentru fiecare anime."""
        content = self.fetch_page(href, session)
        if content:
            return self.fetch_and_parse_detail(content, search_word, href, verbose=verbose)
        return None, None

    def fetch_anime_list(self, genre, session, verbose=False):
        """Extrage link-urile și încă niște date"""
        content = self.fetch_page(self.url, session)
        if content:
            tree = html.fromstring(content)
            target_divs = tree.xpath('//div[@class="category-item"]')
            if target_divs:
                if not verbose:
                    print('Căutăm...')

                # SP33333333333D
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    futures = []
                    for div in target_divs:
                        a_tags = div.xpath('.//a')
                        for a in a_tags:
                            href = a.get('href')
                            futures.append(
                                executor.submit(self.fetch_and_parse_anime, href, genre, session, verbose)
                            )

                    results = []
                    for future in concurrent.futures.as_completed(futures):
                        result_name, result_link = future.result()
                        if result_name and result_link:
                            results.append((result_name, result_link))
                    return results
            else:
                if verbose:
                    print('N-am găsit niciun element. Probabil a fost schimbată pagina')
        else:
            if verbose:
                print(f'Nu am putut extrage datele de aici: {self.url}')
        return []

def main(args):
    start_time = time.time()

    scraper = Scraper(url='https://beta.manga-kids.com/proiecte-anime',
                      user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0')

    with requests.Session() as session:
        try:
            results = scraper.fetch_anime_list(args.genre, session, verbose=args.verbose)

            # Procesare rezultate
            print("\nRezultate:")
            for name, link in results:
                if name and link:
                    print(f'Nume: {name[:-35]} - Link: {link}')
                else:
                    print(f'Nu s-a găsit nimic pentru genul "{args.genre}".')

        except KeyboardInterrupt:
            print("\nCtrl+C...")

    end_time = time.time()
    print(f'\nTimp: {end_time - start_time:.2f} secunde')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Caută anime de pe MkZ după gen.')
    parser.add_argument('--genre', type=str, required=True, help='Genul de căutat')
    parser.add_argument('--verbose', action='store_true', help='Verbose')

    args = parser.parse_args()

    main(args)

