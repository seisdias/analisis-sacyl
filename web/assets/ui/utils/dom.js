// web/assets/ui/utils/dom.js

export function escapeHtml(s){
  const re = new RegExp('[&<>"\']', 'g');
  return String(s).replace(re, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

export function deepCopy(obj){ return JSON.parse(JSON.stringify(obj || {})); }

export function numOrNull(v){
  if(v === "" || v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}