export function getBaseUrl(){
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get("base") || "";
}

export async function apiGet(base, path){
  const res = await fetch(`${base}${path}`);
  if(!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}
