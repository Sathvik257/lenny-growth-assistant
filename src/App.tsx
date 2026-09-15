import {useEffect,useMemo,useRef,useState, type FormEvent, type ReactNode} from 'react';
import {ArrowUp, ArrowUpRight, AudioLines, BookOpen, Check, ChevronDown, ChevronRight, CircleHelp, Code2, Copy, Download, FileText, FolderOpen, Layers3, Library, Loader2, Menu, MessageSquare, PanelRightClose, PanelRightOpen, Plus, Search, Settings2, ShieldCheck, Sparkles, Trash2, X, Zap} from 'lucide-react';
import {api, safeUrl, type Artifact, type Chat, type Detail, type Episode, type Message, type Source, type Status} from './api';
import {safeArtifact} from './security';
import Markdown from './Markdown';

type Mode='auto'|'ask'|'essay'|'markdown'|'html';
const modes:{id:Mode;label:string;icon:typeof MessageSquare}[]=[
 {id:'ask',label:'Ask a question',icon:MessageSquare},
 {id:'essay',label:'Write an essay',icon:FileText},
 {id:'html',label:'Create an artifact',icon:Layers3}
];
const starters=[
 {tag:'PRODUCT–MARKET FIT',title:'How do I know if we have product–market fit?',prompt:'How should a startup measure product market fit? Compare the practical advice from Sean Ellis and Rahul Vohra.',icon:Zap},
 {tag:'GROWTH STRATEGY',title:'Find the growth lever that actually matters.',prompt:'How should a product team choose between acquisition, activation, and retention as its growth priority?',icon:AudioLines},
 {tag:'PRODUCT DISCOVERY',title:'Turn customer conversations into better decisions.',prompt:'How does Teresa Torres recommend doing continuous product discovery and customer interviews?',icon:MessageSquare},
 {tag:'POSITIONING',title:'Make our product easier to understand.',prompt:'What does April Dunford recommend for defining product positioning and identifying the right customers?',icon:Layers3},
];
const initials=(name:string)=>name.split(/\s+/).map(s=>s[0]).slice(0,2).join('');

function Modal({open,onClose,title,children}:{open:boolean;onClose:()=>void;title:string;children:ReactNode}) {
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{if(open)ref.current?.showModal();else ref.current?.close();},[open]);
 return <dialog ref={ref} onCancel={onClose} onClick={e=>{if(e.target===ref.current)onClose();}}>
  <div className="modal-head"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={20}/></button></div>{children}
 </dialog>;
}

