#!/usr/bin/env python3
import httpx
import json
import sys

print('=' * 70)
print('🔍 COMPREHENSIVE API TEST SUITE')
print('=' * 70)

BACKEND = 'http://127.0.0.1:8010'
FRONTEND = 'http://127.0.0.1:3000'
failed = []

# Test 1: Backend Health
print('\n1️⃣  BACKEND HEALTH')
try:
    r = httpx.get(f'{BACKEND}/health', timeout=10)
    if r.status_code == 200:
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Response: {r.json()}')
    else:
        print(f'   ✗ FAILED: {r.status_code}')
        failed.append('Backend Health')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    failed.append('Backend Health')

# Test 2: API Docs
print('\n2️⃣  OPENAPI DOCS')
try:
    r = httpx.get(f'{BACKEND}/openapi.json', timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Endpoints: {len(data.get("paths", {}))}')
    else:
        print(f'   ✗ FAILED: {r.status_code}')
        failed.append('API Docs')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    failed.append('API Docs')

# Test 3: Relationships Endpoint
print('\n3️⃣  RELATIONSHIPS API')
try:
    r = httpx.get(f'{BACKEND}/api/v1/relationships?user_id=demo-user', timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Relationships: {len(data)} found')
    else:
        print(f'   ✗ FAILED: {r.status_code}')
        failed.append('Relationships API')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    failed.append('Relationships API')

# Test 4: Negotiations Endpoint
print('\n4️⃣  NEGOTIATIONS API')
try:
    r = httpx.get(f'{BACKEND}/api/v1/negotiations?user_id=demo-user', timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Negotiations: {len(data)} found')
    else:
        print(f'   ✗ FAILED: {r.status_code}')
        failed.append('Negotiations API')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    failed.append('Negotiations API')

# Test 5: Contracts Endpoint
print('\n5️⃣  CONTRACTS API')
try:
    r = httpx.get(f'{BACKEND}/api/v1/contracts?user_id=demo-user', timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Contracts: {len(data)} found')
    else:
        print(f'   ✗ FAILED: {r.status_code}')
        failed.append('Contracts API')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    failed.append('Contracts API')

# Test 6: Integrations Endpoint
print('\n6️⃣  INTEGRATIONS API')
try:
    r = httpx.get(f'{BACKEND}/api/v1/integrations/status?user_id=demo-user', timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Integrations: {data}')
    else:
        print(f'   ✗ FAILED: {r.status_code}')
        failed.append('Integrations API')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    failed.append('Integrations API')

# Test 7: Frontend Health
print('\n7️⃣  FRONTEND LOAD')
try:
    r = httpx.get(f'{FRONTEND}/', timeout=10)
    if r.status_code == 200 and '<html' in r.text.lower():
        print(f'   ✓ Status: {r.status_code}')
        print(f'   ✓ HTML returned')
    else:
        print(f'   ✗ FAILED: {r.status_code}')
        failed.append('Frontend Load')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    failed.append('Frontend Load')

# Summary
print('\n' + '=' * 70)
if failed:
    print(f'❌ FAILED TESTS: {len(failed)}')
    for f in failed:
        print(f'   • {f}')
    sys.exit(1)
else:
    print('✅ ALL TESTS PASSED')
    print('=' * 70)
