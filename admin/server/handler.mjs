const OWNER_ID='0fd8e9a2-88e5-4c08-ab8f-a5635db8c3ee';
const OWNER_EMAIL='wcsam@outlook.com';
const ORIGIN='https://teha-admin.pages.dev';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export function createHandler(admin){return async function handler(req){
 const origin=req.headers.get('Origin');
 const headers={'Content-Type':'application/json','Cache-Control':'no-store','Vary':'Origin','Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Headers':'authorization,apikey,content-type,x-client-info','Access-Control-Allow-Methods':'POST, OPTIONS'};
 const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
 if(origin&&origin!==ORIGIN)return reply({error:'Origem não permitida.'},403);
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
 if(req.method!=='POST')return reply({error:'Método não permitido.'},405);
 const token=req.headers.get('Authorization')?.match(/^Bearer (.+)$/i)?.[1];
 if(!token)return reply({error:'Entre na sua conta.'},401);
 try{
  const {data:identity,error:authError}=await admin.auth.getUser(token);
  if(authError||!identity?.user)return reply({error:'Sessão inválida ou expirada.'},401);
  const actor=identity.user.id;
  if(actor!==OWNER_ID||identity.user.email?.toLowerCase()!==OWNER_EMAIL||!identity.user.email_confirmed_at)return reply({error:'Acesso exclusivo do proprietário.'},403);
  const {data:membership,error:memberError}=await admin.from('teha_admins').select('user_id').eq('user_id',actor).maybeSingle();
  if(memberError||!membership)return reply({error:'Sua conta não tem acesso ao painel administrativo.'},403);
  if(Number(req.headers.get('Content-Length')||0)>10000)return reply({error:'Solicitação muito grande.'},413);
  const raw=await req.text();if(raw.length>10000)return reply({error:'Solicitação muito grande.'},413);
  let body;try{body=JSON.parse(raw);}catch{return reply({error:'Solicitação inválida.'},400);}
  if(!body||typeof body!=='object'||Array.isArray(body))return reply({error:'Solicitação inválida.'},400);
  const action=body.action;
  if(action==='list'){
   const page=Math.max(1,Math.min(10000,Number.parseInt(body.page,10)||1));
   const {data,error}=await admin.auth.admin.listUsers({page,perPage:50});if(error)throw error;
   const users=data.users.map(u=>({id:u.id,email:u.email,name:u.user_metadata?.name||'',created_at:u.created_at,last_sign_in_at:u.last_sign_in_at,email_confirmed_at:u.email_confirmed_at,banned_until:u.banned_until}));
   return reply({users,page,total:data.total??null,hasMore:users.length===50,actor});
  }
  if(action==='audit'){
   const {data,error}=await admin.from('teha_admin_actions').select('id,actor_id,target_id,action,status,created_at,completed_at').order('created_at',{ascending:false}).limit(100);if(error)throw error;
   return reply({logs:data});
  }
  if(!['create_user','change_email','change_password'].includes(action))return reply({error:'Operação inválida.'},400);
  if(action!=='create_user'&&!UUID.test(body.id||''))return reply({error:'Usuário inválido.'},400);
  const email=String(body.email||'').trim().toLowerCase();
  if(action==='change_email'&&body.id===OWNER_ID&&email!==OWNER_EMAIL)return reply({error:'O e-mail proprietário está protegido. A alteração exige revisão pelo titular no Supabase.'},403);
  if(action!=='change_password'&&(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||email.length>254))return reply({error:'Informe um e-mail válido.'},400);
  if(action!=='change_email'&&(typeof body.password!=='string'||body.password.length<12||body.password.length>128))return reply({error:'Use uma senha de 12 a 128 caracteres.'},400);
  // Register intent before changing credentials. Passwords and tokens never enter the audit table.
  const {data:log,error:logError}=await admin.from('teha_admin_actions').insert({actor_id:actor,target_id:action==='create_user'?null:body.id,action}).select('id').single();
  if(logError)return reply({error:'Não foi possível registrar a auditoria; nenhuma alteração foi feita.'},503);
  const result=action==='create_user'?await admin.auth.admin.createUser({email,password:body.password,email_confirm:true,user_metadata:{name:String(body.name||'').trim().slice(0,100)}}):await admin.auth.admin.updateUserById(body.id,action==='change_email'?{email,email_confirm:true}:{password:body.password});
  const target=result.data?.user?.id||body.id||null;
  const {error:completeError}=await admin.from('teha_admin_actions').update({target_id:target,status:result.error?'failed':'success',completed_at:new Date().toISOString()}).eq('id',log.id);
  if(result.error)return reply({error:result.error.message||'Não foi possível alterar a conta.'},400);
  return reply({ok:true,id:target,warning:completeError?'A operação foi concluída, mas a finalização da auditoria está pendente.':undefined});
 }catch{return reply({error:'Não foi possível concluir a operação. Tente novamente.'},500);}
};}
