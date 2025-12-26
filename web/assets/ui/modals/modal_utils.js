// web/assets/ui/modals/modal_utils.js
import { state } from "../../state.js";

export function apiJson(method, path, body){
  return apiJsonInternal(method, path, body)
}

async function apiJsonInternal(method, path, body){
  const opts = { method, headers: {} };
  if(body !== undefined){
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${state.base}${path}`, opts);
  if(!res.ok){
    let txt = `${res.status} ${res.statusText}`;
    try{
      const j = await res.json();
      txt = j.detail || j.error || JSON.stringify(j);
    }catch{}
    throw new Error(txt);
  }
  return await res.json();
}
