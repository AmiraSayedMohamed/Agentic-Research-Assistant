import requests, os, json

BACKEND = "http://127.0.0.1:8000"
UPLOAD = BACKEND + "/upload_pdf"

# pick a PDF from backend/uploads
u_dir = os.path.join(os.path.dirname(__file__), 'uploads')
files = [f for f in os.listdir(u_dir) if f.endswith('.pdf')]
if not files:
    print('No PDF files found in backend/uploads')
    raise SystemExit(1)

file_path = os.path.join(u_dir, files[0])
print('Using file:', file_path)

with open(file_path, 'rb') as fh:
    files_payload = {'file': (os.path.basename(file_path), fh, 'application/pdf')}
    data = {'query': 'What is the main contribution of the paper?', 'user_id': 'tester'}
    r = requests.post(UPLOAD, files=files_payload, data=data)
    print('status:', r.status_code)
    try:
        print('json:', json.dumps(r.json(), indent=2))
    except Exception:
        print('response text:', r.text)
