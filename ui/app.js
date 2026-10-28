'use strict';
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stateNames={not_started:'未开始',in_progress:'进行中',blocked:'待补证据',ready_for_review:'待复核',complete:'已复核'};
const evidenceNames={suspected:'待验证',supported:'有支持',verified:'已验证',refuted:'已排除',inconclusive:'不确定'};
const S={case:null,stage:'D1',cases:[],settings:{},checks:{},editing:false,busy:false,proposal:null,selected:new Set(),dirty:false,saveChain:Promise.resolve(),saveTimer:null,fishURL:null,view:'home',reportView:'report',mobilePane:'analysis'};
let token=new URLSearchParams(location.hash.slice(1)).get('token')||sessionStorage.getItem('rapidToken')||'';
if(token){sessionStorage.setItem('rapidToken',token);history.replaceState(null,'',location.pathname);}
function toast(text,error=false){$('toast').textContent=text;$('toast').className='toast'+(error?' error':'');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').classList.add('hidden'),error?8000:4200);}
async function api(path,data,raw=false){
 const opts={headers:{'X-Rapid-Token':token}};
 if(data!==undefined){opts.method='POST';opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(data);}
 const response=await fetch('/api'+path,opts);
 if(!response.ok){let err;try{err=await response.json();}catch{err={error:'服务暂时不可用。'};}throw Error(err.error||'操作未完成');}
 return raw?response:response.json();
}
function guard(fn){return async(...args)=>{try{return await fn(...args);}catch(e){toast(e.message||String(e),true);}};}
function modal(title,html,wide=false){$('modalTitle').textContent=title;$('modalBody').innerHTML=html;$('modal').classList.toggle('wide-modal',wide);if(!$('modal').open)$('modal').showModal();}
function closeModal(){$('modal').close();}
function field(label,id,value='',type='text',hint=''){return '<label class="form-field">'+esc(label)+'<input id="'+id+'" type="'+type+'" value="'+esc(value)+'">'+(hint?'<small>'+esc(hint)+'</small>':'')+'</label>';}
function markdown(value){
 const lines=String(value||'').split('\n');let out=[],i=0;
 const inline=s=>esc(s).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
 while(i<lines.length){
  const line=lines[i].trim();
  if(!line){i++;continue;}
  if(line.includes('|')&&i+1<lines.length&&/^\s*\|?\s*:?-{3,}/.test(lines[i+1])){
   const row=s=>s.trim().replace(/^\||\|$/g,'').split('|').map(x=>x.trim());
   out.push('<table><thead><tr>'+row(line).map(x=>'<th>'+inline(x)+'</th>').join('')+'</tr></thead><tbody>');i+=2;
   while(i<lines.length&&lines[i].includes('|')&&lines[i].trim()){out.push('<tr>'+row(lines[i]).map(x=>'<td>'+inline(x)+'</td>').join('')+'</tr>');i++;}
   out.push('</tbody></table>');continue;
  }
  if(/^#{1,6}\s/.test(line))out.push('<h3>'+inline(line.replace(/^#+\s*/,''))+'</h3>');
  else if(/^[-*]\s/.test(line))out.push('<p>• '+inline(line.slice(2))+'</p>');
  else out.push('<p>'+inline(line)+'</p>');
  i++;
 }
 return out.join('');
}
async function bootstrap(){const d=await api('/bootstrap');S.cases=d.cases;S.settings=d.settings;S.checks=d.checks;S.dataPath=d.data_path;renderCases();$('setupHint').classList.toggle('hidden',!!d.settings.base_url);}
function showView(name){
 S.view=name;
 ['home','caseLibrary','reportCenter','workspace'].forEach(id=>$(id).classList.toggle('hidden',id!==name));
 document.querySelectorAll('.main-nav [data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
 $('viewCaption').textContent={home:'研析工作台',caseLibrary:'案例管理',reportCenter:'报告与导出',workspace:'8D 研析'}[name]||'Rapid 8D';
 document.body.classList.toggle('in-workspace',name==='workspace');
}
function renderCases(){
 const q=$('caseSearch').value.trim().toLowerCase();
 if(S.case){
  const c=S.case,summary={id:c.id,title:c.title,updated_at:c.updated_at,mode:c.mode,revision:c.revision,complete:c.stages.filter(s=>s.status==='complete').length,report_kind:c.report_kind};
  S.cases=S.cases.filter(item=>item.id!==c.id).concat(summary).sort((a,b)=>b.updated_at.localeCompare(a.updated_at));
 }
 $('caseCount').textContent=S.cases.length;
 const matched=S.cases.filter(c=>c.title.toLowerCase().includes(q));
 $('caseList').innerHTML=matched.map(c=>'<button class="case-item '+(S.case?.id===c.id?'selected':'')+'" data-case="'+esc(c.id)+'" title="'+esc(c.title)+'"><strong>'+esc(c.title)+'</strong><small class="case-mode">'+(c.mode==='import'?'资料成稿':'引导研析')+' · '+c.complete+'/8 已复核</small><small class="case-date">更新于 '+esc(c.updated_at.slice(0,10))+'</small><span class="case-open">打开 →</span></button>').join('')||'<div class="empty-list">'+(q?'没有匹配的案例。':'尚无案例。<br>新建一份 8D 报告。')+'</div>';
 $('totalCases').textContent=S.cases.length;
 $('closedCases').textContent=S.cases.filter(c=>c.report_kind==='closed').length;
 $('activeCases').textContent=S.cases.filter(c=>c.report_kind!=='closed').length;
 $('recentTitle').textContent=q?'搜索结果':'最近案例';
 $('recentCases').innerHTML=matched.length?'<table class="recent-table"><thead><tr><th>案例名称</th><th>阶段进度</th><th>更新时间</th><th>操作</th></tr></thead><tbody>'+matched.slice(0,6).map(c=>'<tr><td><strong title="'+esc(c.title)+'">'+esc(c.title)+'</strong><small>'+({draft:'调查与分析',reviewed_snapshot:'阶段已复核',closed:'已结案'}[c.report_kind]||'调查与分析')+' · '+(c.mode==='import'?'资料成稿':'引导分析')+'</small></td><td class="progress-cell"><span>'+c.complete+' / 8 已复核</span><i class="progress-track"><i class="progress-fill" style="width:'+Math.max(0,Math.min(100,c.complete/8*100))+'%"></i></i></td><td>'+esc(c.updated_at.slice(0,10))+'</td><td><button class="open-case" data-case="'+esc(c.id)+'">打开 →</button></td></tr>').join('')+'</tbody></table>':'<div class="recent-empty"><strong>'+(q?'没有匹配的案例':'尚未创建案例')+'</strong>'+(q?'请调整左侧的搜索关键词。':'选择上方的“引导分析”或“资料成稿”，开始第一份报告。')+'</div>';
 const latest=S.cases[0];$('continueCaseBtn').classList.toggle('hidden',!latest);$('continueCaseBtn').dataset.case=latest?.id||'';
 $('reportCases').innerHTML=S.cases.length?S.cases.map(c=>'<article class="report-case"><span>'+esc(c.id)+'</span><h3>'+esc(c.title)+'</h3><p>'+c.complete+'/8 阶段已复核 · 版本 '+esc(c.revision)+'<br>最后更新 '+esc(c.updated_at.slice(0,10))+'</p><button data-case="'+esc(c.id)+'">打开报告 →</button></article>').join(''):'<div class="report-empty">尚无可导出的报告。先新建案例并完成研析。</div>';
}
function setReportFocus(value){
 $('workspace').classList.toggle('report-focus',value);
 $('focusReportBtn').setAttribute('aria-pressed',String(value));
 $('focusReportBtn').setAttribute('aria-label',value?'返回分析':'展开报告');
 $('focusReportBtn').title=value?'返回分析':'展开报告';
}
async function refreshCase(){if(S.case)S.case=await api('/cases/'+S.case.id);}
async function openCase(id){
 if(S.busy){toast('分析正在进行，请等待当前任务完成。');return;}
 await flushSave();S.case=await api('/cases/'+id);S.stage='D1';S.reportView='report';S.mobilePane='analysis';const pending=await api('/cases/'+id+'/proposals');S.proposal=pending.id?pending:null;S.editing=false;S.selected=new Set(S.case.sources.map(s=>s.id));setReportFocus(false);renderWorkspace();
}
function renderWorkspace(){
 showView('workspace');setMobilePane(S.mobilePane);
 $('caseTitle').textContent=S.case.title;
 $('caseProgress').textContent='阶段复核 '+S.case.stages.filter(s=>s.status==='complete').length+' / 8';
 $('reportKind').textContent={draft:'报告草稿',reviewed_snapshot:'阶段复核报告',closed:'已结案报告'}[S.case.report_kind]||'报告草稿';
 $('caseMeta').textContent=S.case.id+'  ·  '+(S.case.language==='bilingual'?'中英双语报告':S.case.language==='en'?'英文报告':'中文报告')+'  ·  版本 '+S.case.revision;
 $('stageList').innerHTML=S.case.stages.map(s=>'<button class="stage-btn '+(s.id===S.stage?'active ':'')+(s.status==='complete'?'complete ':'')+'status-'+s.status+'" data-stage="'+s.id+'"><span class="stage-num">'+s.id+'</span><span class="stage-name">'+esc(s.title)+'<small>'+stateNames[s.status]+'</small></span></button>').join('');
 $('chatStage').textContent=S.stage+' · '+S.case.stages.find(s=>s.id===S.stage).title;
 const messages=S.case.messages.filter(m=>m.stage===S.stage);
 $('messages').innerHTML=messages.length?messages.map(m=>'<div class="message-label">'+(m.role==='user'?'调查记录':'分析建议')+'</div><div class="message '+(m.role==='user'?'user':'assistant')+'">'+esc(m.text)+'</div>').join(''):'<div class="welcome-message"><strong>从已知事实开始</strong><br>描述问题现象、提供调查记录，或在“资料库”中添加文件。分析建议会在这里显示。</div>';
 $('messages').scrollTop=$('messages').scrollHeight;
 $('proposalBanner').classList.toggle('hidden',!S.proposal);
 renderCases();renderSources();renderGaps();renderReport();
}
function renderReport(){
 const s=S.case.stages.find(x=>x.id===S.stage);
 $('reportHeading').textContent=s.id+' '+s.title;
 $('reportState').textContent=stateNames[s.status]+(s.manual?' · 已手动编辑':'');
 $('reportState').dataset.status=s.status;
 $('reportContent').innerHTML=s.report_markdown?markdown(s.report_markdown):'<div class="empty-report">这一页会随着分析逐步完善。<br>你也可以直接编辑正文，记录已经确认的内容。</div>';
 $('reportContent').classList.toggle('hidden',S.editing);$('reportEditor').classList.toggle('hidden',!S.editing);
 if(!S.dirty)$('reportEditor').value=s.report_markdown;
 $('editBtn').textContent=S.editing?'预览正文':'编辑正文';
 $('paperRevision').textContent='版本 '+S.case.revision+' · 本机保存';
 $('d4Views').classList.toggle('hidden',S.stage!=='D4');
 if(S.stage!=='D4')S.reportView='report';
 setReportView(S.reportView);
}
async function loadFishPreview(){
 try{const response=await api('/cases/'+S.case.id+'/fishbone.svg',undefined,true);if(S.fishURL)URL.revokeObjectURL(S.fishURL);S.fishURL=URL.createObjectURL(await response.blob());$('fishPreview').innerHTML='<img alt="根因鱼骨图" src="'+S.fishURL+'">';}catch(e){toast(e.message,true);}
}
function tab(name){document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));['chat','sources','gaps'].forEach(n=>$(n+'Pane').classList.toggle('hidden',n!==name));}
function setReportView(name){
 S.reportView=S.stage==='D4'&&name==='fish'?'fish':'report';
 document.querySelectorAll('[data-report-view]').forEach(b=>b.classList.toggle('active',b.dataset.reportView===S.reportView));
 $('reportDocument').classList.toggle('hidden',S.reportView!=='report');$('fishWorkspace').classList.toggle('hidden',S.reportView!=='fish');
 $('editBtn').classList.toggle('hidden',S.reportView!=='report');$('reviewBtn').classList.toggle('hidden',S.reportView!=='report');
 if(S.reportView==='fish')loadFishPreview();
}
function setMobilePane(name){S.mobilePane=name==='report'?'report':'analysis';$('workspace').classList.toggle('mobile-analysis',S.mobilePane==='analysis');$('workspace').classList.toggle('mobile-report',S.mobilePane==='report');document.querySelectorAll('[data-mobile-pane]').forEach(b=>b.classList.toggle('active',b.dataset.mobilePane===S.mobilePane));}
function renderSources(){
 $('sourceCount').textContent=S.case.sources.length;
 $('sources').innerHTML=S.case.sources.map(src=>'<div class="source-card"><label><input type="checkbox" data-source="'+src.id+'" '+(S.selected.has(src.id)?'checked':'')+'><span>'+esc(src.name)+'</span></label><small>'+esc(src.id)+' · '+src.char_count+' 字符 · '+esc(src.coverage)+'</small>'+(src.warnings||[]).map(w=>'<p>'+esc(w)+'</p>').join('')+'<details><summary>查看提取内容</summary><pre>'+esc(src.chunks.map(c=>'['+c.locator+']\n'+c.text).join('\n\n'))+'</pre></details></div>').join('')||'<p class="hint">添加的资料会保留来源和读取范围。</p>';
}
function renderGaps(){
 const gaps=S.case.gaps.filter(g=>!g.resolved),conflicts=S.case.conflicts.filter(c=>!c.resolution);
 $('gapCount').textContent=gaps.length+conflicts.length;
 $('gaps').innerHTML=gaps.map(g=>'<div class="gap-card"><strong>'+esc(g.stage||'全报告')+' · '+esc(g.description)+'</strong><p>'+esc(g.suggested_next_step||g.impact||'需要补充证据。')+'</p><button data-resolve="'+esc(g.id)+'" data-kind="gaps">记录处理依据</button></div>').join('')+conflicts.map(c=>'<div class="gap-card"><strong>资料冲突</strong><p>'+esc(c.description)+'</p><button data-resolve="'+esc(c.id)+'" data-kind="conflicts">记录处理依据</button></div>').join('')||'<p class="hint">尚无待办记录。生成分析后会在这里列出需要补充的证据。</p>';
}
function scheduleSave(){S.dirty=true;$('saveState').textContent='编辑中…';clearTimeout(S.saveTimer);S.saveTimer=setTimeout(()=>guard(flushSave)(),900);}
async function flushSave(){
 clearTimeout(S.saveTimer);
 if(!S.case||!S.dirty)return S.saveChain;
 const cid=S.case.id,sid=S.stage,text=$('reportEditor').value;S.dirty=false;$('saveState').textContent='正在保存…';
 S.saveChain=S.saveChain.catch(()=>{}).then(async()=>{
  try{const c=await api('/cases/'+cid+'/edit',{revision:S.case.revision,stage:sid,text});if(S.case?.id===cid){S.case=c;$('caseMeta').textContent=c.id+' · 版本 '+c.revision;$('saveState').textContent=S.dirty?'编辑中…':'已保存';}}
  catch(e){S.dirty=true;$('saveState').textContent='未保存';throw e;}
 });return S.saveChain;
}
function newCase(mode='guided'){
 modal('新建质量问题案例',field('案例名称','newTitle','','text','例如：某产品尺寸超差 / 客户反馈外观异常')+'<label class="form-field">开始方式<select id="newMode"><option value="guided">引导分析 · 一步一步对话</option><option value="import">资料成稿 · 整理已有过程</option></select></label><label class="form-field">报告语言<select id="newLanguage"><option value="zh">中文</option><option value="bilingual">中文 + English 逐段对照</option><option value="en">English</option></select></label><div class="modal-actions"><button class="primary" id="createCase">创建案例 →</button></div>');
 $('newMode').value=mode;$('newTitle').focus();
 $('createCase').onclick=guard(async()=>{await flushSave();S.case=await api('/cases',{title:$('newTitle').value,mode:$('newMode').value,language:$('newLanguage').value});S.stage='D1';S.selected=new Set();S.proposal=null;S.editing=false;setReportFocus(false);closeModal();await bootstrap();renderWorkspace();tab(S.case.mode==='import'?'sources':'chat');});
}
async function addPaste(){
 await flushSave();const text=$('pasteText').value.trim();if(!text)return toast('请先粘贴资料。');
 S.case=await api('/cases/'+S.case.id+'/source',{revision:S.case.revision,text,name:'调查资料 '+(S.case.sources.length+1)});
 S.selected.add(S.case.sources.at(-1).id);$('pasteText').value='';renderWorkspace();tab('sources');toast('文字资料已保存。');
}
async function uploadFiles(){
 await flushSave();
 for(const file of $('files').files){
  if(file.size>20*1024*1024){toast(file.name+' 超过20 MB。',true);continue;}
  const data=await new Promise((resolve,reject)=>{let r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.onerror=reject;r.readAsDataURL(file);});
  S.case=await api('/cases/'+S.case.id+'/upload',{revision:S.case.revision,name:file.name,data});
  S.selected.add(S.case.sources.at(-1).id);
 }
 $('files').value='';renderWorkspace();tab('sources');toast('文件已读取，请核对提取范围。');
}
function setBusy(value,message='正在分析资料…'){S.busy=value;['sendBtn','importBtn','pasteBtn','files','reviewBtn','fishBtn','newBtn'].forEach(id=>$(id).disabled=value);$('jobStatus').classList.toggle('hidden',!value);$('jobStatus').textContent=message;}
async function runAnalysis(mode){
 if(S.busy)return;await flushSave();
 if(!S.settings.base_url){await settings();toast('请先配置模型接口。');return;}
 const message=mode==='guided'?$('message').value.trim():'';
 if(mode==='guided'&&!message&&!S.case.sources.length)return toast('请先描述问题或添加资料。');
 const cid=S.case.id;
 setBusy(true);
 try{
  const job=await api('/cases/'+cid+'/analyze',{revision:S.case.revision,stage:S.stage,mode,message,source_ids:[...S.selected]});
  const knownSources=new Set(S.case.sources.map(x=>x.id));$('message').value='';await refreshCase();S.case.sources.filter(x=>!knownSources.has(x.id)).forEach(x=>S.selected.add(x.id));renderWorkspace();tab('chat');
  while(true){
   await new Promise(resolve=>setTimeout(resolve,1300));
   const result=await api('/jobs/'+job.job_id);
   if(result.status==='error')throw Error(result.message);
   if(result.status==='done'){
    await refreshCase();S.proposal=await api('/cases/'+cid+'/proposal/'+result.proposal_id);renderWorkspace();toast('分析建议已生成，请对比后采用。');break;
   }
  }
 }finally{setBusy(false);}
}
async function showProposal(){
 await flushSave();const p=S.proposal;if(!p)return;
 modal('对比分析建议','<p class="modal-note">'+esc(p.data.summary||'勾选需要采用的阶段。未勾选的正文保持原样。')+'</p>'+p.data.stages.map(s=>{
  const original=S.case.stages.find(x=>x.id===s.id);
  return '<section class="proposal-stage"><label class="check-row"><input type="checkbox" data-choose="'+s.id+'" '+(!original.manual?'checked':'')+'><strong>'+s.id+' '+esc(original.title)+'</strong>'+(original.manual?'<span class="badge">有手动修改，默认保留</span>':'')+'</label><div class="compare"><div><div class="compare-label">当前内容</div><div class="markdown">'+(markdown(original.report_markdown)||'尚未填写')+'</div></div><div><div class="compare-label">AI 建议（待复核）</div><div class="markdown">'+markdown(s.report_markdown)+'</div></div></div></section>';
 }).join('')+'<p class="modal-note">采用 D4 时会同步更新鱼骨与根因候选。所有建议仍需证据与阶段复核。</p><div class="modal-actions"><button id="keepOriginal">保留原内容</button><button class="primary" id="acceptProposal">采用勾选阶段</button></div>',true);
 $('keepOriginal').onclick=closeModal;
 $('acceptProposal').onclick=guard(async()=>{const chosen=[...document.querySelectorAll('[data-choose]:checked')].map(x=>x.dataset.choose);S.case=await api('/cases/'+S.case.id+'/accept',{revision:S.case.revision,proposal_id:p.id,stages:chosen});S.proposal=null;closeModal();renderWorkspace();await bootstrap();toast('已采用选中阶段，原版本已保留。');});
}
async function settings(){
 const cfg=await api('/settings');
 modal('模型设置','<p class="modal-note">连接你选择的 Chat Completions 兼容接口。分析时发送当前报告、已有分析记录和勾选的资料；密钥使用当前Windows账户保护。</p>'+field('接口地址','apiBase',cfg.base_url,'url','填写基础地址，例如服务提供的 https://…/v1，也可填写完整 /chat/completions 地址。')+field('模型名称','apiModel',cfg.model)+field('API 密钥','apiKey','','password',cfg.key_set?'已保存密钥。留空表示继续使用；输入新值可替换。':'密钥仅保存在本机；无需在对话中提供。')+'<details><summary class="modal-note">高级选项</summary>'+field('最大输出长度','apiMax',cfg.max_tokens,'number')+'<label class="form-field">输出长度参数<select id="tokenParameter"><option value="max_tokens">max_tokens（常用兼容接口）</option><option value="max_completion_tokens">max_completion_tokens</option></select></label><label class="check-row"><input id="jsonMode" type="checkbox">服务支持 JSON 模式时启用</label><label class="check-row"><input id="allowHttp" type="checkbox">允许向指定内网 HTTP 地址发送资料（未加密）</label><label class="check-row"><input id="clearKey" type="checkbox">清除已保存密钥</label></details><p class="modal-note">数据目录：'+esc(S.dataPath||'')+'</p><div class="modal-actions"><button id="testModel">保存并测试连接</button><button class="primary" id="saveSettings">保存设置</button></div>');
 $('tokenParameter').value=cfg.token_parameter||'max_tokens';$('jsonMode').checked=cfg.json_mode;$('allowHttp').checked=!!cfg.allow_http;
 async function save(){S.settings=await api('/settings',{base_url:$('apiBase').value,model:$('apiModel').value,api_key:$('apiKey').value,max_tokens:Number($('apiMax').value),token_parameter:$('tokenParameter').value,json_mode:$('jsonMode').checked,allow_http:$('allowHttp').checked,clear_key:$('clearKey').checked});$('apiKey').value='';$('setupHint').classList.add('hidden');}
 $('saveSettings').onclick=guard(async()=>{await save();closeModal();toast('模型设置已保存。');});
 $('testModel').onclick=guard(async()=>{await save();$('testModel').disabled=true;$('testModel').textContent='正在连接…';try{await api('/test-model',{});toast('连接成功，模型已返回响应。');}finally{$('testModel').disabled=false;$('testModel').textContent='保存并测试连接';}});
}
async function review(){
 await flushSave();const sid=S.stage;const roots=S.case.root_causes;
 modal(sid+' 阶段复核','<p class="modal-note">复核不会替代实际调查或试验。缺口解决后，由你确认当前阶段的关键事实和证据。</p>'+S.checks[sid].map((c,i)=>'<label class="check-row"><input type="checkbox" data-check="'+i+'">'+esc(c)+'</label>').join('')+
 (sid==='D4'?'<h3>根因记录</h3>'+roots.map(r=>'<div class="source-card"><strong>'+esc(r.statement)+'</strong><p>'+esc(r.verification_record||'缺少实际验证记录')+'</p><small>'+esc(r.verification)+' · '+esc((r.source_refs||[]).map(x=>x.source_id).join(', '))+'</small></div>').join('')+'<label class="check-row"><input id="confirmRoots" type="checkbox">我已核对根因和对应的验证记录</label><label class="check-row"><input id="naEscape" type="checkbox">逃逸分析不适用（须在说明中写明依据）</label>':'')+
 field('复核人','reviewer')+'<label class="form-field">复核与证据说明<textarea id="reviewNote" rows="4" placeholder="记录复核依据、适用范围或授权信息…"></textarea></label><div class="modal-actions"><button class="primary" id="confirmReview">'+(sid==='D8'?'确认复核并结案':'确认阶段复核')+'</button></div>');
 $('confirmReview').onclick=guard(async()=>{S.case=await api('/cases/'+S.case.id+'/review',{revision:S.case.revision,stage:sid,reviewer:$('reviewer').value,note:$('reviewNote').value,checks:[...document.querySelectorAll('[data-check]')].map(x=>x.checked),roots_confirmed:$('confirmRoots')?.checked||false,na_escape:$('naEscape')?.checked||false});closeModal();renderWorkspace();await bootstrap();toast('阶段复核已记录。');});
}
async function resolveItem(id,kind){
 modal('记录处理依据','<p class="modal-note">请说明新增了什么证据、如何解决该缺口或冲突。涉及原因变化时，还需修改对应根因和报告内容。</p><textarea id="resolveNote" rows="6"></textarea><div class="modal-actions"><button id="confirmResolve" class="primary">保存处理记录</button></div>');
 $('confirmResolve').onclick=guard(async()=>{await flushSave();S.case=await api('/cases/'+S.case.id+'/resolve',{revision:S.case.revision,id,kind,note:$('resolveNote').value});closeModal();renderWorkspace();tab('gaps');});
}
async function historyView(){
 await flushSave();const list=await api('/cases/'+S.case.id+'/history');
 modal('历史版本','<p class="modal-note">每次编辑与采用建议都会保存先前版本。恢复后需重新复核；当前内容也会保留在历史中。</p>'+list.map(v=>'<div class="history-row"><div><p>版本 '+v.revision+' · '+esc(v.reason)+'</p><small>'+esc(v.at)+'</small></div><button data-version="'+v.id+'">查看与恢复</button></div>').join('')+(list.length?'':'<p>当前还没有历史版本。</p>'));
}
async function previewVersion(id){
 const v=await api('/cases/'+S.case.id+'/history/'+id);
 modal('版本 '+v.revision+' · '+v.title,v.stages.filter(s=>s.report_markdown).map(s=>'<h3>'+s.id+' '+esc(s.title)+'</h3><div class="markdown">'+markdown(s.report_markdown)+'</div>').join('')+'<div class="modal-actions"><button id="restoreVersion" class="primary">恢复这个版本（待复核）</button></div>',true);
 $('restoreVersion').onclick=guard(async()=>{S.case=await api('/cases/'+S.case.id+'/restore',{revision:S.case.revision,version_id:id});S.proposal=null;closeModal();renderWorkspace();toast('版本已恢复，当前原内容保存在历史中。');});
}
async function download(kind){
 await flushSave();toast('正在生成 '+(kind==='docx'?'Word':'PDF')+' 报告…');
 const response=await api('/cases/'+S.case.id+'/export',{format:kind},true);
 const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='Rapid8D-'+S.case.id+'-r'+S.case.revision+'.'+kind;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);toast('报告已导出，并在本机保留版本快照。');
}

