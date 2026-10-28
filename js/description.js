import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const names=['source','image','folder','max_images','provider','model','base_url','description','approved_description'];
function installStyle() {
  if(document.getElementById('muse-ref-description-style'))return;
  const style=document.createElement('style');style.id='muse-ref-description-style';
  style.textContent=`
  .mrd-panel{box-sizing:border-box;width:420px;padding:14px;background:#151e2b;color:#e5e9f1;font:13px/1.4 sans-serif;border:1px solid #38485f;border-radius:10px;display:flex;flex-direction:column;gap:10px}
  .mrd-panel button,.mrd-panel select,.mrd-panel input,.mrd-panel textarea{box-sizing:border-box;border:1px solid #394b64;border-radius:6px;background:#0d1520;color:#e5e9f1;padding:8px;font:inherit;width:100%}
  .mrd-panel button{background:#293b56;cursor:pointer;font-weight:600}
  .mrd-panel button:hover,.mrd-panel select:hover{border-color:#d57ca8;background:#48304a}
  .mrd-panel button.mrd-analyze{background:#a64e7c;border-color:#c773a1}
  .mrd-panel button:disabled{opacity:.5;cursor:wait}
  .mrd-panel input:focus,.mrd-panel textarea:focus,.mrd-panel select:focus{outline:1px solid #d57ca8}
  .mrd-panel img{width:100%;height:210px;object-fit:contain;background:#0b111a;border-radius:6px}
  .mrd-panel textarea{height:140px;resize:vertical}
  .mrd-panel label{display:flex;flex-direction:column;gap:4px;color:#bbc7d9}
  .mrd-panel summary{cursor:pointer;color:#b6a6d6}
  .mrd-panel details label{margin-top:8px}
  .mrd-panel small{color:#aebdd2}
  .mrd-panel{height:auto!important;min-height:0!important;flex-shrink:0;overflow:visible}
  .mrd-panel>*{flex-shrink:0}
  `;document.head.appendChild(style);
}
function build(node){
  installStyle();
  // This node owns its image preview. Native previews otherwise paint behind
  // the DOM panel after the image-upload extension asynchronously loads them.
  node.onDrawBackground=function(){this.imgs=null;};
  node.imgs=null;
  const w=name=>node.widgets.find(x=>x.name===name);
  for(const item of node.widgets){
    if(names.includes(item.name)||item.name==='upload'){
      item.hidden=true;item.computeSize=()=>[0,-4];item.draw=()=>{};
      if(item.element)item.element.style.display='none';
    }
  }
  const root=document.createElement('div');root.className='mrd-panel';
  const el=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;};
  const preview=el('img');preview.alt='Character reference';root.append(preview);
  const picker=el('select');root.append(picker);
  const upload=el('button','Upload character image');root.append(upload);
  const file=el('input');file.type='file';file.accept='image/png,image/jpeg,image/webp,image/bmp';file.style.display='none';root.append(file);
  const provider=el('select');
  for(const [value,title] of [['ollama','Ollama'],['gemini','Google Gemini'],['openai','OpenAI'],['lmstudio','LM Studio'],['custom','Custom']]){const o=el('option',title);o.value=value;provider.append(o);}
  const providerLabel=el('label','Analyze with');providerLabel.append(provider);root.append(providerLabel);
  const advanced=el('details');advanced.append(el('summary','Connection settings'));
  const model=el('input'),base=el('input');model.placeholder='Provider default';base.placeholder='Provider default';
  for(const [name,input] of [['Vision model',model],['Server URL',base]]){const label=el('label',name);label.append(input);advanced.append(label);}
  root.append(advanced);
  const analyze=el('button','Analyze character');analyze.className='mrd-analyze';root.append(analyze);
  const label=el('label','Character description — editable');const description=el('textarea');description.placeholder='Click Analyze character to describe this image.';label.append(description);root.append(label);
  const proceed=el('button','Continue to create RefMod');proceed.className='mrd-analyze';root.append(proceed);
  const status=el('small','Connect description to Create H3 RefMod.');root.append(status);
  const show=text=>{status.textContent=text;node.setDirtyCanvas?.(true,true);};
  const put=(name,value)=>{if(name!=='approved_description'&&w('approved_description'))w('approved_description').value='';if(w(name)){w(name).value=value;}node.setDirtyCanvas?.(true,true);};
  const snapshot=()=>({image:w('image')?.value,provider:w('provider')?.value,model:w('model')?.value||'',base_url:w('base_url')?.value||''});
  function sync(){
    put('source','Uploaded image');put('folder','');put('max_images',1);
    picker.replaceChildren();
    const current=w('image')?.value || '';
    const values=[...new Set([...(w('image')?.options?.values||[]),current])];
    for(const value of values){const option=el('option',value||'Choose an image');option.value=value;picker.append(option);}
    picker.value=current;provider.value=w('provider')?.value||'ollama';model.value=w('model')?.value||'';base.value=w('base_url')?.value||'';description.value=w('description')?.value||'';
    if(current){const path=current.replace(/\\/g,'/');const i=path.lastIndexOf('/');preview.src=api.apiURL('/view?'+new URLSearchParams({filename:path.slice(i+1),subfolder:i<0?'':path.slice(0,i),type:'input'}));preview.hidden=false;}else{preview.removeAttribute('src');preview.hidden=true;}
    analyze.textContent=description.value.trim()?'Reanalyze character':'Analyze character';
    proceed.disabled=!description.value.trim();
    node.imgs=null;node.setDirtyCanvas?.(true,true);
  }
  picker.onchange=()=>{put('image',picker.value);sync();};
  provider.onchange=()=>{put('provider',provider.value);put('model','');put('base_url','');model.value='';base.value='';};
  model.oninput=()=>put('model',model.value);base.oninput=()=>put('base_url',base.value);description.oninput=()=>{put('description',description.value);proceed.disabled=!description.value.trim();};
  upload.onclick=()=>file.click();
  file.onchange=async()=>{
    const selected=file.files?.[0];if(!selected)return;
    upload.disabled=true;show('Uploading image…');
    try{const body=new FormData();body.append('image',selected);body.append('subfolder','muse_refmod_description');
      const response=await api.fetchApi('/upload/image',{method:'POST',body});if(!response.ok)throw Error('Upload failed');
      const data=await response.json();const path=data.subfolder?`${data.subfolder}/${data.name}`:data.name;
      if(w('image')?.options?.values&&!w('image').options.values.includes(path))w('image').options.values.push(path);
      put('image',path);sync();show('Image ready. Click Analyze character.');
    }catch(error){show(error.message);}finally{upload.disabled=false;file.value='';}
  };
  analyze.onclick=async()=>{
    if(analyze.disabled)return;
    const request=snapshot(),previous=w('description').value;
    put('approved_description','');proceed.disabled=true;analyze.disabled=true;show('Analyzing character…');
    try{const response=await api.fetchApi('/muse_refmod_description/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request)});
      const data=await response.json();if(!response.ok||data.error)throw Error(data.error||'Analysis failed');
      if(JSON.stringify(request)!==JSON.stringify(snapshot())||previous!==w('description').value){show('Inputs changed. Click Analyze again.');return;}
      put('description',data.description);description.value=data.description;analyze.textContent='Reanalyze character';show('Review or edit the description, then Continue to create RefMod.');
    }catch(error){show(error.message);}finally{analyze.disabled=false;proceed.disabled=!description.value.trim();}
  };
  proceed.onclick=async()=>{
    if(proceed.disabled||!description.value.trim())return;
    put('description',description.value);put('approved_description',description.value.trim());
    proceed.disabled=true;show('Sending approved description to Create H3 RefMod…');
    try{await app.queuePrompt(0,1);}catch(error){put('approved_description','');show('Could not queue: '+error.message);}
    finally{proceed.disabled=!description.value.trim();}
  };
  const ui=node.addDOMWidget('mrd_ui','mrd_ui',root,{serialize:false,hideOnZoom:false});
  let height=650;
  ui.computeSize=()=>[440,height];
  const resize=()=>{const measured=Math.ceil(root.offsetHeight);if(measured>0&&measured!==height){height=measured;node.setSize([440,height+50]);node.setDirtyCanvas?.(true,true);}};
  const observer=new ResizeObserver(resize);observer.observe(root);
  node._mrd={sync,dispose:()=>observer.disconnect()};sync();node.color='#33234b';node.bgcolor='#151c29';node.size=[440,700];
}
app.registerExtension({name:'Muse.RefModDescription',async beforeRegisterNodeDef(nodeType,nodeData){
  if(nodeData.name!=='MuseRefModDescription')return;
  const created=nodeType.prototype.onNodeCreated,configured=nodeType.prototype.onConfigure,removed=nodeType.prototype.onRemoved;
  nodeType.prototype.onNodeCreated=function(){const r=created?.apply(this,arguments);build(this);return r;};
  nodeType.prototype.onConfigure=function(){const r=configured?.apply(this,arguments);this._mrd?.sync();return r;};
  nodeType.prototype.onRemoved=function(){this._mrd?.dispose();return removed?.apply(this,arguments);};
}});
