export type Source = {label:string;chunk_id:string;guest:string;title:string;url:string;youtube_url:string;timestamp:string;excerpt:string;score:number};
export type Message = {id:string;role:'user'|'assistant';content:string;sources?:Source[];mode?:string;provider?:string;model?:string;artifact_id?:string;warnings?:string[];word_count?:number;generation_ms?:number};
export type Artifact = {id:string;title:string;format:'markdown'|'html';content:string;sources:Source[];created_at:string};
export type Chat = {id:string;title:string;created_at:string;updated_at:string};
export type Detail = Chat & {messages:Message[];artifacts:Artifact[]};
export type Episode = {id:string;guest:string;title:string;url:string};
export type Status = {transcripts:number;chunks:number;database:boolean;agent:boolean;default_provider:string;providers:{id:string;label:string;model:string;available:boolean}[]};
let workspace = localStorage.getItem('lenny-workspace');
if (!workspace) { workspace=crypto.randomUUID(); localStorage.setItem('lenny-workspace',workspace); }
export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
 const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json','X-Workspace-ID':workspace!,...options.headers}});
 if (!response.ok) {
  const data=await response.json().catch(()=>null);
  throw new Error(data?.error?.message || 'The service is unavailable. Check the local services and try again.');
 }
 if (response.status===204) return undefined as T;
 return response.json();
}
export function safeUrl(url:string) {
 try { const u=new URL(url); return ['https:','http:'].includes(u.protocol) ? u.href : undefined; } catch { return undefined; }
}
