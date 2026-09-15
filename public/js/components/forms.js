function fd(f){return Object.fromEntries(new FormData(f))}
function input(n,l,t='text',v='',required=false){return `<label>${l}<input name="${n}" type="${t}" value="${esc(v)}" ${required?'required':''}></label>`}
