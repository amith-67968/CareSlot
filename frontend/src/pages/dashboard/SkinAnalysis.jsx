import { useState, useRef } from 'react';
import { skinAPI } from '../../services/api';
import { Upload, Image as Img, X, Loader2, AlertTriangle, CheckCircle2, Stethoscope, ShieldAlert, Clock } from 'lucide-react';

const SYMPTS = [
  { key:'itching',label:'Itching' },{ key:'redness',label:'Redness' },
  { key:'pain',label:'Pain' },{ key:'burning_sensation',label:'Burning' },{ key:'fever',label:'Fever' },
];
const SEV = {
  mild:{ bg:'#22c55e18',color:'#16a34a',Icon:CheckCircle2,l:'Mild' },
  moderate:{ bg:'#f59e0b18',color:'#d97706',Icon:AlertTriangle,l:'Moderate' },
  severe:{ bg:'#ef444418',color:'#dc2626',Icon:ShieldAlert,l:'Severe' },
};

export default function SkinAnalysis(){
  const[file,setFile]=useState(null);
  const[preview,setPreview]=useState(null);
  const[syms,setSyms]=useState({});
  const[dur,setDur]=useState('');
  const[notes,setNotes]=useState('');
  const[loading,setLoading]=useState(false);
  const[result,setResult]=useState(null);
  const[error,setError]=useState('');
  const[history,setHistory]=useState([]);
  const[showHist,setShowHist]=useState(false);
  const dropRef=useRef(null);
  const fileRef=useRef(null);

  const pickFile=(f)=>{
    if(!f)return;
    if(!['image/jpeg','image/png','image/webp','image/jpg'].includes(f.type)){setError('Upload JPEG/PNG/WebP');return;}
    if(f.size>10*1024*1024){setError('Max 10MB');return;}
    setError('');setFile(f);setPreview(URL.createObjectURL(f));setResult(null);
  };
  const clear=()=>{setFile(null);setPreview(null);setResult(null);if(fileRef.current)fileRef.current.value='';};

  const analyze=async()=>{
    if(!file)return;setLoading(true);setError('');
    try{const r=await skinAPI.analyze(file,{...syms,duration:dur||undefined,additional_notes:notes||undefined});setResult(r);}
    catch(e){setError(e.message||'Analysis failed');}finally{setLoading(false);}
  };

  const loadHist=async()=>{try{const r=await skinAPI.getHistory();setHistory(r.predictions||[]);}catch{setHistory([]);}setShowHist(true);};
  const sev=result?SEV[result.severity_level]||SEV.mild:null;

  return(
    <div className="skin-page">
      <div className="skin-header">
        <div><h1>Skin Disease Analysis</h1><p>Upload a skin image for AI-powered assessment</p></div>
        <button className="skin-history-btn" onClick={loadHist}><Clock size={16}/> Past Scans</button>
      </div>
      <div className="skin-grid">
        <div className="skin-upload-col">
          <div ref={dropRef} className="skin-dropzone"
            onDrop={e=>{e.preventDefault();dropRef.current?.classList.remove('skin-drop-active');pickFile(e.dataTransfer.files?.[0]);}}
            onDragOver={e=>{e.preventDefault();dropRef.current?.classList.add('skin-drop-active');}}
            onDragLeave={()=>dropRef.current?.classList.remove('skin-drop-active')}
            onClick={()=>fileRef.current?.click()}>
            {preview?(
              <div className="skin-preview-wrap">
                <img src={preview} alt="Preview" className="skin-preview-img"/>
                <button className="skin-preview-clear" onClick={e=>{e.stopPropagation();clear();}}><X size={16}/></button>
              </div>
            ):(
              <div className="skin-drop-placeholder">
                <div className="skin-drop-icon"><Upload size={28}/></div>
                <p className="skin-drop-title">Drop image here or click to browse</p>
                <p className="skin-drop-sub">JPEG, PNG, or WebP — max 10 MB</p>
              </div>
            )}
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="skin-file-input" onChange={e=>pickFile(e.target.files?.[0])}/>
          </div>
          <div className="skin-symptoms-card">
            <h3>Accompanying Symptoms</h3>
            <div className="skin-symptom-checks">
              {SYMPTS.map(s=>(
                <label key={s.key} className="skin-check-label">
                  <input type="checkbox" checked={!!syms[s.key]} onChange={()=>setSyms(p=>({...p,[s.key]:!p[s.key]}))}/>
                  <span>{s.label}</span>
                </label>
              ))}
            </div>
            <input type="text" placeholder="Duration (e.g. 3 days)" value={dur} onChange={e=>setDur(e.target.value)} className="skin-duration-input"/>
            <textarea placeholder="Additional notes..." value={notes} onChange={e=>setNotes(e.target.value)} className="skin-notes-input" rows={3}/>
            <button className="skin-analyze-btn" onClick={analyze} disabled={!file||loading}>
              {loading?<><Loader2 size={16} className="auth-spinner"/> Analyzing...</>:<><Img size={16}/> Analyze Image</>}
            </button>
          </div>
          {error&&<div className="skin-error">{error}</div>}
        </div>

        <div className="skin-result-col">
          {result?(
            <div className="skin-result-card">
              <div className="skin-result-top"><h2>Analysis Result</h2>
                <div className="skin-severity-badge" style={{background:sev.bg,color:sev.color}}><sev.Icon size={14}/> {sev.l}</div>
              </div>
              <div className="skin-result-condition">
                <span className="skin-result-label">Detected Condition</span>
                <span className="skin-result-value">{result.predicted_condition}</span>
              </div>
              <div className="skin-confidence">
                <span className="skin-confidence-label">Confidence</span>
                <div className="skin-confidence-bar"><div className="skin-confidence-fill" style={{width:`${(result.confidence_score*100).toFixed(0)}%`}}/></div>
                <span className="skin-confidence-pct">{(result.confidence_score*100).toFixed(1)}%</span>
              </div>
              <div className="skin-specialist"><Stethoscope size={16}/><span>Recommended: <strong>{result.recommended_specialist}</strong></span></div>
              {result.precautions?.length>0&&<div className="skin-result-section"><h4>Precautions</h4><ul>{result.precautions.map((p,i)=><li key={i}>{p}</li>)}</ul></div>}
              {result.home_remedies?.length>0&&<div className="skin-result-section"><h4>Home Remedies</h4><ul>{result.home_remedies.map((r,i)=><li key={i}>{r}</li>)}</ul></div>}
              {result.next_steps?.length>0&&<div className="skin-result-section"><h4>Next Steps</h4><ul>{result.next_steps.map((s,i)=><li key={i}>{s}</li>)}</ul></div>}
              <p className="skin-disclaimer">{result.disclaimer}</p>
            </div>
          ):(
            <div className="skin-result-empty"><Img size={48} strokeWidth={1}/><h3>Results will appear here</h3><p>Upload a skin image and click Analyze.</p></div>
          )}
        </div>
      </div>

      {showHist&&(
        <div className="skin-history-overlay" onClick={()=>setShowHist(false)}>
          <div className="skin-history-modal" onClick={e=>e.stopPropagation()}>
            <div className="skin-history-top"><h2>Past Scans</h2><button onClick={()=>setShowHist(false)}><X size={18}/></button></div>
            {history.length===0?<p className="skin-history-empty">No previous scans.</p>:(
              <div className="skin-history-list">{history.map(h=>(
                <div key={h.id} className="skin-history-item">
                  <div><strong>{h.predicted_condition}</strong>
                    <span className="skin-severity-badge" style={{background:(SEV[h.severity_level]||SEV.mild).bg,color:(SEV[h.severity_level]||SEV.mild).color}}>{h.severity_level}</span>
                  </div>
                  <small>{h.created_at?new Date(h.created_at).toLocaleDateString():''}</small>
                </div>
              ))}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
