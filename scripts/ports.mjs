import net from 'node:net';

export function validPort(value) {
 const port=Number(value);
 if(!Number.isInteger(port)||port<1024||port>65535)throw new Error('APP_PORT must be an integer between 1024 and 65535.');
 return port;
}

export function portAvailable(port) {
 return new Promise(resolve=>{
  const probe=net.createServer();
  probe.once('error',()=>resolve(false));
  probe.listen(port,'127.0.0.1',()=>probe.close(()=>resolve(true)));
 });
}

export async function chooseAppPort(preferred, workspace, available=portAvailable, fetcher=fetch) {
 for(let port=validPort(preferred);port<=Math.min(Number(preferred)+10,65535);port++) {
  try {
   const response=await fetcher(`http://127.0.0.1:${port}/api/health/live`,{signal:AbortSignal.timeout(1500)});
   const body=await response.json();
   if(response.ok&&body.service==='lenny-growth-studio'&&body.workspace===workspace)return {port,reuse:true};
  } catch {}
  if(await available(port))return {port,reuse:false};
 }
 throw new Error('No free preview port found. Set APP_PORT to another local port.');
}
