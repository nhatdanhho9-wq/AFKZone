import os
token = os.environ.get('CASSO_WEBHOOK_TOKEN', '')
expected = 'nJJmwAm0BX43ybO6cszOz2itCCvxUE9M6t4WISqa8k4vl8VcLypqE3O1iAWWFQIB'
print(f"Token length: {len(token)}")
print(f"Expected length: {len(expected)}")
print(f"Match: {token == expected}")
print(f"Token stripped match: {token.strip() == expected}")
if token != expected:
    print(f"Token first 30: '{token[:30]}'")
    print(f"Expected first 30: '{expected[:30]}'")
