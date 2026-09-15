"""Create a source-only handoff without credentials, model weights or runtime data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib

root = Path(__file__).resolve().parents[1]
output = root / 'deliverables'
output.mkdir(exist_ok=True)
archive = output / 'Lenny-Growth-Assistant-Source.zip'
folders = ['src','backend','agent','api','skills','scripts','tests','docs','agent-transcripts','public','.github']
root_files = ['README.md','START_HERE.md','PRD.md','design.md','architecture.md','package.json','package-lock.json','requirements.txt','pytest.ini','Dockerfile','render.Dockerfile','compose.yaml','render.yaml','vercel.json','start.ps1','tsconfig.json','vite.config.ts','vitest.config.ts','index.html','.env.example','.gitignore','.dockerignore']
files = [root / name for name in root_files]
for folder in folders:
    files.extend(p for p in (root / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.log'] and p.name not in ['probe-agent.py','generate-demo.py'])
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for file in sorted(set(files)):
        z.write(file, 'Lenny-Growth-Assistant/' + file.relative_to(root).as_posix())
with ZipFile(archive) as z:
    assert z.testzip() is None
    assert not any('/.env' in n and not n.endswith('/.env.example') for n in z.namelist())
    count = len(z.namelist())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(archive.with_suffix('.sha256')).write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
print(f'{archive}\n{count} files; {archive.stat().st_size:,} bytes; SHA-256 {digest}')
