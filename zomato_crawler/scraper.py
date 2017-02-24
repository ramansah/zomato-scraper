import requests
import csv
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool

CITY = None
LIMIT = None
MAIN_URL = None
HEADERS = {
    'user-agent': 'Mozilla/5.0'
}
THREADS = 10

RESTAURANTS_PARSED = list()


def get_all_restaurants(prev_restaurants, page):
    if not prev_restaurants:
        prev_restaurants = list()
    rest = requests.get(MAIN_URL + str(page), headers=HEADERS, timeout=10)
    if rest.status_code == 200:
        soup = BeautifulSoup(rest.text, 'lxml')
        restaurant_list = soup.find_all('a', {'class': 'result-title'})
        restaurant_list = restaurant_list
        for restaurant in restaurant_list:
            prev_restaurants.append(restaurant.get('href'))
            if len(prev_restaurants) == LIMIT:
                break
        print('Got list of {} restaurants'.format(str(len(prev_restaurants))))
        if LIMIT > len(prev_restaurants):
            get_all_restaurants(prev_restaurants, page+1)
        return prev_restaurants


def parse_restaurant(url):
    rest = requests.get(url, headers=HEADERS, timeout=10)
    if rest.status_code == 200:
        soup = BeautifulSoup(rest.text, 'lxml')
        name = soup.find('h1', {'class': 'res-name'}).find('a').getText().strip()

        phones = soup.findAll('span', {'class': 'fontsize2 bold zgreen'})
        phones = ', '.join(map(lambda x: x.find('span').getText(), phones))

        address = soup.find('div', {'class': 'res-main-address'}).find('div').find('span').getText()

        cuisines = soup.find('div', {'class': 'res-info-cuisines clearfix'}).findAll('a', {'class': 'zred'})
        cuisines = ', '.join(map(lambda x: x.getText(), cuisines))

        cost = soup.find('div', {'class': 'res-info-detail'}).findAll('span')[2].getText()

        time = soup.find('div', {'class': 'res-info-timings'}).find('div', {'class': 'medium'}).getText()

        rest = dict(
            name=name,
            phone=phones,
            address=address,
            cuisines=cuisines,
            cost=cost,
            time=time.replace(u'\xa0', u' ')
        )

        RESTAURANTS_PARSED.append(rest)
        print('.', end='', flush=True)


if __name__ == '__main__':

    CITY = input('Enter city (e.g. pune) : ')
    LIMIT = int(input('Enter number of restaurants (e.g. 25) : '))
    MAIN_URL = 'https://www.zomato.com/{}/best-restaurants?page='.format(CITY)

    list_of_rest = get_all_restaurants(None, 1)

    print('Scraping restaurants ::: Number of dots represents restaurants scraped')

    pool = Pool(THREADS)
    pool.map(parse_restaurant, list_of_rest)
    pool.close()
    pool.join()

    file = open(CITY + '.csv', 'w+')
    csv_writer = csv.writer(file, delimiter=',', quotechar="\"", quoting=csv.QUOTE_ALL)
    for res in RESTAURANTS_PARSED:
        row = (res.get('name'), res.get('phone'), res.get('address'),
               res.get('cuisines'), res.get('cost'), res.get('time'))
        csv_writer.writerow(row)
    file.close()
