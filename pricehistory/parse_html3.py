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
        
        print('\n--- apiData check ---')
        if 'apiData' in pageProps:
            apiData = pageProps['apiData']
            print(f"Type: {type(apiData)}")
            if isinstance(apiData, dict):
                print(f"Keys: {list(apiData.keys())}")
                if 'history' in apiData:
                    print("Found history in apiData!")
                    print(f"Type of history: {type(apiData['history'])}")
                if 'data' in apiData:
                    print("Found data in apiData!")
                    print(f"Type of data: {type(apiData['data'])}")
                    if isinstance(apiData['data'], dict):
                        print(f"Keys in apiData['data']: {apiData['data'].keys()}")
                        
        print('\n--- ogProduct check ---')
        if 'ogProduct' in pageProps:
             ogProduct = pageProps['ogProduct']
             for k, v in ogProduct.items():
                 # print type and length if applicable
                 print(f"  {k}: {type(v)} (len: {len(v) if hasattr(v, '__len__') else 'N/A'})")

    else:
        print('No __NEXT_DATA__ found')
        
except Exception as e:
    traceback.print_exc()
