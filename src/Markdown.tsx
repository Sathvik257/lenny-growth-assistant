import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {safeUrl} from './api';
export default function Markdown({content,onSource}:{content:string;onSource?:(label:string)=>void}) {
 const linked=content.replace(/\[(S\d+)\](?!\()/g,'[$1](#source-$1)');
 return <div className="prose"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
  img:()=>null,
  a:({href,children})=>href?.startsWith('#source-')
   ? <button className="citation" onClick={()=>onSource?.(href.slice(8))} aria-label={'View source '+href.slice(8)}>{children}</button>
   : <a href={safeUrl(href || '')} target="_blank" rel="noopener noreferrer">{children}</a>,
 }}>{linked}</ReactMarkdown></div>;
}
