export const state = {
  base: "",
  meta: null,
  ranges: null,
  currentGroup: null,
  enabledParams: new Set(),
  sessionId: null,
};

export function labelOf(param){
  const meta = state.meta;
  return (meta && meta.defs && meta.defs[param] && meta.defs[param].label) ? meta.defs[param].label : param;
}
