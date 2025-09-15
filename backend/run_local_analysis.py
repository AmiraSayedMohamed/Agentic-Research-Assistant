import asyncio, traceback, os
from agents.pdf_upload_handler import PDFUploadHandler

u_dir = os.path.join(os.path.dirname(__file__), 'uploads')
files = [f for f in os.listdir(u_dir) if f.endswith('.pdf')]
if not files:
    print('No PDF files found')
    raise SystemExit(1)

file_path = os.path.join(u_dir, files[0])
print('Using file:', file_path)

with open(file_path, 'rb') as fh:
    file_content = fh.read()

async def main():
    handler = PDFUploadHandler(upload_dir=os.path.join(os.path.dirname(__file__), 'uploads'))
    try:
        res = await handler.handle_pdf_upload(file_content, os.path.basename(file_path), query='What is the main contribution?', user_id='tester')
        print('Result:', res)
    except Exception:
        traceback.print_exc()

asyncio.run(main())
