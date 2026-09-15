import http from 'node:http';
import { loadEnvFile } from 'node:process';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import { ModelRuntime, createAgentSession, DefaultResourceLoader, SessionManager, SettingsManager } from '@earendil-works/pi-coding-agent';
import {cacheKey,readGeneration,saveGeneration} from './cache.mjs';
import { composeEssay } from './essay.mjs';
import { systemPrompt, buildPrompt, stripFence } from './prompts.mjs';
try { loadEnvFile('.env'); } catch {}
process.env.PI_OFFLINE = '1';
process.env.PI_TELEMETRY = '0';
const agentDir = resolve('.runtime/pi');
mkdirSync(agentDir, { recursive:true });
const registry = await ModelRuntime.create({authPath:resolve(agentDir,'auth.json'),modelsPath:null,refreshOnCreate:false});
await registry.setRuntimeApiKey('ollama', 'ollama');
if (process.env.ANTHROPIC_API_KEY) await registry.setRuntimeApiKey('anthropic', process.env.ANTHROPIC_API_KEY);
const localModel = process.env.OLLAMA_MODEL || 'qwen2.5:3b';
registry.registerProvider('ollama', {
 baseUrl:(process.env.OLLAMA_BASE_URL || 'http://127.0.0.1:11434')+'/v1',
 api:'openai-completions', apiKey:'ollama',
 models:[{id:localModel,name:localModel,reasoning:false,input:['text'],
  cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:8192,maxTokens:2600,
  compat:{supportsDeveloperRole:false,supportsReasoningEffort:false,supportsStore:false,maxTokensField:'max_tokens'}}]
});
let busy = false;
function send(res, status, data) {
 res.writeHead(status, {'Content-Type':'application/json'}); res.end(JSON.stringify(data));
}
async function run(input) {
 const started = performance.now();
 const modelId = input.provider === 'ollama' ? localModel : (process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5');
 const model = registry.getModel(input.provider, modelId);
 if (!model) throw Object.assign(new Error('The configured model was not found. Check the model name in .env.'), {code:'model_not_found'});
 const settingsManager = SettingsManager.inMemory({compaction:{enabled:false},retry:{enabled:false}});
 const loader = new DefaultResourceLoader({
  cwd:agentDir,agentDir,settingsManager,noExtensions:true,noSkills:true,noPromptTemplates:true,noThemes:true,noContextFiles:true,
  systemPrompt:systemPrompt(input.mode),
 });
 await loader.reload();
 const {session} = await createAgentSession({
  cwd:agentDir,agentDir,modelRuntime:registry,model,thinkingLevel:'off',
  tools:[],noTools:'all',resourceLoader:loader,settingsManager,sessionManager:SessionManager.inMemory()
 });
 const stream = session.agent.streamFunction;
 session.agent.streamFunction = (model, context, options) => stream(model, context, {...options, temperature:0.2, maxTokens:input.mode==='ask'?700:input.mode==='essay'?650:1800});
 console.log(JSON.stringify({event:'generation_contract',system_prompt_configured:session.systemPrompt.includes('Cite'),mode:input.mode}));
 let activeSection = session;
 let timedOut = false;
 const timer = setTimeout(() => { timedOut=true; void activeSection.abort(); }, Number(process.env.MODEL_TIMEOUT_SECONDS || 1500)*1000);
 try {
  if (input.mode==='essay') {
   const content=await composeEssay(async (prompt)=>{
    const fresh=await createAgentSession({cwd:agentDir,agentDir,modelRuntime:registry,model,thinkingLevel:'off',tools:[],noTools:'all',resourceLoader:loader,settingsManager,sessionManager:SessionManager.inMemory()});
    activeSection=fresh.session;
    const sectionStream=activeSection.agent.streamFunction;
    activeSection.agent.streamFunction=(model,context,options)=>sectionStream(model,context,{...options,temperature:0.2,maxTokens:650});
    try {
     if(timedOut)throw new Error('Generation deadline exceeded.');
     await activeSection.prompt(prompt,{expandPromptTemplates:false});
     const last=activeSection.messages.filter(m=>m.role==='assistant').at(-1);
     if(!last || ['error','aborted'].includes(last.stopReason))throw new Error('Essay section generation failed.');
     return last.content.filter(c=>c.type==='text').map(c=>c.text).join('\n');
    } finally {activeSection.dispose();}
   },buildPrompt(input));
   return {content,model:modelId,duration_ms:Math.round(performance.now()-started)};
  }
  await session.prompt(buildPrompt(input), {expandPromptTemplates:false});
  let candidate = session.messages.filter(m=>m.role==='assistant').at(-1);
  let draft = candidate?.content.filter(c=>c.type==='text').map(c=>c.text).join('\n') || '';
  const labels = [...draft.matchAll(/\[S(\d+)\]/g)].map(m=>'S'+m[1]);
  const valid = new Set(input.sources.map(s=>s.label));
  const needsCitations = !labels.length || labels.some(s=>!valid.has(s));
  if (!timedOut && candidate?.stopReason!=='error' && needsCitations) {
   await session.prompt('Revise the entire previous response. Add the exact supplied [S#] citations after each factual paragraph. Remove unsupported claims. Return only the complete corrected response.', {expandPromptTemplates:false});
  }
  const messages = session.messages.filter(m => m.role==='assistant');
  const last = messages.at(-1);
  if (timedOut) throw Object.assign(new Error('The local model timed out. Try a shorter request or a smaller model.'), {code:'model_timeout'});
  if (!last || last.stopReason === 'error' || last.stopReason === 'aborted') throw new Error(last?.errorMessage || 'The model did not return an answer.');
  const content = stripFence(last.content.filter(c => c.type==='text').map(c => c.text).join('\n'));
  if (!content) throw new Error('The model returned an empty answer.');
  return {content,model:modelId,duration_ms:Math.round(performance.now()-started)};
 } catch(error) {
  if(timedOut)throw Object.assign(new Error('The local model timed out. Try a shorter request or a smaller model.'),{code:'model_timeout'});
  throw error;
 } finally { clearTimeout(timer); session.dispose(); }
}
const server = http.createServer(async (req,res) => {
 if (req.method==='GET' && req.url==='/health') return send(res,200,{status:'ok',engine:'Pi Coding Agent',busy});
 if (req.method!=='POST' || req.url!=='/generate') return send(res,404,{message:'Not found'});
 if (req.headers.authorization !== 'Bearer '+(process.env.AGENT_TOKEN || 'local-development-only')) return send(res,401,{code:'unauthorized',message:'Invalid agent credential.'});
 if (busy) return send(res,429,{code:'model_busy',message:'The model is working on another request. Try again shortly.'});
 let body='';
 let acquired=false;
 try {
  for await (const chunk of req) {
   body+=chunk;
   if (body.length>150000) return send(res,413,{code:'request_too_large',message:'Request is too large.'});
  }
  const input=JSON.parse(body);
  if (!['ollama','anthropic'].includes(input.provider) || !['ask','essay','markdown','html'].includes(input.mode) ||
      typeof input.prompt!=='string' || input.prompt.length>8000 || !Array.isArray(input.sources) || input.sources.length>8 ||
      !Array.isArray(input.history)) return send(res,400,{code:'invalid_request',message:'Invalid generation request.'});
  if (input.provider==='anthropic' && !process.env.ANTHROPIC_API_KEY) return send(res,503,{code:'missing_key',message:'Configure ANTHROPIC_API_KEY or select Ollama.'});
  if (busy) return send(res,429,{code:"model_busy",message:"The model is working on another request. Try again shortly."});
  busy=true; acquired=true;
  const key=cacheKey(input,input.provider==='ollama'?localModel:process.env.ANTHROPIC_MODEL);
  const cacheDir=resolve('.runtime/generations');
  let result=readGeneration(cacheDir,key);
  if(!result){result=await run(input);try{const labels=[...result.content.matchAll(/\[S(\d+)\]/g)].map(m=>'S'+m[1]);if(labels.length && labels.every(l=>input.sources.some(s=>s.label===l)))saveGeneration(cacheDir,key,result);}catch{console.error(JSON.stringify({event:'generation_cache_write_failed'}));}}
  else console.log(JSON.stringify({event:'generation_cache_hit'}));
  console.log(JSON.stringify({event:'generation_complete',provider:input.provider,mode:input.mode,duration_ms:result.duration_ms}));
  send(res,200,result);
 } catch (error) {
  console.error(JSON.stringify({event:'generation_failed',code:error.code || 'model_error',type:error.name}));
  send(res,error.code==='model_timeout'?504:503,{code:error.code || 'model_unavailable',
   message:error.code==='model_timeout'?error.message:'The model could not respond. Check that Ollama is running and the configured model is downloaded, or verify the cloud key.'});
 } finally { if (acquired) busy=false; }
});
server.listen(Number(process.env.AGENT_PORT || 8788), process.env.AGENT_HOST || '127.0.0.1', () => console.log('Pi agent listening on port '+(process.env.AGENT_PORT || 8788)));