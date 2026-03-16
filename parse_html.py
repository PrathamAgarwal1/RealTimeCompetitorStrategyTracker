import json
import re

with open('scrapping/pricehistory/Apple iPhone 15 (128 GB) - Black - Price History.html', 'r', encoding='utf-8') as f:
    html = f.read()

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    print('Found __NEXT_DATA__')
    pageProps = data.get('props', {}).get('pageProps', {})
    print(list(pageProps.keys()))
    if 'ogProduct' in pageProps:
        print('Keys in ogProduct:', list(pageProps['ogProduct'].keys()))
        print('Is history in ogProduct?', 'history' in pageProps['ogProduct'])
    if 'product' in pageProps:
        print('Keys in product:', list(pageProps['product'].keys()))
        print('Is history in product?', 'history' in pageProps['product'])
else:
    print('No __NEXT_DATA__ found')
