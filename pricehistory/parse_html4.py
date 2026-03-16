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
        
        apiData = pageProps.get('apiData', {})
        if apiData:
             print('Types in apiData:')
             for k, v in apiData.items():
                 print(f"  {k}: {type(v)} (len: {len(v) if hasattr(v, '__len__') else 'N/A'})")
                 
             if 'data' in apiData:
                 print("\nKeys in apiData['data']:")
                 for k, v in apiData['data'].items():
                     print(f"  {k}: {type(v)} (len: {len(v) if hasattr(v, '__len__') else 'N/A'})")

    else:
        print('No __NEXT_DATA__ found')
        
except Exception as e:
    traceback.print_exc()
