#!/usr/bin/env python3
import httpx
import json

BACKEND = 'http://127.0.0.1:8010'

# Check all endpoint return formats
endpoints = [
    ('/api/v1/relationships', 'user_id'),
    ('/api/v1/negotiations', 'user_id'),
    ('/api/v1/contracts', 'user_id'),
    ('/api/v1/integrations/status', 'user_id'),
]

for endpoint, param in endpoints:
    try:
        r = httpx.get(f'{BACKEND}{endpoint}', params={param: 'demo-user'}, timeout=10)
        d = r.json()
        print(f'{endpoint}:')
        print(f'  Type: {type(d).__name__}')
        if isinstance(d, dict):
            print(f'  Keys: {list(d.keys())}')
        else:
            print(f'  Length: {len(d)}')
        print()
    except Exception as e:
        print(f'{endpoint}: ERROR - {e}\n')
