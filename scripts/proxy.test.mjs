import test from 'node:test';
import assert from 'node:assert/strict';
import handler from '../api/proxy.mjs';

function response() {
  return {headers:{}, setHeader(k,v){this.headers[k]=v;}, end(value){this.body=Buffer.from(value).toString();}};
}

test('proxy forwards only the workspace id and server-side reviewer credential', async () => {
  process.env.BACKEND_URL='https://backend.example';
  process.env.BACKEND_ACCESS_PASSWORD='secret-value';
  const original=global.fetch;
  global.fetch=async (url, init) => {
    assert.equal(url,'https://backend.example/api/sessions');
    assert.equal(init.headers['X-Workspace-ID'],'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');
    assert.equal(init.headers.Authorization,'Basic '+Buffer.from('reviewer:secret-value').toString('base64'));
    assert.equal(init.headers.Cookie,undefined);
    return new Response('{"ok":true}',{status:200,headers:{'Content-Type':'application/json'}});
  };
  try {
    const res=response();
    await handler({method:'GET',query:{path:'sessions'},headers:{'x-workspace-id':'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',cookie:'ignored'}},res);
    assert.equal(res.statusCode,200);
    assert.equal(res.body,'{"ok":true}');
  } finally { global.fetch=original; }
});

test('proxy rejects traversal without contacting an upstream', async () => {
  process.env.BACKEND_URL='https://backend.example';
  const original=global.fetch;
  global.fetch=async () => { throw new Error('must not run'); };
  try {
    const res=response();
    await handler({method:'GET',query:{path:'../private'},headers:{}},res);
    assert.equal(res.statusCode,503);
  } finally { global.fetch=original; }
});
