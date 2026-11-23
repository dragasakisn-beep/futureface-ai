(() => {
 const photo=document.getElementById("photo"), generate=document.getElementById("generate"), result=document.getElementById("result"), status=document.getElementById("genStatus");
 const canvas=document.getElementById("canvas");
 if(!photo||!generate||!result||!status) return;
 const button=generate.cloneNode(true);
 button.textContent="Generate REAL AI portrait";
 generate.replaceWith(button);
 const fresh=button.cloneNode(true);
 button.replaceWith(fresh);
 // Capture click before the original local-poster handler can run.
 fresh.addEventListener("click",async ev=>{
  ev.preventDefault();ev.stopImmediatePropagation();
  const file=photo.files?.[0];
  if(!file){status.textContent="Upload a photo first.";return}
  const timeline=document.querySelector('input[name="timeline"]:checked')?.value;
  const base=(window.FUTUREFACE_API_BASE||"").replace(/\/$/,"");
  if(!base){status.textContent="AI backend URL is not configured.";return}
  fresh.disabled=true;fresh.textContent="Generating portrait…";result.classList.add("hidden");status.textContent="Generating with OpenAI. This may take a minute.";
  try{
   const form=new FormData();form.append("photo",file);form.append("timeline",timeline);
   const response=await fetch(base+"/api/transform",{method:"POST",body:form});
   const json=await response.json();
   if(!response.ok)throw Error(json.detail||"Generation failed");
   const img=new Image();img.onload=()=>{
    const ctx=canvas.getContext("2d");ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    result.classList.remove("hidden");status.textContent="AI-generated portrait ready. Download or share it.";
   };img.onerror=()=>{status.textContent="Generated image could not be displayed."};img.src=json.image;
  }catch(err){status.textContent="AI generation unavailable: "+err.message}
  finally{fresh.disabled=false;fresh.textContent="Generate REAL AI portrait"}
 },true);
 // Existing photo change handler updates disabled state of the original node.
 photo.addEventListener("change",()=>{fresh.disabled=!photo.files?.length});
 document.getElementById("remove")?.addEventListener("click",()=>{fresh.disabled=true});
})();
