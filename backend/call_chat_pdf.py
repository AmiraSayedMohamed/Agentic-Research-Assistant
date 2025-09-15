import requests

url = 'http://127.0.0.1:8000/api/chat_pdf'
payload = {'question': 'Please summarize the most important contributions of the uploaded paper.'}
try:
    r = requests.post(url, json=payload, timeout=30)
    print('status', r.status_code)
    try:
        print(r.json())
    except Exception:
        print('text:', r.text)
except Exception as e:
    print('request failed:', e)
