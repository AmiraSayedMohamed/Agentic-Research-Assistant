import urllib.request, sys

endpoints = [
    ('backend', 'http://127.0.0.1:8000/'),
    ('frontend', 'http://127.0.0.1:3000/')
]

for name, url in endpoints:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            body = r.read(800).decode('utf-8', errors='replace')
            print(f"{name} OK: status={r.status} body_snippet={body[:200]!r}")
    except Exception as e:
        print(f"{name} FAILED: {e}")
        sys.exit(1)
print('CHECK_COMPLETE')
