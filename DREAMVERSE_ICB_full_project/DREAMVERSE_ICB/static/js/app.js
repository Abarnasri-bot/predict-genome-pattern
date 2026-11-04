const $ = (id) => document.getElementById(id);
const toast = (msg) => { const t=$("toast"); t.textContent=msg; t.classList.add("show"); setTimeout(()=>t.classList.remove("show"),2400); };

$("themeToggle").addEventListener("click",()=>{document.body.classList.toggle("glow");toast("Glow settings shifted ✧");});

const seqInput=$("sequenceInput");
seqInput.addEventListener("input",()=>{$("baseCount").textContent=`${seqInput.value.replace(/\s/g,"").length} bases`;});
document.querySelectorAll(".sample").forEach(b=>b.addEventListener("click",()=>{seqInput.value=b.dataset.seq;seqInput.dispatchEvent(new Event("input"));}));

$("analyzeBtn").addEventListener("click",async()=>{
  $("resultStatus").textContent="PROCESSING...";
  try{
    const res=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sequence:seqInput.value})});
    const data=await res.json(); if(!res.ok) throw new Error(data.error||"Analysis failed");
    $("prediction").textContent=`GROUP ${data.prediction}`;
    $("predictionNote").textContent=`Model confidence: ${data.confidence}% (not a guarantee of biological certainty)`;
    $("aVal").textContent=data.features.A_count;$("tVal").textContent=data.features.T_count;
    $("gVal").textContent=data.features.G_count;$("cVal").textContent=data.features.C_count;
    $("lenVal").textContent=data.features.Length;$("gcVal").textContent=`${data.features.GC_percent}%`;
    $("gcLabel").textContent=`${data.features.GC_percent}%`;$("gcBar").style.width=`${data.features.GC_percent}%`;
    $("modelInfo").textContent=`Training source: ${data.model_source}. ${data.accuracy===null?"Accuracy not reported for this small dataset.":`Held-out test accuracy: ${data.accuracy}%.`} ${data.warning}`;
    $("resultStatus").textContent="ANALYSIS COMPLETE";await loadHistory();toast("Sequence decoded ✦");
  }catch(e){$("resultStatus").textContent="CHECK INPUT";toast(e.message);}
});

$("uploadBtn").addEventListener("click",async()=>{
  const f=$("datasetFile").files[0];if(!f){toast("Choose your assignment CSV first.");return;}
  const fd=new FormData();fd.append("dataset",f);
  $("uploadBtn").textContent="TRAINING...";
  try{const r=await fetch("/api/upload",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error);toast(`${d.message} ${d.rows} rows.`);await loadStatus();}
  catch(e){toast(e.message);}finally{$("uploadBtn").textContent="UPLOAD & TRAIN MODEL";}
});

async function loadStatus(){try{const r=await fetch("/api/status");const d=await r.json();$("modelInfo").textContent=d.ok?`Training source: ${d.source} • ${d.rows} sequences • ${d.accuracy===null?"No reliable held-out accuracy available.":`Test accuracy: ${d.accuracy}%`}`:d.error;}catch(e){}}
async function loadHistory(){const r=await fetch("/api/history");const rows=await r.json();$("historyList").innerHTML=rows.length?rows.map(x=>`<div class="history-row"><span>${x.sequence.slice(0,28)}${x.sequence.length>28?"…":""}</span><b>GROUP ${x.group_result}</b><span>${new Date(x.created_at).toLocaleString()}</span></div>`).join(""):"No analyses yet.";}
async function loadLeaderboard(){const r=await fetch("/api/leaderboard");const rows=await r.json();$("leaderboard").textContent=rows.length?rows.map((x,i)=>`${i+1}. ${x.player} — ${x.score}`).join("  /  "):"No scores yet — be the first explorer.";}

document.querySelectorAll(".collect").forEach(b=>b.addEventListener("click",()=>{toast(`Entering ${b.dataset.world}... find a fragment below!`);$("gameStage").scrollIntoView({behavior:"smooth",block:"center"});}));

// Six collectible fragments appear in changing positions; click to collect.
const layer=$("fragmentLayer");let collected=0,score=0;
const positions=[[12,25],[28,70],[47,18],[65,65],[82,30],[90,75]];
positions.forEach((p,i)=>{const f=document.createElement("button");f.className="fragment";f.textContent=["A","T","G","C","✦","✧"][i];f.style.left=p[0]+"%";f.style.top=p[1]+"%";f.style.animationDelay=(i*.22)+"s";f.title="Collect DNA fragment";f.addEventListener("click",()=>{if(f.disabled)return;f.disabled=true;f.style.opacity=".15";f.style.transform="scale(.5)";collected++;score+=10;$("collected").textContent=`${collected} / 6`;$("score").textContent=String(score).padStart(3,"0");toast("Fragment collected +10 ✧");if(collected===6){toast("Dream map completed! +20 bonus");score+=20;$("score").textContent=String(score).padStart(3,"0");fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({player:"Dream Explorer",score})}).then(loadLeaderboard);}});layer.appendChild(f);});
loadStatus();loadHistory();loadLeaderboard();
