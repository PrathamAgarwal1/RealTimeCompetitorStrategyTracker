import json
import re
import traceback

try:
    with open('Apple iPhone 15 (128 GB) - Black - Price History.html', 'r', encoding='utf-8') as f:
        html = f.read()

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        pageProps = data.get('props', {}).get('pageProps', {})
        print('Available keys in pageProps:', list(pageProps.keys()))
        
        for key in pageProps.keys():
            if key not in ['ogProduct', 'product']:
                print(f'Type of {key}: {type(pageProps[key])}')
                if isinstance(pageProps[key], dict):
                    print(f'  Keys in {key}:', list(pageProps[key].keys()))
                elif isinstance(pageProps[key], list):
                    print(f'  List {key} length:', len(pageProps[key]))
                    if pageProps[key] and isinstance(pageProps[key][0], dict):
                        print(f'  Keys in {key}[0]:', list(pageProps[key][0].keys()))

        if 'product' in pageProps and isinstance(pageProps['product'], dict):
             print('Checking product dictionary more closely...')
             for k, v in pageProps['product'].items():
                 # print type and length if applicable
                 print(f'  {k}: {type(v)}')
    else:
        print('No __NEXT_DATA__ found')
except Exception as e:
    traceback.print_exc()
