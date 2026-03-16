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
        
        with open('pageProps_dump.json', 'w', encoding='utf-8') as out:
             json.dump(pageProps, out, indent=2)
        print('Dumped pageProps to pageProps_dump.json')

    else:
        print('No __NEXT_DATA__ found')
        
except Exception as e:
    traceback.print_exc()
