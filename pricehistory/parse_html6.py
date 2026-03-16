import json

with open('pageProps_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def find_paths(obj, target_key, current_path=''):
    paths = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f'{current_path}.{k}' if current_path else k
            if k == target_key or target_key in str(k).lower():
                paths.append(new_path)
            paths.extend(find_paths(v, target_key, new_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f'{current_path}[{i}]'
            paths.extend(find_paths(item, target_key, new_path))
    return paths

print('Paths to "history":')
for path in find_paths(data, 'history')[:20]:
    print(path)

print('\nPaths to "price":')
for path in find_paths(data, 'price')[:20]:
    print(path)
