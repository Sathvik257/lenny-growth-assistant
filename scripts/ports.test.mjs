import test from 'node:test';
import assert from 'node:assert/strict';
import {chooseAppPort,validPort} from './ports.mjs';

test('launcher skips a different application instead of reusing it',async()=>{
 const result=await chooseAppPort(8000,'ours',async port=>port===8001,async()=>({ok:true,json:async()=>({status:'ok',service:'other'})}));
 assert.deepEqual(result,{port:8001,reuse:false});
});
test('launcher reuses only this project workspace',async()=>{
 const result=await chooseAppPort(8001,'ours',async()=>false,async()=>({ok:true,json:async()=>({service:'lenny-growth-studio',workspace:'ours'})}));
 assert.deepEqual(result,{port:8001,reuse:true});
});
test('invalid port is rejected',()=>{
 for(const value of ['bad',0,65536,1.5])assert.throws(()=>validPort(value));
});
