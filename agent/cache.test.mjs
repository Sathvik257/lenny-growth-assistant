import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {cacheKey,readGeneration,saveGeneration} from './cache.mjs';
test('generation cache isolates models and sessions and survives reread',()=>{
 mkdirSync('.runtime',{recursive:true});
 const dir=mkdtempSync('.runtime/cache-test-');
 const key=cacheKey({session_id:'a',prompt:'same'},'model-a');
 assert.notEqual(key,cacheKey({session_id:'b',prompt:'same'},'model-a'));
 assert.notEqual(key,cacheKey({session_id:'a',prompt:'same'},'model-b'));
 saveGeneration(dir,key,{content:'A generated answer [S1]'});
 assert.equal(readGeneration(dir,key).content,'A generated answer [S1]');
 writeFileSync(join(dir,key+'.json'),JSON.stringify({saved_at:0,result:{content:'expired'}}));
 assert.equal(readGeneration(dir,key),null);
 writeFileSync(join(dir,key+'.json'),'invalid');
 assert.equal(readGeneration(dir,key),null);
});