export default function App() {
 const [sessions,setSessions]=useState<Chat[]>([]);
 const [current,setCurrent]=useState<string|null>(null);
 const [messages,setMessages]=useState<Message[]>([]);
 const [artifacts,setArtifacts]=useState<Artifact[]>([]);
 const [status,setStatus]=useState<Status|null>(null);
 const [episodes,setEpisodes]=useState<Episode[]>([]);
 const savedProvider=useRef(localStorage.getItem('lenny-provider'));
 const [provider,setProvider]=useState(savedProvider.current||'ollama');
 const [mode,setMode]=useState<Mode>('ask');
 const [draft,setDraft]=useState('');
 const [busy,setBusy]=useState(false);
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState('');
 const [panel,setPanel]=useState<'sources'|'artifact'>('sources');
 const [panelOpen,setPanelOpen]=useState(window.innerWidth>1050);
 const [activeArtifact,setActiveArtifact]=useState<Artifact|null>(null);
 const [activeSources,setActiveSources]=useState<Source[]>([]);
 const [expanded,setExpanded]=useState<string|null>(null);
 const [sourceView,setSourceView]=useState(false);
 const [view,setView]=useState<'studio'|'library'|'artifacts'>('studio');
 const [search,setSearch]=useState('');
 const [settingsOpen,setSettingsOpen]=useState(false);
 const [helpOpen,setHelpOpen]=useState(false);
 const [mobileNav,setMobileNav]=useState(false);
 const [deleteId,setDeleteId]=useState<string|null>(null);
 const [copied,setCopied]=useState(false);
 const [elapsed,setElapsed]=useState(0);
 const end=useRef<HTMLDivElement>(null);
 const textarea=useRef<HTMLTextAreaElement>(null);
 const requestVersion=useRef(0);
 const activeProvider=status?.providers.find(p=>p.id===provider);
 const currentTitle=sessions.find(s=>s.id===current)?.title;
 const refreshing=useRef(false);

 async function refresh() {
  if(refreshing.current)return;refreshing.current=true;
  try {
   const results=await Promise.allSettled([api<Chat[]>('/sessions'),api<Status>('/status'),api<Episode[]>('/library')]);
   if(results[0].status==='fulfilled')setSessions(results[0].value);
   else setError(results[0].reason.message);
   if(results[1].status==='fulfilled'){setStatus(results[1].value);if(!savedProvider.current){setProvider(results[1].value.default_provider);savedProvider.current=results[1].value.default_provider;}}
   if(results[2].status==='fulfilled')setEpisodes(results[2].value);
  } finally {refreshing.current=false;}
 }
 useEffect(()=>{void refresh();},[]);
 useEffect(()=>{end.current?.scrollIntoView({behavior:'smooth'});},[messages,busy]);
 useEffect(()=>{
  if(!busy){setElapsed(0);return;}
  const start=Date.now(); const timer=setInterval(()=>setElapsed(Math.floor((Date.now()-start)/1000)),1000);
  return ()=>clearInterval(timer);
 },[busy]);
 useEffect(()=>{localStorage.setItem('lenny-provider',provider);},[provider]);

 function newChat() {
  if(busy)return;
  requestVersion.current++;setCurrent(null);setMessages([]);setArtifacts([]);setActiveArtifact(null);setActiveSources([]);
  setExpanded(null);setError('');setDraft('');setView('studio');setPanel('sources');setMobileNav(false);setLoading(false);
  setTimeout(()=>textarea.current?.focus(),0);
 }
 async function openChat(id:string) {
  if(busy)return;
  const version=++requestVersion.current;
  setLoading(true);setError('');setMobileNav(false);setView('studio');
  try {
   const data=await api<Detail>('/sessions/'+id);
   if(version!==requestVersion.current)return;
   setCurrent(id);setMessages(data.messages);setArtifacts(data.artifacts);
   setActiveSources([...data.messages].reverse().find(m=>m.sources?.length)?.sources||[]);
   setActiveArtifact(data.artifacts.at(-1)||null);setPanel('sources');
  } catch(e){if(version===requestVersion.current)setError((e as Error).message);}
  finally {if(version===requestVersion.current)setLoading(false);}
 }
 async function send(e?:FormEvent, override?:string) {
  e?.preventDefault();
  const text=(override||draft).trim();
  if(!text||busy||loading||!activeProvider?.available||!status?.agent||!status?.transcripts)return;
  setError('');setBusy(true);setView('studio');setDraft('');
  const optimistic:Message={id:'pending',role:'user',content:text};
  setMessages(prev=>[...prev,optimistic]);
  try {
   let id=current;
   if(!id) {
    const session=await api<Chat>('/sessions',{method:'POST',body:JSON.stringify({timezone:Intl.DateTimeFormat().resolvedOptions().timeZone})});
    id=session.id;setCurrent(id);setSessions(prev=>[session,...prev]);
   }
   const result=await api<{user:Message;assistant:Message;artifact:Artifact|null;session:Chat}>('/sessions/'+id+'/messages',{
    method:'POST',body:JSON.stringify({content:text,mode:mode==='ask'?'auto':mode,provider})
   });
   setMessages(prev=>[...prev.filter(m=>m.id!=='pending'),result.user,result.assistant]);
   setActiveSources(result.assistant.sources||[]);setExpanded(null);
   setSessions(prev=>[result.session,...prev.filter(s=>s.id!==id)]);
   if(result.artifact) {
    setArtifacts(prev=>[...prev,result.artifact!]);setActiveArtifact(result.artifact);
    setPanel('artifact');setPanelOpen(true);setSourceView(false);
   } else {setPanel('sources');}
  } catch(e) {
   setMessages(prev=>prev.filter(m=>m.id!=='pending'));setDraft(text);setError((e as Error).message);
  } finally {setBusy(false);setTimeout(()=>textarea.current?.focus(),0);}
 }
 function showSource(label:string,sources=activeSources) {
  setActiveSources(sources);setExpanded(label);setPanel('sources');setPanelOpen(true);
 }
 async function removeChat() {
  if(!deleteId)return;
  try {await api('/sessions/'+deleteId,{method:'DELETE'});setSessions(prev=>prev.filter(s=>s.id!==deleteId));if(current===deleteId)newChat();setDeleteId(null);}
  catch(e){setError((e as Error).message);setDeleteId(null);}
 }
 async function copyArtifact() {
  if(!activeArtifact)return;
  try {await navigator.clipboard.writeText(activeArtifact.content);setCopied(true);setTimeout(()=>setCopied(false),1800);}
  catch {setError('Clipboard access was blocked. Use Download to save the document.');}
 }
 function downloadArtifact() {
  if(!activeArtifact)return;
  const html=activeArtifact.format==='html';
  const blob=new Blob([html?safeArtifact(activeArtifact.content):activeArtifact.content],{type:html?'text/html':'text/markdown'});
  const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;
  a.download='lenny-'+activeArtifact.title.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,60)+(html?'.html':'.md');a.click();URL.revokeObjectURL(url);
 }
 const availableEpisodes=episodes.filter(e=>(e.title+' '+e.guest).toLowerCase().includes(search.toLowerCase()));
 const artifactHtml=useMemo(()=>activeArtifact?.format==='html'?safeArtifact(activeArtifact.content):'', [activeArtifact?.content,activeArtifact?.format]);
 const serviceReady=!!(activeProvider?.available&&status?.agent&&status?.transcripts);
 return <div className={'app '+(panelOpen&&view==='studio'?'with-panel':'')+(panelOpen&&panel==='artifact'?' artifact-open':'')}>
  {mobileNav&&<button className="nav-scrim" aria-label="Close navigation" onClick={()=>setMobileNav(false)}/>}
  <aside className={'sidebar '+(mobileNav?'mobile-open':'')}>
   <a href="/" className="brand" onClick={e=>{e.preventDefault();newChat();}} aria-label="Lenny Growth Assistant home"><span className="brand-mark">L<span>•</span></span><span>Lenny<span className="brand-sub">GROWTH ASSISTANT</span></span></a>
   <button className="new-chat" onClick={newChat} disabled={busy}><Plus size={18}/> New conversation <span>↗</span></button>
   <div className="nav-label">WORKSPACE</div>
   <nav aria-label="Main navigation">
    <button className={view==='studio'?'nav-item active':'nav-item'} onClick={()=>{setView('studio');setMobileNav(false);}}><MessageSquare size={18}/>Research studio</button>
    <button className={view==='library'?'nav-item active':'nav-item'} onClick={()=>{setView('library');setMobileNav(false);}}><Library size={18}/>Transcript library<span className="count">{status?.transcripts||'—'}</span></button>
    <button className={view==='artifacts'?'nav-item active':'nav-item'} onClick={()=>{setView('artifacts');setMobileNav(false);}}><FolderOpen size={18}/>Conversation artifacts{artifacts.length>0&&<span className="count">{artifacts.length}</span>}</button>
   </nav>
   <div className="history-heading"><span className="nav-label">RECENT CONVERSATIONS</span><MessageSquare size={13}/></div>
   <div className="history-list">
    {sessions.length===0?<p className="history-empty">Your thinking, saved here.<br/>Start with a question.</p>:sessions.map(s=><div key={s.id} className={'history-row '+(current===s.id?'selected':'')}>
     <button onClick={()=>void openChat(s.id)} disabled={busy} title={s.title}>{s.title}</button>
     <button className="delete-chat" onClick={()=>setDeleteId(s.id)} disabled={busy} aria-label={'Delete '+s.title}><Trash2 size={13}/></button>
    </div>)}
   </div>
   <div className="sidebar-bottom">
    <div className="knowledge-status"><span className={'status-dot '+(!status?.transcripts?'offline':'')}/><div><strong>{status?.transcripts?status.transcripts+' episodes indexed':'Knowledge base'}</strong><span>{status?.transcripts?'From Lenny’s Podcast':'Waiting for connection'}</span></div><BookOpen size={16}/></div>
    <button className="profile" onClick={()=>setSettingsOpen(true)}><span className="profile-avatar">Y</span><span><strong>Your workspace</strong><small>Personal research studio</small></span><Settings2 size={17}/></button>
   </div>
  </aside>
  <main className="main">
   <header className="topbar">
    <div className="breadcrumb"><button className="icon-button mobile-menu" aria-label="Open navigation" onClick={()=>setMobileNav(true)}><Menu size={20}/></button><span className="workspace-icon"><Layers3 size={16}/></span><span>Workspace</span><ChevronRight size={14}/><strong>{view==='library'?'Transcript library':view==='artifacts'?'Artifacts':'Research studio'}</strong></div>
    <div className="top-actions"><span className={'provider-state '+(activeProvider?.available&&status?.agent?'ready':'')}><span/>{activeProvider?.available&&status?.agent?'Connected':'Setup needed'}</span><div className="provider-select"><select aria-label="Model provider" value={provider} disabled={busy} onChange={e=>setProvider(e.target.value)}><option value="ollama">Ollama · Local</option><option value="anthropic">Anthropic · Cloud</option></select><ChevronDown size={13}/></div><button className="icon-button" onClick={()=>{setPanelOpen(!panelOpen);setView('studio');}} aria-label={panelOpen?'Hide evidence panel':'Show evidence panel'}>{panelOpen?<PanelRightClose size={18}/>:<PanelRightOpen size={18}/>}</button></div>
   </header>
   {view==='studio'?<>
    <div className="chat-heading"><span><span className="section-overline">THE RESEARCH STUDIO</span><h1>{currentTitle||'A little curiosity. A lot of possibility.'}</h1></span><button className="icon-button" aria-label="How this works" onClick={()=>setHelpOpen(true)}><CircleHelp size={18}/></button></div>
    <section className="conversation" aria-label="Conversation">
     {loading?<div className="loading"><Loader2 className="spin"/> Loading conversation…</div>:messages.length===0?
      <div className="welcome">
       <div className="welcome-symbol"><AudioLines size={29}/><span className="spark"><Sparkles size={13}/></span></div>
       <div className="eyebrow">GREAT THINKING STARTS HERE</div>
       <h2>Good questions.<br/><em>Grounded answers.</em></h2>
       <p>Bring your next product challenge.<br/>Find a way forward in Lenny’s conversations.</p>
       <div className="starter-grid">{starters.map(s=><button key={s.tag} className="starter" disabled={busy} onClick={()=>{setDraft(s.prompt);textarea.current?.focus();}}><div><s.icon size={18}/><ArrowUpRight size={16}/></div><small>{s.tag}</small><span>{s.title}</span></button>)}</div>
       <div className="welcome-note"><ShieldCheck size={14}/>Real conversations. Sources you can check.</div>
      </div>:
      <div className="message-list">{messages.map(m=><article key={m.id} className={'message '+m.role}>
       <div className={'message-avatar '+m.role}>{m.role==='user'?'Y':<AudioLines size={19}/>}</div>
       <div className="message-body"><div className="message-author">{m.role==='user'?'You':'Lenny Growth Assistant'}{m.role==='assistant'&&m.model&&<small>{m.provider==='ollama'?'LOCAL':'CLOUD'}</small>}</div><Markdown content={m.content} onSource={label=>showSource(label,m.sources)}/>
        {!!m.warnings?.length&&<div className="draft-warning">{m.warnings.map(w=><p key={w}>{w}</p>)}</div>}
        {m.artifact_id&&<button className="artifact-card" onClick={()=>{const a=artifacts.find(a=>a.id===m.artifact_id);if(a){setActiveArtifact(a);setActiveSources(a.sources);setPanel('artifact');setPanelOpen(true);setSourceView(false);}}}><span className="file-icon"><FileText size={23}/></span><span><strong>{m.mode==='essay'?'Your Ship 30 essay':m.mode==='html'?'Your HTML artifact':'Your Markdown document'}</strong><small>{m.word_count?.toLocaleString()} words · Open in viewer</small></span><ArrowUpRight size={18}/></button>}
        {!!m.sources?.length&&<button className="source-summary" onClick={()=>{setActiveSources(m.sources!);setPanel('sources');setPanelOpen(true);}}><BookOpen size={13}/>{m.sources.length} source passages<ChevronRight size={12}/></button>}
       </div>
      </article>)}{busy&&<div className="message assistant"><div className="message-avatar assistant"><AudioLines size={19}/></div><div className="message-body"><div className="message-author">Lenny Growth Assistant</div><div className="thinking" role="status" aria-live="polite"><span/><span/><span/><p>{elapsed<4?'Finding relevant passages…':mode==='ask'?'Reading the evidence and shaping an answer…':'Drafting your document from the evidence…'}</p></div><small className="generation-time">{elapsed}s · {provider==='ollama'?'Your local model is working. Long essays can take 10–25 minutes on a CPU.':'Generating with Anthropic.'}</small></div></div>}<div ref={end}/></div>}
    </section>
    <div className="composer-wrap">
     {status&&!serviceReady&&!busy&&<div className="connection-notice" role="status"><span><strong>Let’s get connected.</strong> {activeProvider?.available?'The agent or transcript library is not ready.':'The selected model is not configured.'}</span><button type="button" onClick={()=>setSettingsOpen(true)}>Check connection <ArrowUpRight size={14}/></button></div>}
     {error&&<div className="error-banner" role="alert"><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}
     <form className="composer" onSubmit={e=>void send(e)}>
      <div className="mode-tabs">{modes.map(m=><button type="button" key={m.id} className={mode===m.id||m.id==='html'&&mode==='markdown'?'selected':''} onClick={()=>setMode(m.id)} disabled={busy}><m.icon size={14}/>{m.label}</button>)}</div>
      <textarea ref={textarea} aria-label="Your message" placeholder={mode==='essay'?'What idea should we turn into a 1,250-word essay?':mode==='html'||mode==='markdown'?'Describe a document, brief, or visual you want to create…':'Ask a product or growth question…'} value={draft} onChange={e=>setDraft(e.target.value)} maxLength={8000} rows={2} disabled={busy||loading} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();void send();}}}/>
      <div className="composer-footer"><span className="composer-context"><BookOpen size={14}/>{status?.transcripts?status.transcripts+' podcast transcripts':'Transcript knowledge base'}</span><div className="send-controls">{(mode==='html'||mode==='markdown')&&<select aria-label="Artifact format" value={mode} onChange={e=>setMode(e.target.value as Mode)} disabled={busy}><option value="html">HTML / CSS</option><option value="markdown">Markdown</option></select>}<span className="key-hint">{draft.length>7000?`${draft.length.toLocaleString()} / 8,000`:"↵ to send"}</span><button className="send-button" type="submit" disabled={!draft.trim()||busy||loading||!serviceReady} aria-label="Send message">{busy?<Loader2 size={18} className="spin"/>:<ArrowUp size={19}/>}</button></div></div>
     </form>
     <div className="composer-disclaimer">Grounded in transcripts. Still worth a second look.<span>Shift + Enter for a new line</span></div>
    </div>
   </>:view==='library'?<section className="library-view"><div className="section-overline">THE KNOWLEDGE BEHIND THE ANSWERS</div><h1>The transcript library<span>{episodes.length}</span></h1><p>Conversations with the people who build, lead, and grow products.</p><label className="library-search"><Search size={18}/><input placeholder="Find a guest or topic…" aria-label="Search transcript library" value={search} onChange={e=>setSearch(e.target.value)}/></label><div className="episode-grid">{availableEpisodes.map((e,i)=><a key={e.id} href={safeUrl(e.url)} target="_blank" rel="noopener noreferrer" className="episode-card"><div className={'guest-avatar color-'+i%4}>{initials(e.guest)}</div><span><strong>{e.guest}</strong><small>{e.title}</small></span><ArrowUpRight size={17}/></a>)}</div>{!availableEpisodes.length&&<div className="empty-state"><Search size={30}/><h2>No transcripts found</h2><p>{episodes.length?'Try a different guest or topic.':'Import transcripts to start building your knowledge base.'}</p></div>}</section>:
   <section className="library-view"><div className="section-overline">FROM THINKING TO SOMETHING TANGIBLE</div><h1>Conversation artifacts<span>{artifacts.length}</span></h1><p>Documents created in {currentTitle?'“'+currentTitle+'”':'your current conversation'}.</p>{artifacts.length?<div className="saved-artifacts">{artifacts.map(a=><button key={a.id} onClick={()=>{setActiveArtifact(a);setActiveSources(a.sources);setPanel('artifact');setPanelOpen(true);setView('studio');}}><FileText size={25}/><strong>{a.title}</strong><span>{a.format.toUpperCase()} · {a.sources.length} sources</span><ArrowUpRight size={16}/></button>)}</div>:<div className="empty-state"><FolderOpen size={35}/><h2>Your ideas, ready to take shape.</h2><p>Open a conversation and choose Write an essay or Create an artifact.</p><button className="primary-button" onClick={()=>{setView('studio');setMode('essay');}}>Write your first essay<ArrowUpRight size={16}/></button></div>}</section>}
  </main>
  {panelOpen&&view==='studio'&&<aside className="evidence-panel">
   <div className="panel-tabs"><button className={panel==='sources'?'selected':''} onClick={()=>setPanel('sources')}><BookOpen size={15}/>Evidence{activeSources.length>0&&<span>{activeSources.length}</span>}</button><button className={panel==='artifact'?'selected':''} onClick={()=>setPanel('artifact')}><Layers3 size={15}/>Artifact{artifacts.length>0&&<span>{artifacts.length}</span>}</button><button className="icon-button close-panel" aria-label="Close side panel" onClick={()=>setPanelOpen(false)}><X size={16}/></button></div>
   {panel==='sources'?<div className="sources-content">
    <div className="panel-overline">FOLLOW THE THINKING</div><h2>{activeSources.length?'The evidence behind it.':'Meet your source material.'}</h2><p className="panel-intro">{activeSources.length?'Read the passages behind the answer. Every source takes you back to the conversation.':'Good advice has a source. Yours comes from the people behind extraordinary products.'}</p>
    {activeSources.length?<div className="source-list">{activeSources.map(s=><div className={'source-item '+(expanded===s.label?'expanded':'')} key={s.label}>
     <button className="source-toggle" onClick={()=>setExpanded(expanded===s.label?null:s.label)}><span className="source-number">{s.label}</span><span><strong>{s.guest}</strong><small>{s.title}</small></span><ChevronDown size={15}/></button>
     {expanded===s.label&&<div className="source-excerpt"><div className="excerpt-label">TRANSCRIPT PASSAGE {s.timestamp&&'· '+s.timestamp}</div><p>{s.excerpt}</p><a href={safeUrl(s.url)} target="_blank" rel="noopener noreferrer">Read the transcript<ArrowUpRight size={13}/></a>{safeUrl(s.youtube_url)&&<a href={safeUrl(s.youtube_url)} target="_blank" rel="noopener noreferrer">Watch the conversation<ArrowUpRight size={13}/></a>}</div>}
    </div>)}</div>:<>
     <div className="featured-guests">{episodes.slice(0,4).map((e,i)=><a key={e.id} href={safeUrl(e.url)} target="_blank" rel="noopener noreferrer"><span className={'guest-avatar color-'+i}>{initials(e.guest)}</span><span><strong>{e.guest}</strong><small>Lenny’s Podcast</small></span><ArrowUpRight size={15}/></a>)}</div>
     <button className="browse-library" onClick={()=>setView('library')}>Explore the transcript library<ArrowUpRight size={15}/></button>
     <div className="evidence-empty"><span className="evidence-ring"><BookOpen size={25}/></span><h3>Every insight has a trail.</h3><p>Ask a question and the supporting passages will appear here.</p><div className="trail"><span>QUESTION</span><i/><span>EVIDENCE</span><i/><span>ACTION</span></div></div>
    </>}
    <div className="source-footer"><ShieldCheck size={16}/><p>{activeSources.length?'Source labels are checked against retrieved passages. Review the passages to verify each claim.':'Answers stay within the indexed transcripts. When the evidence falls short, we say so.'}</p></div>
   </div>:activeArtifact?<div className="artifact-panel">
    <div className="artifact-toolbar"><select aria-label="Choose artifact" value={activeArtifact.id} onChange={e=>{const selected=artifacts.find(a=>a.id===e.target.value)!;setActiveArtifact(selected);setActiveSources(selected.sources);setSourceView(false);}}>{artifacts.map(a=><option key={a.id} value={a.id}>{a.title}</option>)}</select><div><button className={'icon-button '+(sourceView?'on':'')} onClick={()=>setSourceView(!sourceView)} aria-label={sourceView?'Show rendered artifact':'Show artifact source'}><Code2 size={17}/></button><button className="icon-button" onClick={()=>void copyArtifact()} aria-label="Copy artifact">{copied?<Check size={17}/>:<Copy size={17}/>}</button><button className="icon-button" onClick={downloadArtifact} aria-label="Download artifact"><Download size={17}/></button></div></div>
    <div className="artifact-meta"><span>{activeArtifact.format.toUpperCase()}</span><span>{activeArtifact.sources.length} sources</span>{activeArtifact.format==='html'&&<span><ShieldCheck size={12}/>Isolated preview</span>}</div>
    {sourceView?<pre className="artifact-source">{activeArtifact.content}</pre>:activeArtifact.format==='html'?<iframe title="Artifact preview" sandbox="" referrerPolicy="no-referrer" srcDoc={artifactHtml}/>:<div className="markdown-artifact"><Markdown content={activeArtifact.content} onSource={label=>showSource(label,activeArtifact.sources)}/></div>}
   </div>:<div className="empty-artifact"><div className="empty-paper"><FileText size={38}/></div><h2>A home for your next idea.</h2><p>Create an essay, Markdown document, or HTML artifact. It will open right here, beside your conversation.</p><button className="secondary-button" onClick={()=>{setMode('essay');textarea.current?.focus();}}>Start an essay<ArrowUpRight size={15}/></button></div>}
  </aside>}
  <Modal open={settingsOpen} onClose={()=>setSettingsOpen(false)} title="Workspace settings">
   <div className="settings-content"><p>Choose where your answers are generated. Switching to cloud sends your question and relevant transcript passages to Anthropic.</p><label>Model provider<select value={provider} disabled={busy} onChange={e=>setProvider(e.target.value)}><option value="ollama">Ollama — on this computer</option><option value="anthropic">Anthropic — cloud</option></select></label><div className="settings-status">{status?.providers.map(p=><div key={p.id}><span><strong>{p.label}</strong><small>{p.model}</small></span><span className={p.available?'available':'unavailable'}>{p.available?'Available':'Not configured'}</span></div>)}</div><p className="settings-note">Provider changes never happen automatically. Model names and credentials are configured in the server’s .env file.</p><button className="secondary-button" onClick={()=>void refresh()}>Refresh service status</button></div>
  </Modal>
  <Modal open={helpOpen} onClose={()=>setHelpOpen(false)} title="A question → evidence → a useful next step">
   <div className="settings-content"><p><strong>Ask a question.</strong> Explore a product challenge or compare ideas from podcast guests. Follow-ups remember this conversation.</p><p><strong>Check the evidence.</strong> Select a source label to read the supporting passage and open the original transcript.</p><p><strong>Make something useful.</strong> Choose Write an essay for a Ship 30 draft, or Create an artifact for a Markdown or HTML document.</p><p>Each conversation is separate. Your chats and artifacts are saved in your workspace.</p></div>
  </Modal>
  <Modal open={!!deleteId} onClose={()=>setDeleteId(null)} title="Delete this conversation?"><div className="settings-content"><p>This removes its messages and artifacts permanently.</p><div className="dialog-actions"><button className="secondary-button" onClick={()=>setDeleteId(null)}>Keep conversation</button><button className="danger-button" onClick={()=>void removeChat()}>Delete conversation</button></div></div></Modal>
 </div>;
}
