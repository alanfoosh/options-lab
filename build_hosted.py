#!/usr/bin/env python3
"""Build the standalone hosted page (index.html) from the claude.ai artifact source (leap-lab.html).
Usage: python3 build_hosted.py leap-lab.html index.html [version number, matches the artifact version]
The artifact page talks to claude.ai's runtime (window.claude); the hosted page gets a small shim that
provides the same calls: Alpha Vantage over its web API with the user's own key, per-user saved data in Supabase,
and file downloads. The main page code is left untouched apart from a few text replacements below."""
import sys,re
src,dst=sys.argv[1],sys.argv[2]
VERSION=sys.argv[3] if len(sys.argv)>3 else '30'
import datetime
BUILT=datetime.date.today().isoformat()
s=open(src,encoding='utf8').read()

SB_URL="https://zngsukxhmfqacwzvzvnt.supabase.co"
SB_KEY="sb_publishable_5d-c0IOZGajoHC93Cc5AQg_nzVuF8mP"

def rep(a,b,count=1):
    global s
    assert s.count(a)>=1,a[:70]
    s=s.replace(a,b) if count==0 else s.replace(a,b,count)

# text that only makes sense inside claude.ai
rep('case "needs_reauth":return "Your Alpha Vantage connection has expired. Reconnect it in claude.ai Settings, Connectors, then refresh.";',
    'case "needs_reauth":return "Add your Alpha Vantage key in the Account box at the top, then press Refresh.";')
rep('case "server_not_connected":return "Alpha Vantage isn\'t connected. Add it in claude.ai Settings, Connectors.";','case "server_not_connected":return "Alpha Vantage isn\'t reachable. Check your connection.";')
rep('const AV_PER_MIN=72;','const AV_PER_MIN=(()=>{try{const n=+localStorage.getItem(KEY+"-avrate");return n>0?Math.max(1,n-3):72}catch(e){return 72}})();')
rep('avLimitText=t=>/rate limit|per minute|call frequency|requests per|premium endpoint|higher API call/i.test(t||"")',
    'avLimitText=t=>/rate limit|per minute|call frequency|requests per|higher API call/i.test(t||"")')
rep('This page isn\'t allowed to use Alpha Vantage. Allow it in the page\'s permissions, then refresh.','Alpha Vantage refused this request. Check your key in the Account box.')

account='''
<section class="panel" id="acct" aria-label="Account and Alpha Vantage key">
  <div style="font-weight:600;margin-bottom:8px">Account</div>
  <div class="grid2">
    <label class="f">Your Alpha Vantage key<input type="password" id="avKey" autocomplete="off" spellcheck="false" placeholder="paste your key"></label>
    <label class="f">Calls per minute your key allows<select id="avRate"><option value="5">5 (free key)</option><option value="75">75 (premium)</option><option value="150">150</option><option value="300">300</option><option value="600">600</option><option value="1200">1200</option></select></label>
  </div>
  <div class="btnrow" style="margin-top:8px"><button type="button" id="avSave">Save key</button><span class="hint" id="avNote" style="align-self:center;margin:0"></span></div>
  <div id="acctOut" style="margin-top:12px">
    <div class="grid2">
      <label class="f">Email<input type="email" id="acEmail" autocomplete="email"></label>
      <label class="f">Password<input type="password" id="acPass" autocomplete="current-password"></label>
    </div>
    <div class="btnrow" style="margin-top:8px"><button type="button" class="primary" id="acIn">Sign in</button><button type="button" id="acUp">Create account</button></div>
  </div>
  <div id="acctIn" hidden style="margin-top:12px"><span id="acWho"></span> <button type="button" id="acOut" style="margin-left:8px">Sign out</button></div>
  <p class="hint" id="acMsg">Sign in to keep your watch list, saved tickers, cost basis and Alpha Vantage key with your account, on any device. Signed in, the key is kept in your account only, not in this browser. Without an account everything stays in this browser. Signing out clears this browser's copy; your account keeps its own.</p>
</section>
'''
rep('<div class="stack">',account+'\n<div class="stack">')
rep('<button type="button" role="tab" id="tabPut" aria-selected="false">Sell puts</button>','<button type="button" role="tab" id="tabPut" aria-selected="false">Sell puts</button>\n  <button type="button" role="tab" id="tabSet" aria-selected="false" style="margin-left:auto">Settings</button>')
rep('<div class="stack" id="leapTab">','<div class="stack" id="setTab" hidden><div id="setSlot"></div><p class="hint" id="setNote">Sign in with the Account box at the top of the page. Once you are signed in, it moves here.</p><p class="hint" id="appVer" style="margin:12px 2px 0">Options Scenario Lab, version __VERSION__ (built __BUILT__)</p></div>\n<div class="stack" id="leapTab">')
rep('const cc=S.tab==="cc",pt=S.tab==="put",lp=!cc&&!pt;','const cc=S.tab==="cc",pt=S.tab==="put",st=S.tab==="set",lp=!cc&&!pt&&!st;')
rep('$("srPanel").hidden=pt;','$("srPanel").hidden=pt||st;document.querySelector(\'[aria-label="More settings"]\').hidden=st;')
rep('$("leapTab").hidden=!lp;$("ccTab").hidden=!cc;$("putTab").hidden=!pt;','$("leapTab").hidden=!lp;$("ccTab").hidden=!cc;$("putTab").hidden=!pt;$("setTab").hidden=!st;$("tabSet").setAttribute("aria-selected",st);$("stockGrid").closest("section").hidden=st;')
rep('function render(){\n  renderSR();','function render(){\n  if(S.tab==="set")return;\n  renderSR();')
rep('$("tabPut").onclick=()=>{','$("tabSet").onclick=()=>{S.tab="set";derived();save();render()};\n$("tabPut").onclick=()=>{')


