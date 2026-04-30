import { useState, useEffect, useCallback } from 'react';
import { notificationAPI } from '../../services/api';
import { Bell, Clock, Plus, X, Check, Loader2 } from 'lucide-react';

const TYPE_ICONS = { appointment: '📅', follow_up: '🔄', medicine: '💊', health_check: '🩺', general: '📢' };

export default function Notifications(){
  const[tab,setTab]=useState('notifications');
  const[notifs,setNotifs]=useState([]);
  const[reminders,setReminders]=useState([]);
  const[loading,setLoading]=useState(true);
  const[showForm,setShowForm]=useState(false);
  const[form,setForm]=useState({title:'',description:'',reminder_type:'medicine',scheduled_at:'',recurrence:'none'});
  const[saving,setSaving]=useState(false);

  const load=useCallback(async()=>{
    setLoading(true);
    try{
      if(tab==='notifications'){const r=await notificationAPI.list();setNotifs(r.notifications||[]);}
      else{const r=await notificationAPI.listReminders();setReminders(r.reminders||[]);}
    }catch{ /* notification fetch is retryable from the tab controls */ }finally{setLoading(false);}
  },[tab]);

  useEffect(()=>{load();},[load]);

  const markRead=async(id)=>{try{await notificationAPI.markRead(id);load();}catch{ /* keep item visible if update fails */ }};
  const cancelRem=async(id)=>{try{await notificationAPI.cancelReminder(id);load();}catch{ /* keep reminder visible if cancellation fails */ }};

  const createReminder=async(e)=>{
    e.preventDefault();setSaving(true);
    try{await notificationAPI.createReminder({...form,scheduled_at:new Date(form.scheduled_at).toISOString()});setShowForm(false);setTab('reminders');load();}
    catch{ /* form remains open for retry */ }finally{setSaving(false);}
  };

  return(
    <div className="notif-page">
      <div className="notif-header"><div><h1>Notifications & Reminders</h1></div>
        <button className="appt-new-btn" onClick={()=>setShowForm(true)}><Plus size={16}/> New Reminder</button>
      </div>

      <div className="appt-filters">
        <button className={`appt-filter-btn ${tab==='notifications'?'appt-filter-active':''}`} onClick={()=>setTab('notifications')}>Notifications</button>
        <button className={`appt-filter-btn ${tab==='reminders'?'appt-filter-active':''}`} onClick={()=>setTab('reminders')}>Reminders</button>
      </div>

      {loading?<div className="appt-loading"><Loader2 size={24} className="auth-spinner"/></div>:tab==='notifications'?(
        notifs.length===0?<div className="appt-empty"><Bell size={48} strokeWidth={1}/><h3>No notifications</h3></div>:(
          <div className="notif-list">{notifs.map(n=>(
            <div key={n.id} className={`notif-item ${n.is_read?'':'notif-unread'}`}>
              <span className="notif-type-icon">{TYPE_ICONS[n.type]||'📢'}</span>
              <div className="notif-body"><strong>{n.title}</strong><p>{n.body}</p>
                {n.created_at&&<small>{new Date(n.created_at).toLocaleString()}</small>}
              </div>
              {!n.is_read&&<button className="notif-read-btn" onClick={()=>markRead(n.id)} title="Mark read"><Check size={14}/></button>}
            </div>
          ))}</div>
        )
      ):(
        reminders.length===0?<div className="appt-empty"><Clock size={48} strokeWidth={1}/><h3>No reminders</h3></div>:(
          <div className="notif-list">{reminders.map(r=>(
            <div key={r.id} className="notif-item">
              <span className="notif-type-icon">{TYPE_ICONS[r.reminder_type]||'⏰'}</span>
              <div className="notif-body"><strong>{r.title}</strong>{r.description&&<p>{r.description}</p>}
                <small>{new Date(r.scheduled_at).toLocaleString()} · {r.recurrence} · {r.status}</small>
              </div>
              {r.status==='pending'&&<button className="notif-cancel-btn" onClick={()=>cancelRem(r.id)} title="Cancel"><X size={14}/></button>}
            </div>
          ))}</div>
        )
      )}

      {showForm&&(
        <div className="skin-history-overlay" onClick={()=>setShowForm(false)}>
          <div className="appt-modal" onClick={e=>e.stopPropagation()}>
            <div className="skin-history-top"><h2>New Reminder</h2><button onClick={()=>setShowForm(false)}><X size={18}/></button></div>
            <form onSubmit={createReminder} className="appt-form">
              <div className="appt-form-field"><label>Title *</label><input required value={form.title} onChange={e=>setForm(p=>({...p,title:e.target.value}))}/></div>
              <div className="appt-form-field"><label>Description</label><textarea value={form.description} onChange={e=>setForm(p=>({...p,description:e.target.value}))} rows={2}/></div>
              <div className="appt-form-field"><label>Type</label><select value={form.reminder_type} onChange={e=>setForm(p=>({...p,reminder_type:e.target.value}))}><option value="medicine">Medicine</option><option value="appointment">Appointment</option><option value="follow_up">Follow Up</option><option value="health_check">Health Check</option></select></div>
              <div className="appt-form-field"><label>When *</label><input type="datetime-local" required value={form.scheduled_at} onChange={e=>setForm(p=>({...p,scheduled_at:e.target.value}))}/></div>
              <div className="appt-form-field"><label>Recurrence</label><select value={form.recurrence} onChange={e=>setForm(p=>({...p,recurrence:e.target.value}))}><option value="none">None</option><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></div>
              <button type="submit" className="appt-submit-btn" disabled={saving}>{saving?'Creating...':'Create Reminder'}</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
