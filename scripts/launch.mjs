import {loadEnvFile} from 'node:process';
import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,openSync,writeFileSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {chooseAppPort} from './ports.mjs';
try {loadEnvFile('.env');} catch {console.error('Copy .env.example to .env first.');process.exit(1);}
mkdirSync('.runtime',{recursive:true});
const python=process.platform==='win32'?resolve('.venv/Scripts/python.exe'):resolve('.venv/bin/python');
if (!existsSync(python)) throw new Error('Create .venv and install requirements.txt first. See README.md.');
const records=existsSync('.runtime/services.json')?JSON.parse(readFileSync('.runtime/services.json','utf8')):[];
async function reachable(url) {try{return (await fetch(url,{signal:AbortSignal.timeout(1500)})).ok;}catch{return false;}}
function start(name,file,args,extra={}) {
 const child=spawn(file,args,{cwd:process.cwd(),detached:true,windowsHide:true,
  env:{...process.env,...extra},stdio:['ignore',openSync('.runtime/'+name+'-out.log','a'),openSync('.runtime/'+name+'-error.log','a')]});
 child.unref(); records.push({name,pid:child.pid,started_at:new Date().toISOString()});
 writeFileSync('.runtime/services.json',JSON.stringify(records,null,2));
}
async function wait(url,name) {for(let i=0;i<40;i++){if(await reachable(url))return;await new Promise(r=>setTimeout(r,1000));}throw new Error(name+' did not start. Check .runtime/'+name+'-error.log');}
async function command(file,args) {
 const child=spawn(file,args,{stdio:'inherit',windowsHide:true});
 const code=await new Promise(r=>child.on('exit',r));
 if(code!==0)throw new Error(args.join(' ')+' failed with exit '+code);
}
async function databaseReady() {
 const probe=spawn(python,['-c','from backend.db import engine; from sqlalchemy import text; c=engine.connect(); c.execute(text("SELECT 1")); c.close()'],{stdio:'ignore',windowsHide:true});
 return await new Promise((resolve,reject)=>{probe.on('error',reject);probe.on('exit',code=>resolve(code===0));});
}
const localDB=process.env.DATABASE_URL?.includes('127.0.0.1:54329');
if(localDB) {
 // Check this database through SQLAlchemy; a failed query triggers portable startup.
 if(!await databaseReady()) {
  start('postgres',process.execPath,['scripts/local-postgres.mjs']);
  let ready=false;
  for(let i=0;i<10;i++){if(await databaseReady()){ready=true;break;}await new Promise(r=>setTimeout(r,1000));}
  if(!ready)throw new Error('PostgreSQL did not become ready. Check .runtime/postgres-error.log.');
 }
}
const ollamaURL=process.env.OLLAMA_BASE_URL||'http://127.0.0.1:11434';
if(!await reachable(ollamaURL+'/api/tags')) {
 const exe=process.platform==='win32'?resolve('.runtime/ollama/ollama.exe'):'ollama';
 if(process.platform==='win32'&&!existsSync(exe))await command(python,['scripts/download-ollama.py']);
 start('ollama',exe,['serve'],{OLLAMA_MODELS:resolve('.runtime/models'),OLLAMA_HOST:'127.0.0.1:11434',OLLAMA_CONTEXT_LENGTH:'8192',OLLAMA_NUM_PARALLEL:'1'});
 await wait(ollamaURL+'/api/tags','ollama');
}
const model=process.env.OLLAMA_MODEL||'qwen2.5:3b';
const tags=await (await fetch(ollamaURL+'/api/tags')).json();
if(!tags.models.some(m=>m.name===model)) {
 console.log('Downloading local model '+model+'; this may take several minutes.');
 const pull=await fetch(ollamaURL+'/api/pull',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model,stream:false})});
 if(!pull.ok)throw new Error('Ollama model download failed');
 const result=await pull.json();if(result.error)throw new Error(result.error);
}
if(!existsSync('data/transcripts/manifest.json'))await command(python,['scripts/fetch-transcripts.py']);
await command(python,['-m','backend.ingest']);
if(!await reachable('http://127.0.0.1:8788/health'))start('agent',process.execPath,['agent/server.mjs']);
await wait('http://127.0.0.1:8788/health','agent');
if(!existsSync('dist/index.html'))throw new Error('Run npm run build first.');
const workspace=createHash('sha256').update(resolve(process.cwd())).digest('hex').slice(0,16);
const chosen=await chooseAppPort(process.env.APP_PORT||8000,workspace);
const appURL=`http://127.0.0.1:${chosen.port}`;
if(!chosen.reuse)start('api',python,['-m','uvicorn','backend.main:app','--host','127.0.0.1','--port',String(chosen.port)]);
await wait(appURL+'/api/health/ready','api');
writeFileSync('.runtime/preview-url.txt',appURL+'\n');
console.log('\nLenny Growth Assistant is ready: '+appURL+'\nServices run in the background. Logs: .runtime/');