let fishDraft=null,rootDraft=null;
function newId(prefix){return prefix+crypto.randomUUID().replaceAll('-','').slice(0,8);}
function flat(nodes){return nodes.flatMap(n=>[n,...flat(n.children||[])]);}
function findNode(id){return fishDraft.categories.flatMap(c=>flat(c.causes)).find(n=>n.id===id);}
function sourceOptions(selected){return '<option value="">未关联来源</option>'+S.case.sources.map(s=>'<option value="'+s.id+'" '+(selected===s.id?'selected':'')+'>'+esc(s.name)+'</option>').join('');}
function collectFish(){
 fishDraft.problem_statement=$('fishProblem').value;
 document.querySelectorAll('[data-nlabel]').forEach(el=>{findNode(el.dataset.nlabel).label=el.value;});
 document.querySelectorAll('[data-nstatus]').forEach(el=>{findNode(el.dataset.nstatus).status=el.value;});
 document.querySelectorAll('[data-nsource]').forEach(el=>{const n=findNode(el.dataset.nsource);if((n.source_refs?.[0]?.source_id||'')!==el.value)n.source_refs=el.value?[{source_id:el.value,locator:null,quote:null}]:[];});
 document.querySelectorAll('[data-nroot]').forEach(el=>{const n=findNode(el.dataset.nroot);if((n.root_cause_refs?.[0]||'')!==el.value)n.root_cause_refs=el.value?[el.value]:[];});
 document.querySelectorAll('[data-nnote]').forEach(el=>{findNode(el.dataset.nnote).verification_note=el.value;});
 document.querySelectorAll('[data-rfield]').forEach(el=>{rootDraft.find(r=>r.id===el.dataset.rid)[el.dataset.rfield]=el.value;});
 document.querySelectorAll('[data-rsource]').forEach(el=>{const r=rootDraft.find(r=>r.id===el.dataset.rsource);if((r.source_refs?.[0]?.source_id||'')!==el.value)r.source_refs=el.value?[{source_id:el.value,locator:null,quote:null}]:[];});
}
function nodeRows(nodes,depth=0){
 return nodes.map(n=>'<div class="fish-row" style="margin-left:'+Math.min(depth,3)*14+'px"><small>'+esc(n.id)+'</small><input data-nlabel="'+n.id+'" value="'+esc(n.label)+'" aria-label="原因描述"><select data-nstatus="'+n.id+'" aria-label="原因状态">'+Object.entries(evidenceNames).map(([k,v])=>'<option value="'+k+'" '+(n.status===k?'selected':'')+'>'+v+'</option>').join('')+'</select><select data-nsource="'+n.id+'" aria-label="原因来源">'+sourceOptions(n.source_refs?.[0]?.source_id)+'</select><button data-remove-node="'+n.id+'" aria-label="移除原因">×</button></div><div class="fish-row" style="margin-left:'+Math.min(depth,3)*14+'px"><button class="subtle" data-child="'+n.id+'">＋ 子因</button><input data-nnote="'+n.id+'" value="'+esc(n.verification_note||'')+'" placeholder="验证说明（已验证节点需来源及根因关联或验证说明）"><select data-nroot="'+n.id+'" aria-label="关联根因" style="grid-column:span 2"><option value="">尚未形成根因</option>'+rootDraft.map(r=>'<option value="'+r.id+'" '+(n.root_cause_refs?.[0]===r.id?'selected':'')+'>'+esc(r.id+' '+r.statement.slice(0,35))+'</option>').join('')+'</select></div>'+nodeRows(n.children||[],depth+1)).join('');
}
function renderFishEditor(){
 const body='<p class="modal-note">鱼骨组织候选原因；状态由证据决定。填写根因记录后，再到 D4 做阶段复核。完整原因保存在表格中，图中长标签会缩短显示。</p>'+field('问题陈述','fishProblem',fishDraft.problem_statement||'')+
 fishDraft.categories.map(c=>'<div class="fish-category"><h3>'+esc(c.label)+'</h3>'+nodeRows(c.causes)+'<button data-add-cause="'+c.id+'">＋ 添加原因</button></div>').join('')+
 '<div class="root-grid">'+field('新分类名称','categoryName')+'<div><button id="addCategory" style="margin-top:23px">＋ 添加分类</button></div></div><h3>根因记录</h3><p class="modal-note">这里区分产生和逃逸根因。用户认可某个解释，不等于已经验证。</p>'+
 rootDraft.map(r=>'<div class="root-card"><small>'+esc(r.id)+'</small><div class="root-grid"><label class="form-field">分析线<select data-rid="'+r.id+'" data-rfield="kind"><option value="occurrence" '+(r.kind==='occurrence'?'selected':'')+'>产生根因</option><option value="escape" '+(r.kind==='escape'?'selected':'')+'>逃逸根因</option></select></label><label class="form-field">验证状态<select data-rid="'+r.id+'" data-rfield="verification">'+Object.entries({unverified:'未验证',supported:'有支持',verified:'已验证',refuted:'已排除',inconclusive:'不确定'}).map(([k,v])=>'<option value="'+k+'" '+(r.verification===k?'selected':'')+'>'+v+'</option>').join('')+'</select></label></div><label class="form-field">根因陈述<input data-rid="'+r.id+'" data-rfield="statement" value="'+esc(r.statement||'')+'"></label><label class="form-field">实际验证记录<textarea data-rid="'+r.id+'" data-rfield="verification_record" rows="3">'+esc(typeof r.verification_record==='object'&&r.verification_record?JSON.stringify(r.verification_record):r.verification_record||'')+'</textarea></label><label class="form-field">关联来源<select data-rsource="'+r.id+'">'+sourceOptions(r.source_refs?.[0]?.source_id)+'</select></label><button data-remove-root="'+r.id+'">移除这条根因记录</button></div>').join('')+
 '<button id="addRoot" style="margin-top:14px">＋ 添加根因记录</button><div class="modal-actions"><button id="saveFish" class="primary">保存鱼骨与根因</button></div>';
 modal('D4 鱼骨图与根因编辑',body,true);
 $('addCategory').onclick=()=>{collectFish();const name=$('categoryName').value.trim();if(!name)return toast('请输入分类名称。');fishDraft.categories.push({id:newId('M'),label:name,causes:[]});renderFishEditor();};
 $('addRoot').onclick=()=>{collectFish();rootDraft.push({id:newId('RC-O'),kind:'occurrence',statement:'',verification:'unverified',confirmation:'unreviewed',source_refs:[],verification_record:''});renderFishEditor();};
 $('saveFish').onclick=guard(async()=>{collectFish();S.case=await api('/cases/'+S.case.id+'/analysis',{revision:S.case.revision,fishbone:fishDraft,root_causes:rootDraft});closeModal();renderWorkspace();toast('鱼骨与根因记录已保存，D4及相关结论需复核。');});
}
async function fishEditor(){
 await flushSave();fishDraft=structuredClone(S.case.fishbone);rootDraft=structuredClone(S.case.root_causes);
 if(!fishDraft.categories.length)fishDraft.categories=['人','机','料','法','测','环'].map(label=>({id:newId('M'),label,causes:[]}));
 renderFishEditor();
}
function removeNode(nodes,id){return nodes.filter(n=>n.id!==id).map(n=>({...n,children:removeNode(n.children||[],id)}));}
function freshNode(){return {id:newId('H'),label:'新原因',status:'suspected',source_refs:[],root_cause_refs:[],children:[]};}
document.addEventListener('click',guard(async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(b.dataset.new)return newCase(b.dataset.new);
 if(b.dataset.case)return openCase(b.dataset.case);
 if(b.dataset.stage){await flushSave();S.stage=b.dataset.stage;S.reportView='report';S.editing=false;renderWorkspace();return;}
 if(b.dataset.tab)return tab(b.dataset.tab);
 if(b.dataset.reportView)return setReportView(b.dataset.reportView);
 if(b.dataset.mobilePane)return setMobilePane(b.dataset.mobilePane);
 if(b.dataset.resolve)return resolveItem(b.dataset.resolve,b.dataset.kind);
 if(b.dataset.version)return previewVersion(b.dataset.version);
 if(b.dataset.addCause){collectFish();fishDraft.categories.find(c=>c.id===b.dataset.addCause).causes.push(freshNode());renderFishEditor();return;}
 if(b.dataset.child){collectFish();findNode(b.dataset.child).children.push(freshNode());renderFishEditor();return;}
 if(b.dataset.removeNode){collectFish();fishDraft.categories.forEach(c=>c.causes=removeNode(c.causes,b.dataset.removeNode));renderFishEditor();return;}
 if(b.dataset.removeRoot){collectFish();rootDraft=rootDraft.filter(r=>r.id!==b.dataset.removeRoot);fishDraft.categories.flatMap(c=>flat(c.causes)).forEach(n=>n.root_cause_refs=(n.root_cause_refs||[]).filter(x=>x!==b.dataset.removeRoot));renderFishEditor();return;}
}));
document.addEventListener('change',e=>{if(e.target.dataset.source){if(e.target.checked)S.selected.add(e.target.dataset.source);else S.selected.delete(e.target.dataset.source);}});
$('homeBtn').onclick=guard(async()=>{if(S.busy)return toast('请等待当前分析完成。');await flushSave();showView('home');await bootstrap();});
$('dashboardBtn').onclick=$('homeBtn').onclick;
$('caseLibraryBtn').onclick=guard(async()=>{await flushSave();showView('caseLibrary');renderCases();});
$('reportCenterBtn').onclick=guard(async()=>{await flushSave();showView('reportCenter');renderCases();});
$('viewAllCases').onclick=()=>showView('caseLibrary');
$('setupModelBtn').onclick=guard(settings);
$('focusReportBtn').onclick=()=>setReportFocus(!$('workspace').classList.contains('report-focus'));
$('newBtn').onclick=()=>newCase();
$('settingsBtn').onclick=guard(settings);
$('caseSearch').oninput=renderCases;
$('closeModal').onclick=closeModal;
$('pasteBtn').onclick=guard(addPaste);
$('files').onchange=guard(uploadFiles);
$('sendBtn').onclick=guard(()=>runAnalysis('guided'));
$('importBtn').onclick=guard(()=>runAnalysis('import'));
$('message').onkeydown=e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter')guard(()=>runAnalysis('guided'))();};
$('proposalBtn').onclick=guard(showProposal);
$('reviewBtn').onclick=guard(review);
$('fishBtn').onclick=guard(fishEditor);
$('historyBtn').onclick=guard(historyView);
$('wordBtn').onclick=guard(()=>download('docx'));
$('pdfBtn').onclick=guard(()=>download('pdf'));
$('editBtn').onclick=guard(async()=>{await flushSave();S.editing=!S.editing;renderReport();if(S.editing)$('reportEditor').focus();});
$('reportEditor').oninput=scheduleSave;
$('quitBtn').onclick=guard(async()=>{await flushSave();await api('/quit',{});document.body.innerHTML='<main style="padding:70px"><h1>已保存并退出</h1><p>可以关闭此窗口。下次双击 Rapid 8D 继续。</p></main>';});
setInterval(()=>api('/ping',{}).catch(()=>{}),20000);
window.addEventListener('beforeunload',e=>{if(S.dirty){e.preventDefault();e.returnValue='';}});
window.addEventListener('pagehide',()=>{fetch('/api/disconnect',{method:'POST',headers:{'X-Rapid-Token':token,'Content-Type':'application/json'},body:'{}',keepalive:true}).catch(()=>{});});
guard(async()=>{await bootstrap();await api('/ping',{});})().catch(()=>{});
