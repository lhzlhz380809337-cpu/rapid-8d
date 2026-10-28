// DOM integration test, not a real-browser visual test.
const {JSDOM,VirtualConsole}=require('../.ui-test-deps/node_modules/jsdom');
const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const session=JSON.parse(fs.readFileSync(path.join(root,process.env.RAPID_TEST_DATA||'.qa/frozen','session.json'),'utf8'));
const mock=JSON.parse(fs.readFileSync(path.join(root,'.qa/mock-session.json'),'utf8'));
const base='http://127.0.0.1:'+session.port;
const errors=[],downloads=[];
const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!e.message.includes('navigation'))errors.push(e.message)});
(async()=>{
 const html=await (await fetch(base)).text();
 const dom=new JSDOM(html,{url:base+'/#token='+session.token,runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
  w.fetch=(url,opts)=>fetch(new URL(url,base),opts);w.structuredClone=structuredClone;
  w.URL.createObjectURL=blob=>{downloads.push(blob);return 'blob:testing';};w.URL.revokeObjectURL=()=>{};
  w.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};
  w.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');};
 }});
 const w=dom.window,d=w.document,el=id=>d.getElementById(id),sleep=ms=>new Promise(r=>setTimeout(r,ms));
 async function wait(fn,message){for(let i=0;i<240;i++){if(fn())return;await sleep(50);}throw Error(message+' | '+el('toast').textContent);}
 async function click(id){assert(el(id),'Missing '+id);el(id).click();await sleep(80);}
 async function api(route,body){const r=await fetch(base+'/api'+route,{method:body?'POST':'GET',headers:{'Content-Type':'application/json','X-Rapid-Token':session.token},body:body?JSON.stringify(body):undefined});if(!r.ok)throw Error(await r.text());return r.json();}
 async function snapshot(name){
  if(!process.env.RAPID_UI_SNAPSHOTS)return;
  const doc=d.documentElement.cloneNode(true);
  doc.querySelectorAll('script').forEach(s=>s.remove());
  doc.querySelectorAll('link[rel="icon"]').forEach(s=>s.remove());
  const style=doc.querySelector('link[rel="stylesheet"]');
  style.href=require('node:url').pathToFileURL(path.join(root,'ui/style.css')).href;
  const toast=doc.querySelector('#toast');if(toast)toast.classList.add('hidden');
  const diagram=doc.querySelector('#fishPreview img');
  if(diagram){
   const list=await api('/cases');
   const r=await fetch(base+'/api/cases/'+list[0].id+'/fishbone.svg',{headers:{'X-Rapid-Token':session.token}});
   diagram.src='data:image/svg+xml;base64,'+Buffer.from(await r.arrayBuffer()).toString('base64');
  }
  fs.writeFileSync(path.join(root,'.qa','redesign-'+name+'.html'),'<!doctype html>\n'+doc.outerHTML,'utf8');
 }
 try{
  await wait(()=>el('setupHint').classList.contains('hidden')===false,'bootstrap');
  assert.equal(el('totalCases').textContent,'0','dashboard uses actual case totals');
  await snapshot('home-empty');
  await click('settingsBtn');await wait(()=>el('apiBase'),'settings');
  el('apiBase').value='http://127.0.0.1:'+mock.port+'/v1';el('apiModel').value='synthetic-test';
  await click('testModel');await wait(()=>el('toast').textContent.includes('连接成功'),'connection test');
  await click('closeModal');
  d.querySelector('[data-new="import"]').click();el('newTitle').value='隔膜分切边缘毛刺调查（示例）';
  await click('createCase');await wait(()=>!el('workspace').classList.contains('hidden'),'create case');
  el('pasteText').value='模拟记录：隔膜边缘毛刺，抽查200卷中6卷不良。尚未验证根因。';
  await click('pasteBtn');await wait(()=>el('sourceCount').textContent==='1','paste');
  // Uploaded text follows the same FileReader -> upload route as office files.
  Object.defineProperty(el('files'),'files',{configurable:true,value:[new w.File(['第二条模拟记录'],'fixture.txt',{type:'text/plain'})]});
  el('files').dispatchEvent(new w.Event('change'));await wait(()=>el('sourceCount').textContent==='2','upload');
  const check=d.querySelectorAll('[data-source]')[1];check.checked=false;check.dispatchEvent(new w.Event('change',{bubbles:true}));
  await click('importBtn');await wait(()=>!el('proposalBanner').classList.contains('hidden'),'whole report');
  assert.equal(d.querySelectorAll('[data-source]')[1].checked,false,'selection must persist');
  await click('proposalBtn');await wait(()=>d.querySelectorAll('[data-choose]').length===8,'8 stage suggestion');
  await click('acceptProposal');await wait(()=>!el('modal').open,'accept all');
  assert(el('reportContent').textContent.includes('质量负责人'));
  assert(el('d4Views').classList.contains('hidden'),'fishbone view is hidden outside D4');
  d.querySelector('[data-stage="D4"]').click();await wait(()=>el('reportHeading').textContent.startsWith('D4'),'D4 preview');
  assert(!el('d4Views').classList.contains('hidden'),'fishbone view appears in D4');
  assert(!el('reportDocument').classList.contains('hidden'),'D4 defaults to report');
  d.querySelector('[data-report-view="fish"]').click();
  await wait(()=>d.querySelector('#fishPreview img'),'fish preview');
  await snapshot('workspace');
  d.querySelector('[data-report-view="report"]').click();
  await click('focusReportBtn');assert(el('workspace').classList.contains('report-focus'));
  assert.equal(el('focusReportBtn').getAttribute('aria-pressed'),'true');
  await snapshot('report-expanded');
  await click('focusReportBtn');assert(!el('workspace').classList.contains('report-focus'));
  d.querySelector('[data-stage="D1"]').click();await wait(()=>el('reportHeading').textContent.startsWith('D1'),'return to D1');
  assert(el('d4Views').classList.contains('hidden'),'fishbone view hides after leaving D4');
  await click('editBtn');el('reportEditor').value='手工核对内容 <script>bad()</script>';el('reportEditor').dispatchEvent(new w.Event('input'));
  await wait(()=>el('saveState').textContent==='已保存','autosave');await click('editBtn');
  assert(el('reportContent').textContent.includes('<script>'));assert.equal(el('reportContent').querySelectorAll('script').length,0,'escape report HTML');
  el('message').value='继续澄清人员职责';await click('sendBtn');await wait(()=>!el('proposalBanner').classList.contains('hidden'),'guided response');
  await click('proposalBtn');await wait(()=>d.querySelector('[data-choose="D1"]'),'proposal compare');
  assert.equal(d.querySelector('[data-choose="D1"]').checked,false,'manual edit retained by default');
  await click('keepOriginal');
  d.querySelector('[data-stage="D4"]').click();await wait(()=>el('reportHeading').textContent.startsWith('D4'),'D4');
  d.querySelector('[data-report-view="fish"]').click();await wait(()=>!el('fishWorkspace').classList.contains('hidden'),'fish workspace');
  await click('fishBtn');await wait(()=>el('fishProblem'),'fish editor');
  el('fishProblem').value='修改后的模拟问题';
  d.querySelector('[data-nlabel]').value='修改后的候选原因';
  await click('saveFish');await wait(()=>!el('modal').open,'save fish');
  await click('wordBtn');await wait(()=>el('toast').textContent.includes('已导出'),'word export');
  await click('pdfBtn');await wait(()=>el('toast').textContent.includes('已导出'),'PDF export');
  await click('historyBtn');await wait(()=>d.querySelectorAll('[data-version]').length>0,'history');
  d.querySelector('[data-version]').click();await wait(()=>el('restoreVersion'),'history preview');
  const cases=await api('/cases');const c=await api('/cases/'+cases[0].id);
  assert.equal(c.fishbone.problem_statement,'修改后的模拟问题');assert(c.messages.some(x=>x.role==='assistant'));assert.equal(c.stages[0].report_markdown,'手工核对内容 <script>bad()</script>');
  await click('closeModal');await click('dashboardBtn');await wait(()=>!el('home').classList.contains('hidden'),'dashboard navigation');
  assert.equal(el('totalCases').textContent,'1');assert.equal(el('activeCases').textContent,'1');assert.equal(el('closedCases').textContent,'0');
  assert.equal(d.querySelectorAll('.recent-table tbody tr').length,1);
  await click('caseLibraryBtn');assert(!el('caseLibrary').classList.contains('hidden'));assert.equal(d.querySelectorAll('#caseList .case-item').length,1);
  await click('reportCenterBtn');assert(!el('reportCenter').classList.contains('hidden'));assert.equal(d.querySelectorAll('#reportCases .report-case').length,1);
  await click('dashboardBtn');
  await snapshot('home');
  d.querySelector('.open-case').click();await wait(()=>!el('workspace').classList.contains('hidden'),'open recent case');
  assert(el('caseTitle').textContent.includes('隔膜分切'));
  await click('focusReportBtn');await click('newBtn');el('newTitle').value='新建引导分析示例';
  await click('createCase');await wait(()=>el('caseTitle').textContent==='新建引导分析示例','new guided case');
  assert(!el('workspace').classList.contains('report-focus'),'new case must show investigation');
  assert.equal(errors.length,0,errors.join('\n'));
  console.log('PASS: settings, test connection, case, paste, file upload, source selection, whole-report proposal, adoption, safe text, manual edits, autosave, guided proposal, fish editing, Word/PDF export, history.');
  console.log('TEST_CASE='+c.id);
 }finally{dom.window.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
