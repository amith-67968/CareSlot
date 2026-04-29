import { useState, useEffect } from 'react';
import { doctorAPI } from '../../services/api';
import { MapPin, Star, Phone, Globe, Clock, Search, Loader2, Navigation } from 'lucide-react';

export default function Doctors(){
  const[results,setResults]=useState([]);
  const[specs,setSpecs]=useState([]);
  const[specialty,setSpecialty]=useState('');
  const[keyword,setKeyword]=useState('');
  const[radius,setRadius]=useState(5000);
  const[loading,setLoading]=useState(false);
  const[error,setError]=useState('');
  const[located,setLocated]=useState(false);
  const[coords,setCoords]=useState(null);

  useEffect(()=>{doctorAPI.getSpecialties().then(d=>setSpecs(d.specialties||[])).catch(()=>{});},[]);

  const getLocation=()=>new Promise((res,rej)=>{
    if(coords)return res(coords);
    if(!navigator.geolocation)return rej(new Error('Geolocation not supported'));
    navigator.geolocation.getCurrentPosition(p=>{const c={lat:p.coords.latitude,lng:p.coords.longitude};setCoords(c);setLocated(true);res(c);},()=>rej(new Error('Location access denied')));
  });

  const search=async()=>{
    setLoading(true);setError('');
    try{
      const loc=await getLocation();
      const r=await doctorAPI.findNearby(loc.lat,loc.lng,specialty||undefined,radius,keyword||undefined);
      setResults(r.results||[]);
    }catch(e){setError(e.message);}finally{setLoading(false);}
  };

  return(
    <div className="doc-page">
      <div className="doc-header"><h1>Find Doctors & Hospitals</h1><p>Search nearby healthcare providers</p></div>
      <div className="doc-search-bar">
        <select value={specialty} onChange={e=>setSpecialty(e.target.value)} className="doc-select">
          <option value="">All Specialties</option>
          {specs.map(s=><option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
        <input type="text" placeholder="Keyword (e.g. clinic)" value={keyword} onChange={e=>setKeyword(e.target.value)} className="doc-keyword"/>
        <select value={radius} onChange={e=>setRadius(Number(e.target.value))} className="doc-radius">
          <option value={2000}>2 km</option><option value={5000}>5 km</option><option value={10000}>10 km</option><option value={25000}>25 km</option>
        </select>
        <button className="doc-search-btn" onClick={search} disabled={loading}>
          {loading?<Loader2 size={16} className="auth-spinner"/>:<Search size={16}/>} Search
        </button>
      </div>
      {!located&&<p className="doc-loc-hint"><Navigation size={14}/> Your location will be requested on search.</p>}
      {error&&<div className="skin-error">{error}</div>}

      {results.length===0&&!loading?(
        <div className="doc-empty"><MapPin size={48} strokeWidth={1}/><h3>Search for nearby doctors</h3><p>Select a specialty and radius, then hit search.</p></div>
      ):(
        <div className="doc-grid">
          {results.map(d=>(
            <div key={d.place_id} className="doc-card">
              <div className="doc-card-top">
                <h3>{d.name}</h3>
                {d.is_open_now!=null&&<span className={`doc-open-badge ${d.is_open_now?'doc-open':'doc-closed'}`}>{d.is_open_now?'Open':'Closed'}</span>}
              </div>
              <p className="doc-address"><MapPin size={13}/>{d.address}</p>
              {d.rating&&<div className="doc-rating"><Star size={14}/><strong>{d.rating}</strong><span>({d.total_ratings} reviews)</span></div>}
              {d.distance_text&&<span className="doc-distance"><Navigation size={12}/>{d.distance_text}</span>}
              {d.specialty_match&&<span className="doc-specialty-match">{d.specialty_match}</span>}
              <div className="doc-links">
                {d.phone_number&&<a href={`tel:${d.phone_number}`}><Phone size={13}/>{d.phone_number}</a>}
                {d.website&&<a href={d.website} target="_blank" rel="noreferrer"><Globe size={13}/>Website</a>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
