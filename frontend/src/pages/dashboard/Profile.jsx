import { useState, useEffect } from 'react';
import { profileAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { UserCircle, Save, Loader2, Plus, X } from 'lucide-react';

export default function Profile(){
  const{user}=useAuth();
  const[profile,setProfile]=useState(null);
  const[editing,setEditing]=useState(false);
  const[form,setForm]=useState({});
  const[saving,setSaving]=useState(false);
  const[medHist,setMedHist]=useState([]);
  const[showAdd,setShowAdd]=useState(false);
  const[newCond,setNewCond]=useState({condition_name:'',status:'active',notes:''});

  useEffect(()=>{
    profileAPI.get().then(d=>{setProfile(d);setForm(d);}).catch(()=>{ /* profile can be retried by revisiting */ });
    profileAPI.getMedicalHistory().then(d=>setMedHist(Array.isArray(d)?d:[])).catch(()=>{ /* optional section */ });
  },[]);

  const set=(k,v)=>setForm(p=>({...p,[k]:v}));

  const saveProfile=async()=>{
    setSaving(true);
    try{const r=await profileAPI.update({full_name:form.full_name,phone:form.phone,date_of_birth:form.date_of_birth,gender:form.gender,blood_group:form.blood_group});setProfile(r);setEditing(false);}
    catch{ /* keep edit mode active for retry */ }finally{setSaving(false);}
  };

  const addCondition=async(e)=>{
    e.preventDefault();
    try{await profileAPI.addMedicalHistory(newCond);const r=await profileAPI.getMedicalHistory();setMedHist(Array.isArray(r)?r:[]);setShowAdd(false);setNewCond({condition_name:'',status:'active',notes:''});}catch{ /* form remains open for retry */ }
  };

  return(
    <div className="profile-page">
      <div className="profile-header"><h1>My Profile</h1>
        {!editing?<button className="appt-new-btn" onClick={()=>setEditing(true)}>Edit Profile</button>
          :<button className="appt-new-btn" onClick={saveProfile} disabled={saving}>{saving?<Loader2 size={16} className="auth-spinner"/>:<Save size={16}/>} Save</button>}
      </div>

      <div className="profile-grid">
        <div className="profile-card profile-info-card">
          <div className="profile-avatar"><UserCircle size={64} strokeWidth={1}/></div>
          <div className="profile-fields">
            <div className="profile-field"><label>Full Name</label>{editing?<input value={form.full_name||''} onChange={e=>set('full_name',e.target.value)}/>:<span>{profile?.full_name||'—'}</span>}</div>
            <div className="profile-field"><label>Email</label><span>{profile?.email||user?.email||'—'}</span></div>
            <div className="profile-field"><label>Phone</label>{editing?<input value={form.phone||''} onChange={e=>set('phone',e.target.value)}/>:<span>{profile?.phone||'—'}</span>}</div>
            <div className="profile-field"><label>Date of Birth</label>{editing?<input type="date" value={form.date_of_birth||''} onChange={e=>set('date_of_birth',e.target.value)}/>:<span>{profile?.date_of_birth||'—'}</span>}</div>
            <div className="profile-field"><label>Gender</label>{editing?<select value={form.gender||''} onChange={e=>set('gender',e.target.value)}><option value="">Select</option><option value="male">Male</option><option value="female">Female</option><option value="other">Other</option></select>:<span>{profile?.gender||'—'}</span>}</div>
            <div className="profile-field"><label>Blood Group</label>{editing?<input value={form.blood_group||''} onChange={e=>set('blood_group',e.target.value)} placeholder="A+, B-, etc."/>:<span>{profile?.blood_group||'—'}</span>}</div>
          </div>
        </div>

        <div className="profile-card">
          <div className="profile-card-header"><h3>Medical History</h3><button onClick={()=>setShowAdd(true)}><Plus size={16}/> Add</button></div>
          {medHist.length===0?<p className="profile-empty">No medical history recorded.</p>:(
            <div className="profile-med-list">{medHist.map(m=>(
              <div key={m.id} className="profile-med-item">
                <strong>{m.condition_name}</strong>
                <span className={`profile-med-status profile-med-${m.status}`}>{m.status}</span>
                {m.notes&&<p>{m.notes}</p>}
                {m.diagnosed_date&&<small>Diagnosed: {m.diagnosed_date}</small>}
              </div>
            ))}</div>
          )}
        </div>
      </div>

      {showAdd&&(
        <div className="skin-history-overlay" onClick={()=>setShowAdd(false)}>
          <div className="appt-modal" onClick={e=>e.stopPropagation()}>
            <div className="skin-history-top"><h2>Add Condition</h2><button onClick={()=>setShowAdd(false)}><X size={18}/></button></div>
            <form onSubmit={addCondition} className="appt-form">
              <div className="appt-form-field"><label>Condition *</label><input required value={newCond.condition_name} onChange={e=>setNewCond(p=>({...p,condition_name:e.target.value}))}/></div>
              <div className="appt-form-field"><label>Status</label><select value={newCond.status} onChange={e=>setNewCond(p=>({...p,status:e.target.value}))}><option value="active">Active</option><option value="resolved">Resolved</option></select></div>
              <div className="appt-form-field"><label>Notes</label><textarea value={newCond.notes} onChange={e=>setNewCond(p=>({...p,notes:e.target.value}))} rows={2}/></div>
              <button type="submit" className="appt-submit-btn">Add Condition</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
