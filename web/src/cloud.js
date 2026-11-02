import {createClient} from '@supabase/supabase-js';
let demoMode=false,demoRecords={};
const cloud=createClient(__SUPABASE_URL__,__SUPABASE_KEY__,{
 auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storage:sessionStorage}
});
async function readSnapshot(){
 if(demoMode)return structuredClone(demoRecords);
 if(!cloudUser)throw new Error('Entre na sua conta.');
 const grouped={};for(const name of stores)grouped[name]=[];
 for(let offset=0;;offset+=500){
  const {data,error}=await cloud.from('teha_records').select('store,data,version').eq('owner_id',cloudUser.id).order('store').order('id').range(offset,offset+499);
  if(error)throw error;
  for(const row of data||[])if(grouped[row.store])grouped[row.store].push({...row.data,_revision:row.version});
  if((data||[]).length<500)break;
 }
 const {data:audits,error}=await cloud.from('teha_history').select('id,at,actor,store,record_id').eq('owner_id',cloudUser.id).order('at',{ascending:false}).limit(100);
 if(error)throw error;
 grouped.audit=(audits||[]).map(a=>({id:String(a.id),createdAt:a.at,author:a.actor,action:'Gravação na nuvem',store:a.store,recordId:a.record_id}));
 return grouped;
}
