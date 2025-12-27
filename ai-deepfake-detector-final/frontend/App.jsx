
import React, {useState} from 'react';

export default function App(){
  const [file,setFile]=useState(null);
  const [res,setRes]=useState('');

  async function send(){
    const f=new FormData();
    f.append('file',file);
    f.append('type','image');
    const r=await fetch('http://localhost:8000/api/upload',{
      method:'POST',
      headers:{'X-API-KEY':'change_me'},
      body:f
    });
    const j=await r.json();
    setRes(JSON.stringify(j));
  }

  return (
    <div>
      <h2>AI Deepfake Detector</h2>
      <input type='file' onChange={e=>setFile(e.target.files[0])}/>
      <button onClick={send}>Analyze</button>
      <pre>{res}</pre>
    </div>
  );
}
