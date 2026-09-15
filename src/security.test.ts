// @vitest-environment jsdom
import {describe,it,expect} from 'vitest';
import {safeArtifact,ARTIFACT_CSP} from './security';
describe('generated HTML boundary',()=>{
 it('gives generated fragments a visible title and readable default styles',()=>{
  const doc=new DOMParser().parseFromString(safeArtifact('<title>A clear title</title><article><p>Useful content [S1].</p></article>'),'text/html');
  expect(doc.querySelector('h1')?.textContent).toBe('A clear title');
  expect(doc.querySelector('style')?.textContent).toContain('system-ui');
 });
 it('removes script, event handlers, navigation and embedded content',()=>{
  const html=safeArtifact('<html><head><meta http-equiv="refresh" content="0;url=https://evil.test"></head><body onload="alert(1)"><script>parent.hacked=true</script><h1>Useful work</h1><img src=x onerror="alert(1)"><iframe src="https://evil.test"></iframe><form action="https://evil.test"><input></form><a href="javascript:alert(1)">Link</a><svg onload="alert(1)"></svg></body></html>');
  const doc=new DOMParser().parseFromString(html,'text/html');
  expect(doc.querySelector('h1')?.textContent).toBe('Useful work');
  expect(doc.querySelectorAll('script,img,iframe,form,input,a,svg,base,link').length).toBe(0);
  expect(doc.body.getAttribute('onload')).toBeNull();
  expect(doc.querySelector('meta[http-equiv="refresh"]')).toBeNull();
  expect(doc.querySelector('meta[http-equiv="Content-Security-Policy"]')?.getAttribute('content')).toBe(ARTIFACT_CSP);
 });
 it('retains safe inline CSS while CSP denies all network resources',()=>{
  const html=safeArtifact('<style>h1{color:red;background:url(https://evil.test/x)}</style><h1 style="padding:20px">Hello</h1>');
  expect(html).toContain('color:red');
  expect(html).toContain("default-src 'none'");
  expect(html).toContain("connect-src 'none'");
  expect(html).toContain("img-src 'none'");
 });
 it('closes malformed documents and neutralizes nested attack markup',()=>{
  const html=safeArtifact('<p>Safe</p><math><mtext><table><mglyph><style><!--</style><img title="--><img src=1 onerror=alert(1)>">');
  const doc=new DOMParser().parseFromString(html,'text/html');
  expect(doc.querySelectorAll('img,math,script').length).toBe(0);
  expect(doc.querySelector('meta[http-equiv="Content-Security-Policy"]')).not.toBeNull();
 });
});
