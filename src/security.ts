import DOMPurify from 'dompurify';
export const ARTIFACT_CSP = "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
export function safeArtifact(html:string) {
 const clean=DOMPurify.sanitize(html,{
  WHOLE_DOCUMENT:true,
  ALLOWED_TAGS:['html','head','body','title','style','main','section','article','header','footer','aside','div','span','p','h1','h2','h3','h4','h5','h6','ul','ol','li','strong','em','b','i','small','blockquote','pre','code','table','thead','tbody','tr','th','td','caption','hr','br'],
  ALLOWED_ATTR:['class','style','id','colspan','rowspan','scope','aria-label'],
  FORBID_TAGS:['script','iframe','object','embed','form','input','button','svg','math','link','base','meta'],
  ALLOW_DATA_ATTR:false
 });
 const doc=new DOMParser().parseFromString(clean,'text/html');
 if(!doc.querySelector('h1')){const heading=doc.createElement('h1');heading.textContent=doc.title||'Research brief';doc.body.prepend(heading);}
 return doc.documentElement.outerHTML.replace('<head>', '<head><meta http-equiv="Content-Security-Policy" content="'+ARTIFACT_CSP+'"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{overflow-wrap:anywhere;font:16px/1.65 system-ui,sans-serif;color:#334155;background:#fff;margin:28px;max-width:760px}h1{font:normal 36px/1.15 Georgia,serif;color:#253342;margin:0 0 28px;padding-bottom:20px;border-bottom:3px solid #e97852}h2,h3{color:#253342;line-height:1.3}section{margin:22px 0}p{margin:12px 0}table{max-width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #e2e8f0}</style>');
}
