import { useState } from 'react';
import { pcodAPI } from '../../services/api';
import { Loader2, AlertTriangle, CheckCircle2, ShieldAlert, Stethoscope, Clock, X, ArrowRight, ArrowLeft } from 'lucide-react';

const RISK={low:{bg:'#22c55e18',color:'#16a34a',Icon:CheckCircle2},medium:{bg:'#f59e0b18',color:'#d97706',Icon:AlertTriangle},high:{bg:'#ef444418',color:'#dc2626',Icon:ShieldAlert}};

const STEPS=[
  {title:'Menstrual Health',fields:[
    {key:'irregular_periods',label:'Do you experience irregular periods?',type:'bool',req:true},
    {key:'period_frequency',label:'How often do you get periods?',type:'select',options:['monthly','every 2-3 months','rarely']},
    {key:'heavy_bleeding',label:'Heavy menstrual bleeding?',type:'bool'},
  ]},
  {title:'Physical Symptoms',fields:[
    {key:'weight_gain',label:'Unexplained weight gain?',type:'bool',req:true},
    {key:'acne',label:'Persistent acne?',type:'bool',req:true},
    {key:'facial_hair_growth',label:'Excessive facial hair?',type:'bool',req:true},
    {key:'hair_thinning',label:'Hair thinning or loss?',type:'bool',req:true},
    {key:'skin_darkening',label:'Dark patches on skin?',type:'bool'},
  ]},
  {title:'Systemic Symptoms',fields:[
    {key:'fatigue',label:'Chronic fatigue?',type:'bool',req:true},
    {key:'mood_swings',label:'Frequent mood swings?',type:'bool',req:true},
    {key:'pelvic_pain',label:'Pelvic pain?',type:'bool'},
    {key:'sleep_issues',label:'Sleep disturbances?',type:'bool'},
  ]},
  {title:'Medical History & Lifestyle',fields:[
    {key:'insulin_resistance_history',label:'History of insulin resistance?',type:'bool'},
    {key:'diabetes_family_history',label:'Family history of diabetes?',type:'bool'},
    {key:'thyroid_issues',label:'Known thyroid issues?',type:'bool'},
    {key:'pcos_family_history',label:'Family history of PCOS/PCOD?',type:'bool'},
    {key:'exercise_frequency',label:'Exercise frequency',type:'select',options:['daily','weekly','rarely']},
    {key:'stress_level',label:'Stress level',type:'select',options:['low','moderate','high']},
    {key:'age',label:'Your age',type:'number'},
  ]},
];

