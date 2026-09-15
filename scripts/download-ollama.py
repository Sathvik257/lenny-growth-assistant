"""Download only Ollama's executable and CPU runtime from the official release ZIP."""
import io, json, urllib.request, zipfile
from pathlib import Path

class RemoteZip(io.RawIOBase):
    def __init__(self, url):
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=60) as r:
            self.url = r.url
            self.length = int(r.headers['Content-Length'])
        self.pos = 0
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos+offset if whence == 1 else self.length+offset
        return self.pos
    def read(self, size=-1):
        if size < 0: size = self.length-self.pos
        if size == 0: return b''
        req = urllib.request.Request(self.url, headers={'Range':f'bytes={self.pos}-{self.pos+size-1}'})
        with urllib.request.urlopen(req, timeout=180) as r:
            if r.status != 206: raise RuntimeError('Server did not honor range request')
            data = r.read()
        self.pos += len(data)
        return data

url = 'https://github.com/ollama/ollama/releases/download/v0.34.0/ollama-windows-amd64.zip'
out = Path('.runtime/ollama')
out.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(RemoteZip(url)) as z:
    names = z.namelist()
    selected = [n for n in names if not n.endswith('/') and ('/' not in n or ('cuda' not in n.lower() and 'vulkan' not in n.lower() and 'mlx' not in n.lower()))]
    print('CPU runtime files:', selected, flush=True)
    for name in selected:
        dest = (out/name).resolve()
        if not dest.is_relative_to(out.resolve()): raise RuntimeError('Invalid archive path')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(z.read(name))
        print('Saved', name, flush=True)
