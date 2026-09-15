import {createHash,randomUUID} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync,renameSync,readdirSync,statSync,unlinkSync} from 'node:fs';
import {join} from 'node:path';
const TTL=24*60*60*1000;
export function cacheKey(input,model) {return createHash('sha256').update('essay-isolated-v3\n'+model+'\n'+JSON.stringify(input)).digest('hex');}
export function readGeneration(dir,key) {
 try {const data=JSON.parse(readFileSync(join(dir,key+'.json'),'utf8'));return Date.now()-data.saved_at<TTL?data.result:null;}catch{return null;}
}
export function saveGeneration(dir,key,result) {
 mkdirSync(dir,{recursive:true});
 const tmp=join(dir,randomUUID()+'.tmp');
 writeFileSync(tmp,JSON.stringify({saved_at:Date.now(),result}),{mode:0o600});
 renameSync(tmp,join(dir,key+'.json'));
 const files=readdirSync(dir).filter(n=>/^[a-f0-9]{64}\.json$/.test(n)).map(n=>({name:n,time:statSync(join(dir,n)).mtimeMs})).sort((a,b)=>b.time-a.time);
 for(const [i,f] of files.entries())if(i>=20 || Date.now()-f.time>TTL)unlinkSync(join(dir,f.name));
}
