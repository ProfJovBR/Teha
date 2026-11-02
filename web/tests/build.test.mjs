import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
test('The approved layout and navigation are retained',async()=>{
 const html=await readFile('public/index.html','utf8');
 for(const id of ['drawer','profileEdit','calendarGrid','waitingList','form-pacientes','form-triagem','toothForm','backupExport'])assert.ok(html.includes('id="'+id+'"'),id);
 assert.ok(!html.includes('data-page="triagem" aria-label'));
 assert.ok(html.includes('Visualizar demonstração'));
});
test('No secret or service role key is shipped in source',async()=>{
 const src=await readFile('src/cloud.js','utf8');
 assert.ok(!src.includes('service_role'));assert.ok(!src.includes('sb_secret_'));
 assert.ok(src.includes('sessionStorage'));assert.ok(src.includes('__SUPABASE_KEY__'));
});
test('Generated bundle is valid JavaScript',async()=>{
 new vm.Script(await readFile('dist/app.js','utf8'));
});
test('Cloud writes fail explicitly and use optimistic locking',async()=>{
 const src=await readFile('src/layout.js','utf8');
 assert.ok(src.includes("cloud.rpc('teha_save'"));assert.ok(src.includes('p_expected:_revision??0'));
 assert.ok(src.includes('O registro não foi salvo'));
});
test('Schema restricts data ownership and preserves clinical records',async()=>{
 const sql=await readFile('database/schema.sql','utf8');
 assert.ok(sql.includes('enable row level security'));
 assert.ok(sql.includes('owner_id=(select auth.uid())'));
 assert.ok(sql.includes("if new.store in ('notes','teeth')"));
 assert.ok(!sql.includes('grant delete'));
});