export default function PCODAssessment(){
  const[step,setStep]=useState(0);
  const[form,setForm]=useState({irregular_periods:false,weight_gain:false,acne:false,facial_hair_growth:false,hair_thinning:false,fatigue:false,mood_swings:false});
  const[loading,setLoading]=useState(false);
  const[result,setResult]=useState(null);
  const[error,setError]=useState('');
  const[history,setHistory]=useState([]);
  const[showHist,setShowHist]=useState(false);

  const set=(k,v)=>setForm(p=>({...p,[k]:v}));
  const next=()=>step<STEPS.length-1&&setStep(s=>s+1);
  const prev=()=>step>0&&setStep(s=>s-1);

  const submit=async()=>{
    setLoading(true);setError('');
    try{const r=await pcodAPI.assess(form);setResult(r);setStep(STEPS.length);}
    catch(e){setError(e.message);}finally{setLoading(false);}
  };

  const loadHist=async()=>{try{const r=await pcodAPI.getHistory();setHistory(r.assessments||[]);}catch{setHistory([]);}setShowHist(true);};
  const reset=()=>{setStep(0);setResult(null);setForm({irregular_periods:false,weight_gain:false,acne:false,facial_hair_growth:false,hair_thinning:false,fatigue:false,mood_swings:false});};

  const risk=result?RISK[result.risk_level]||RISK.low:null;

  return(
    <div className="pcod-page">
      <div className="pcod-header">
        <div><h1>PCOD / PCOS Assessment</h1><p>Complete the questionnaire for a risk assessment</p></div>
        <button className="skin-history-btn" onClick={loadHist}><Clock size={16}/> History</button>
      </div>

      {result?(
        <div className="pcod-result">
          <div className="skin-result-card">
            <div className="skin-result-top"><h2>Assessment Result</h2>
              <div className="skin-severity-badge" style={{background:risk.bg,color:risk.color}}><risk.Icon size={14}/> {result.risk_level.toUpperCase()} Risk</div>
            </div>
            <div className="skin-confidence">
              <span className="skin-confidence-label">Risk Score</span>
              <div className="skin-confidence-bar"><div className="skin-confidence-fill" style={{width:`${(result.risk_score*100).toFixed(0)}%`,background:risk.color}}/></div>
              <span className="skin-confidence-pct">{(result.risk_score*100).toFixed(1)}%</span>
            </div>
            {result.conditions_flagged?.length>0&&<div className="pcod-flags"><h4>Conditions Flagged</h4><div className="pcod-flag-chips">{result.conditions_flagged.map((c,i)=><span key={i} className="pcod-flag-chip">{c}</span>)}</div></div>}
            {result.key_indicators?.length>0&&<div className="skin-result-section"><h4>Key Indicators</h4><ul>{result.key_indicators.map((k,i)=><li key={i}>{k}</li>)}</ul></div>}
            <div className="skin-specialist"><Stethoscope size={16}/><span>Recommended: <strong>{result.recommended_specialist}</strong></span></div>
            {result.recommendations?.length>0&&<div className="skin-result-section"><h4>Recommendations</h4><ul>{result.recommendations.map((r,i)=><li key={i}>{r}</li>)}</ul></div>}
            {result.precautions?.length>0&&<div className="skin-result-section"><h4>Precautions</h4><ul>{result.precautions.map((p,i)=><li key={i}>{p}</li>)}</ul></div>}
            <p className="skin-disclaimer">{result.disclaimer}</p>
            <button className="pcod-retake-btn" onClick={reset}>Take Again</button>
          </div>
        </div>
      ):(
        <div className="pcod-form-area">
          <div className="pcod-progress">
            {STEPS.map((_,i)=>(
              <div key={i} className={`pcod-progress-step ${i<=step?'pcod-step-active':''} ${i<step?'pcod-step-done':''}`}>
                <div className="pcod-step-dot">{i<step?'✓':i+1}</div>
                <span>{STEPS[i].title}</span>
              </div>
            ))}
          </div>
          <div className="pcod-step-card">
            <h2>{STEPS[step].title}</h2>
            <div className="pcod-fields">
              {STEPS[step].fields.map(f=>(
                <div key={f.key} className="pcod-field">
                  <label>{f.label}{f.req&&<span className="pcod-req">*</span>}</label>
                  {f.type==='bool'?(
                    <div className="pcod-toggle-row">
                      <button className={`pcod-toggle ${form[f.key]===true?'pcod-toggle-yes':''}`} onClick={()=>set(f.key,true)}>Yes</button>
                      <button className={`pcod-toggle ${form[f.key]===false?'pcod-toggle-no':''}`} onClick={()=>set(f.key,false)}>No</button>
                    </div>
                  ):f.type==='select'?(
                    <select value={form[f.key]||''} onChange={e=>set(f.key,e.target.value)} className="pcod-select">
                      <option value="">Select...</option>
                      {f.options.map(o=><option key={o} value={o}>{o}</option>)}
                    </select>
                  ):(
                    <input type="number" value={form[f.key]||''} onChange={e=>set(f.key,parseInt(e.target.value)||undefined)} placeholder="Enter..." className="pcod-number-input"/>
                  )}
                </div>
              ))}
            </div>
            {error&&<div className="skin-error">{error}</div>}
            <div className="pcod-nav">
              {step>0&&<button className="pcod-nav-btn pcod-nav-prev" onClick={prev}><ArrowLeft size={16}/> Previous</button>}
              {step<STEPS.length-1?<button className="pcod-nav-btn pcod-nav-next" onClick={next}>Next <ArrowRight size={16}/></button>
                :<button className="pcod-nav-btn pcod-nav-submit" onClick={submit} disabled={loading}>{loading?<><Loader2 size={16} className="auth-spinner"/> Assessing...</>:'Submit Assessment'}</button>}
            </div>
          </div>
        </div>
      )}

      {showHist&&(
        <div className="skin-history-overlay" onClick={()=>setShowHist(false)}>
          <div className="skin-history-modal" onClick={e=>e.stopPropagation()}>
            <div className="skin-history-top"><h2>Assessment History</h2><button onClick={()=>setShowHist(false)}><X size={18}/></button></div>
            {history.length===0?<p className="skin-history-empty">No previous assessments.</p>:(
              <div className="skin-history-list">{history.map(h=>(
                <div key={h.id} className="skin-history-item">
                  <div><strong>Risk: {h.risk_level}</strong>
                    <span className="skin-severity-badge" style={{background:(RISK[h.risk_level]||RISK.low).bg,color:(RISK[h.risk_level]||RISK.low).color}}>{(h.risk_score*100).toFixed(0)}%</span>
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
