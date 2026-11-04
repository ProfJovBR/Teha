import {createClient} from '@supabase/supabase-js';
let demoMode=false,demoRecords={},accessInfo={role:'blocked'};
const rolePages={doctor:['inicio','pacientes','agenda','triagem','prontuario','odontograma','tratamentos','documentos'],reception:['inicio','pacientes','agenda','triagem'],management:['relatorios','financeiro','equipe']};
function hasRole(role){return (accessInfo.roles||[accessInfo.role]).includes(role);}
function canPage(id){return hasRole('admin')||(accessInfo.roles||[accessInfo.role]).some(role=>(rolePages[role]||[]).includes(id));}
function applyAccess(){document.querySelectorAll('nav [data-page]').forEach(el=>el.hidden=!canPage(el.dataset.page));$('adminHistory').hidden=accessInfo.role!=='admin';$('doctorSearch').hidden=!canPage('pacientes');const clinical=canPage('prontuario');$('doctorCurrent').closest('article').hidden=!clinical;$('doctorAlerts').closest('article').hidden=!clinical;const active=document.querySelector('.content>section:not([hidden])');if(active&&!canPage(active.id))page(accessInfo.role==='management'?'relatorios':'inicio');}

const cloud=createClient(__SUPABASE_URL__,__SUPABASE_KEY__,{
 auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storage:sessionStorage}
});
async function readSnapshot(){
 if(demoMode)return structuredClone(demoRecords);
 if(!cloudUser)throw new Error('Entre na sua conta.');
 const recordsPage=offset=>cloud.from('teha_records').select('store,data,version').eq('owner_id',cloudUser.id).order('store').order('id').range(offset,offset+499);
 // Both requests enforce current database permissions independently.
 const [permissions,firstPage]=await Promise.all([cloud.rpc('teha_access'),recordsPage(0)]);
 const {data:access,error:accessError}=permissions;if(accessError)throw accessError;accessInfo=access;if(!['admin','doctor','reception','management'].includes(accessInfo.role)){showAuth('Sua conta está sem perfil de acesso. Solicite a liberação ao administrador.');throw new Error('Perfil de acesso não autorizado.');}
 const grouped={};for(const name of stores)grouped[name]=[];
 for(let offset=0;;offset+=500){
  const {data,error}=offset===0?firstPage:await recordsPage(offset);
  if(error)throw error;
  for(const row of data||[])if(grouped[row.store])grouped[row.store].push({...row.data,_revision:row.version});
  if((data||[]).length<500)break;
 }
 if(accessInfo.role==='admin'){const {data:audits,error}=await cloud.from('teha_history').select('id,at,actor,store,record_id').order('at',{ascending:false}).limit(100);
 if(error)throw error;
 grouped.audit=(audits||[]).map(a=>({id:String(a.id),createdAt:a.at,author:a.actor,action:'Gravação na nuvem',store:a.store,recordId:a.record_id}));
 }
 if((hasRole('doctor')||hasRole('reception'))&&!hasRole('management')&&!hasRole('admin'))grouped.team=accessInfo.team||[];if(hasRole('management')&&!hasRole('doctor')&&!hasRole('reception')&&!hasRole('admin'))grouped.patients=accessInfo.patients||[];if(hasRole('doctor')&&!hasRole('management')&&accessInfo.clinic?.id)grouped.settings.push(accessInfo.clinic);
 return grouped;
}
