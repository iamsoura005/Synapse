#!/usr/bin/env python3
import httpx
import json
import sys

print('=' * 70)
print('🔍 EXTENDED API TEST SUITE (MUTATIONS & EDGE CASES)')
print('=' * 70)

BACKEND = 'http://127.0.0.1:8010'
failed = []
passed = 0

def test(name, method, endpoint, json_data=None, params=None, expected_status=200):
    global failed, passed
    try:
        url = f'{BACKEND}{endpoint}'
        if method == 'GET':
            r = httpx.get(url, params=params, timeout=10)
        elif method == 'POST':
            r = httpx.post(url, json=json_data, params=params, timeout=10)
        elif method == 'PUT':
            r = httpx.put(url, json=json_data, params=params, timeout=10)
        elif method == 'DELETE':
            r = httpx.delete(url, params=params, timeout=10)
        
        if r.status_code == expected_status:
            print(f'   ✓ {method} {endpoint} - Status {r.status_code}')
            passed += 1
            return r.json() if r.text else None
        else:
            print(f'   ✗ {method} {endpoint} - Expected {expected_status}, got {r.status_code}')
            print(f'      Response: {r.text[:200]}')
            failed.append(f'{method} {endpoint}')
            return None
    except Exception as e:
        print(f'   ✗ {method} {endpoint} - ERROR: {e}')
        failed.append(f'{method} {endpoint}')
        return None

# Test Relationship Endpoints
print('\n📝 RELATIONSHIP ENDPOINTS')
rel_result = test('Get Relationships', 'GET', '/api/v1/relationships', params={'user_id': 'demo-user'})
if rel_result and len(rel_result) > 0:
    rel_id = rel_result[0].get('id')
    test('Get Single Relationship', 'GET', f'/api/v1/relationships/{rel_id}', params={'user_id': 'demo-user'})
    test('Get Relationship Graph', 'GET', f'/api/v1/relationships/{rel_id}/graph', params={'user_id': 'demo-user'})
    test('Get Relationship Insights', 'GET', f'/api/v1/relationships/{rel_id}/insights', params={'user_id': 'demo-user'})

test('Create Relationship', 'POST', '/api/v1/relationships', 
     json_data={'user_id': 'demo-user', 'name': 'Test User', 'email': 'test@example.com'}, 
     expected_status=201)

# Test Negotiation Endpoints
print('\n📝 NEGOTIATION ENDPOINTS')
neg_result = test('Get Negotiations', 'GET', '/api/v1/negotiations', params={'user_id': 'demo-user'})
if neg_result and len(neg_result) > 0:
    neg_id = neg_result[0].get('id')
    test('Get Single Negotiation', 'GET', f'/api/v1/negotiations/{neg_id}', params={'user_id': 'demo-user'})
    test('Get Negotiation Rounds', 'GET', f'/api/v1/negotiations/{neg_id}/rounds', params={'user_id': 'demo-user'})
    test('Approve Negotiation', 'POST', f'/api/v1/negotiations/{neg_id}/approve', params={'user_id': 'demo-user'})
    test('Modify Negotiation', 'POST', f'/api/v1/negotiations/{neg_id}/modify', 
         json_data={'terms': {'key': 'value'}}, params={'user_id': 'demo-user'})
    test('Override Negotiation', 'POST', f'/api/v1/negotiations/{neg_id}/override',
         json_data={'split': {'party1': 0.5, 'party2': 0.5}}, params={'user_id': 'demo-user'})
    test('Delay Negotiation', 'POST', f'/api/v1/negotiations/{neg_id}/delay',
         json_data={'days': 3}, params={'user_id': 'demo-user'})

test('Start Manual Negotiation', 'POST', '/api/v1/negotiations/manual',
     json_data={'negotiation_type': 'expense', 'urgency': 'medium', 'parties': ['demo-user', 'alex-chen']},
     params={'user_id': 'demo-user'}, expected_status=201)

# Test Contract Endpoints
print('\n📝 CONTRACT ENDPOINTS')
contract_result = test('Get Contracts', 'GET', '/api/v1/contracts', params={'user_id': 'demo-user'})
if contract_result and len(contract_result) > 0:
    contract_id = contract_result[0].get('id')
    test('Get Single Contract', 'GET', f'/api/v1/contracts/{contract_id}', params={'user_id': 'demo-user'})

test('Create Contract', 'POST', '/api/v1/contracts',
     json_data={
         'title': 'Test Contract',
         'parties': ['demo-user', 'alex-chen'],
         'terms': {'key': 'value'},
         'negotiation_id': 'test-neg-id'
     },
     params={'user_id': 'demo-user'}, expected_status=201)

# Test Integration Endpoints
print('\n📝 INTEGRATION ENDPOINTS')
test('Get Integration Status', 'GET', '/api/v1/integrations/status', params={'user_id': 'demo-user'})
test('Connect Integration', 'POST', '/api/v1/integrations/google_calendar/connect',
     params={'user_id': 'demo-user'}, expected_status=200)
test('Disconnect Integration', 'DELETE', '/api/v1/integrations/slack/disconnect',
     params={'user_id': 'demo-user'}, expected_status=200)

# Summary
print('\n' + '=' * 70)
print(f'✅ PASSED: {passed}')
print(f'❌ FAILED: {len(failed)}')
if failed:
    print('\nFailed endpoints:')
    for f in failed:
        print(f'   • {f}')
    sys.exit(1)
else:
    print('🎉 ALL EXTENDED TESTS PASSED!')
    print('=' * 70)
