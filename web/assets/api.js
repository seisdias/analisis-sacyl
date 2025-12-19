export function getBaseUrl(){
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get("base") || "";
}

export function getSessionId(){
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get("session_id") || "";
}

export async function apiGet(base, path){
  const sid = getSessionId();
  const url = new URL(`${base}${path}`, window.location.origin);

  if(sid){
    url.searchParams.set("session_id", sid);
  }

  const res = await fetch(url.toString());
  if(!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}
