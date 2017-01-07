#!venv/bin/python3
import sys
import requests
from bs4 import BeautifulSoup as bs

root = 'https://www.cambridgeshire.gov.uk'
NUM_PAGES = 5
POSTCODE = 'your_postcode'
OUTPUT = 'out.txt'

def all_childminders(max_pages=None):
    page = 1
    while True:
        try:
            links = scrape_search_page(page)
            for link in links:
                yield link
            page+=1
            if max_pages and page>max_pages:
                raise StopIteration
        except requests.HTTPError: #TODO be more specific
            raise StopIteration

def scrape_search_page(page):
    search = '/site/custom_scripts/fid/fid_results.aspx'
    payload = {'q': 'Registered+childminders',
                'p': POSTCODE,
                't': 1,
                'page': page,
                'age': 'earlyyears'}
    r = requests.get(root + search, params=payload)
    if r.status_code == 404:
        #TODO better error
        raise requests.HTTPError
    soup = bs(r.content, 'html.parser')
    schools = soup.find_all(attrs={'class': 'school-address'})
    links = []
    for school in schools:
        summary = {
                    'Name': school.h3.text.strip(),
                    'Approx. Location': school.p.text.strip(),
                    'Link': school.a.get('href'),
                    'Distance': school.next_sibling.next_sibling
                                        .text.replace('Childminder','')
                                        .strip('\r\t\n ()')
                    }
        links.append(summary)
    return links


def get_details(link):

    simple_labels = ('Alt Telephone:',
        'Email:',
        'Telephone:',
        'Type:',
        'Inspection:',
        'Age range:',
        'Ofsted URN:',
        'Address:',
        'Mobile number:'
        'Website:')
    details = {}
    detail_url = root+link
    r = requests.get(detail_url)
    if not r.status_code == 200:
        raise requests.HTTPError
    soup = bs(r.content, 'html.parser')

    labels = soup.find_all('p', {'class': 'fid_label'})
    for label in labels:
        label_text = label.text.strip()
        if label_text in simple_labels:
            details[label_text] = \
                label.next_sibling.next_sibling.text.strip().replace('\t','')

    details_block = soup.find(attrs={'class': 'school_left'})
    headings = details_block.find_all('h3')
    for heading in headings:
        details[heading.text.strip()] = \
            heading.next_sibling.next_sibling.text.strip().replace('\t', '')
    return details

def get_unique_keys(dict_list):
    keys = set({})
    for dictionary in dict_list:
        keys.update(dictionary.keys())
    return keys

def to_front(input_list, element):
    input_list.insert(0, input_list.pop(input_list.index(element)))

def main():
    minders = []
    for childminder in all_childminders(NUM_PAGES):
        print('Getting details for ' + childminder['Name'])
        details = get_details(childminder['Link'])
        childminder.update(details)
        minders.append(childminder)
    u_keys = list(get_unique_keys(minders))
    to_front(u_keys, 'Name')
    with open(OUTPUT, 'w') as f:
        for minder in minders:
            for key in u_keys:
                if key in minder:
                    f.write(minder[key]
                                .replace('\t', '')
                                .replace('\n', '')
                                .replace('\r', ''))
                else:
                    f.write('-')
                f.write('\t')
            f.write('\n')
    return minders

if __name__ == '__main__':
    main()
