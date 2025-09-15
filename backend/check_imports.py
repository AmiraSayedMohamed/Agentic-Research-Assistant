import traceback

print('Running backend import checks...')

try:
    import app
    print('import app: OK')
except Exception:
    print('import app: FAILED')
    traceback.print_exc()

modules = [
    ('fitz', 'PyMuPDF'),
    ('sentence_transformers', 'sentence-transformers'),
    ('faiss', 'faiss'),
    ('numpy', 'numpy'),
]

for mod, name in modules:
    try:
        __import__(mod)
        print(f'import {mod} (\"{name}\") OK')
    except Exception as e:
        print(f'import {mod} (\"{name}\") FAILED: {e}')