shim=r'''<script>
/* Hosted-page shim: gives the page the same window.claude calls the claude.ai artifact runtime provides. */
(function(){
const SB_URL="__SB_URL__",SB_KEY="__SB_KEY__",LS="leap-lab-v2",TABLE="options_lab_user_data";
const $=id=>document.getElementById(id);
const get=k=>{try{return localStorage.getItem(k)}catch(e){return null}},set=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const sb=(window.supabase&&window.supabase.createClient)?window.supabase.createClient(SB_URL,SB_KEY):null;
let session=null,memKey=null;   // signed in: the key lives only in the account and in memory; signed out: in this browser
const getKey=()=>session?(memKey||""):(get(LS+"-avkey")||"").trim();
const del=k=>{try{localStorage.removeItem(k)}catch(e){}};
let keyDone;const keyReady=new Promise(r=>{keyDone=r});
const ready=(async()=>{try{if(sb){const r=await sb.auth.getSession();session=(r&&r.data&&r.data.session)||null}}catch(e){}})();
if(sb)sb.auth.onAuthStateChange((ev,s)=>{const was=!!session;session=s||null;if(ev==="SIGNED_IN"&&!was&&window.__shimBooted)location.reload();if(ev==="SIGNED_OUT"&&was&&window.__shimBooted)location.reload()});

/* ----- Alpha Vantage over its web API, with the user's own key ----- */
const mcp={async callTool(server,tool,input){
  await keyReady;const key=getKey();
  if(!key)throw {code:"needs_reauth",message:"No Alpha Vantage key"};
  if(tool==="HISTORICAL_OPTIONS"&&input&&input.expiration&&dayCache.has(input.symbol+"|"+input.date)){
    const f=dayCache.get(input.symbol+"|"+input.date).filter(x=>x.expiration===input.expiration);
    return {payload:f.length?{message:"success",data:f}:{message:"No data for symbol "+input.symbol+" on date "+input.date+" with expiration "+input.expiration+".",data:[]}};
  }
  const p=new URLSearchParams();
  Object.entries(input||{}).forEach(([k,v])=>{if(k==="return_full_data"||v==null)return;p.set(k,v)});
  p.set("function",tool==="COMPANY_OVERVIEW"?"OVERVIEW":tool);p.set("apikey",key);
  let r;try{r=await fetch("https://www.alphavantage.co/query?"+p.toString())}catch(e){throw {code:"server_unavailable",message:"Couldn't reach Alpha Vantage",retryable:true}}
  if(!r.ok)throw {code:"tool_error",message:"Alpha Vantage answered HTTP "+r.status};
  const text=await r.text();let payload=text;try{payload=JSON.parse(text)}catch(e){}
  if(tool==="HISTORICAL_OPTIONS"&&payload&&Array.isArray(payload.data)&&payload.data.length&&payload.data[0].expiration){
    // keep the whole day if Alpha Vantage sent every expiry, and serve each expiry from it; otherwise pass through
    const dk=input.symbol+"|"+input.date;
    if(!input.expiration)return {payload};
    let rows=payload.data;
    if(new Set(rows.map(x=>x.expiration)).size>1){dayCache.set(dk,rows)}
    const f=rows.filter(x=>x.expiration===input.expiration);
    payload=f.length?Object.assign({},payload,{data:f}):{message:"No data for symbol "+input.symbol+" on date "+input.date+" with expiration "+input.expiration+".",data:[]};
  }
  return {payload};
}};
const dayCache=new Map();
/* ----- per-user saved data (Supabase, protected by row-level security: each person reads and writes only their own row) ----- */
const COL={favorites:"favs",putWatch:"put_watch",costBasis:"cost_basis"};
const db={collection:()=>({doc:name=>({
  async get(){const {data,error}=await sb.from(TABLE).select(COL[name]).eq("user_id",session.user.id).maybeSingle();if(error)throw error;const v=data&&data[COL[name]];return {exists:v!=null,data:()=>v}},
  async set(obj){const row={user_id:session.user.id,updated_at:new Date().toISOString()};row[COL[name]]=obj;const {error}=await sb.from(TABLE).upsert(row,{onConflict:"user_id"});if(error)throw error}
})})};
const user={id:async()=>session&&session.user.id};
const dl={async save({filename,data}){const b=data instanceof Blob?data:new Blob([data],{type:"text/csv"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=filename;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},1000)}};
window.claude={use:async n=>{await ready;return n==="mcp"?mcp:n==="downloads"?dl:(n==="db"&&sb&&session)?db:(n==="user"&&sb&&session)?user:null}};

/* ----- account box ----- */
const note=t=>{$("acMsg").textContent=t};
function placeAcct(){const a=$("acct"),slot=$("setSlot");if(session){slot.appendChild(a);$("setNote").hidden=true}else $("setNote").hidden=false}
function showAcct(){placeAcct();
  $("acctIn").hidden=!session;$("acctOut").hidden=!!session;
  if(session)$("acWho").textContent="Signed in as "+session.user.email+".";
  const k=getKey();
  $("avNote").textContent=k?"Key saved"+(session?" in your account only (not in this browser).":" in this browser (sign in to keep it in your account instead)."):"Needed for live data. Premium keys include end-of-day options.";
}
async function keySync(){ // signed in: the account copy is used; a key only on this browser is moved up and removed from the browser
  if(sb&&session){
    try{const {data}=await sb.from(TABLE).select("av_key").eq("user_id",session.user.id).maybeSingle();
      const remote=data&&data.av_key,local=(get(LS+"-avkey")||"").trim();
      if(remote)memKey=remote;
      else if(local){const {error}=await sb.from(TABLE).upsert({user_id:session.user.id,av_key:local,updated_at:new Date().toISOString()},{onConflict:"user_id"});if(!error)memKey=local}
      if(memKey)del(LS+"-avkey");
    }catch(e){}
  }
  keyDone();$("avKey").value=getKey();showAcct();
}
$("avKey").value=session?"":(get(LS+"-avkey")||"");
$("avRate").value=get(LS+"-avrate")||"75";
$("avRate").onchange=()=>{set(LS+"-avrate",$("avRate").value);location.reload()};
$("avSave").onclick=async()=>{
  const k=$("avKey").value.trim();
  if(sb&&session){
    try{const {error}=await sb.from(TABLE).upsert({user_id:session.user.id,av_key:k||null,updated_at:new Date().toISOString()},{onConflict:"user_id"});
      if(error)throw error;memKey=k;del(LS+"-avkey")}catch(e){note("Couldn't save the key to your account. Try again.");return}
  }else set(LS+"-avkey",k);
  showAcct();
};
const creds=()=>({email:$("acEmail").value.trim(),password:$("acPass").value});
$("acIn").onclick=async()=>{if(!sb){note("Sign-in isn't available right now (couldn't load the account service).");return}
  const {error}=await sb.auth.signInWithPassword(creds());if(error)note(error.message)};
$("acUp").onclick=async()=>{if(!sb){note("Sign-in isn't available right now (couldn't load the account service).");return}
  const c=creds();if(!c.email||c.password.length<6){note("Enter an email and a password of at least 6 characters.");return}
  const {data,error}=await sb.auth.signUp({email:c.email,password:c.password,options:{emailRedirectTo:location.origin+location.pathname}});
  if(error){note(error.message);return}
  if(!data.session)note("Almost done: check your email and tap the confirmation link, then you'll be signed in.")};
$("acOut").onclick=async()=>{await sb.auth.signOut();try{Object.keys(localStorage).filter(k=>k.indexOf(LS)===0).forEach(k=>localStorage.removeItem(k))}catch(e){}location.reload()};
ready.then(()=>{keySync();window.__shimBooted=true});
showAcct();
})();
</script>
'''.replace("__SB_URL__",SB_URL).replace("__SB_KEY__",SB_KEY)

m=re.search(r'<script>\n\(function\(\)\{\n"use strict";',s)
assert m,"main script not found"
s=s[:m.start()]+'<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>\n'+shim+s[m.start():]

head='<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>*,*::before,*::after{box-sizing:border-box}html,body{margin:0}body{background:var(--bg);color:var(--ink);font-family:var(--font-ui)}@media(max-width:520px){.tabs{gap:0}.tabs button{padding:10px 7px;font-size:13px;white-space:nowrap;min-width:0}}input[type=password],input[type=email]{font:500 16px var(--font-num);color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:9px 10px;min-height:42px;width:100%;min-width:0}</style>\n'
s=s.replace('__VERSION__',VERSION).replace('__BUILT__',BUILT)
out=head+s+'\n</body></html>\n'
open(dst,'w',encoding='utf8').write(out)
print("wrote",dst,len(out))
