export const state = {
  base: "",
  sessionId: "",
  meta: null,
  ranges: null,
  currentGroup: null,
  enabledParams: new Set(),
};


export function labelOf(param){
  const meta = state.meta;
  return (meta && meta.defs && meta.defs[param] && meta.defs[param].label) ? meta.defs[param].label : param;
}
