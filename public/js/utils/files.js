function fileData(file){return new Promise((resolve,reject)=>{let r=new FileReader;r.onload=()=>resolve(r.result);r.onerror=()=>reject(Error('Could not read image'));r.readAsDataURL(file)})}
