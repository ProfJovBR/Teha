let signupMode=false,cloudChannel=null,openingUser=null,authGeneration=0;
function showAuth(text=''){
 ready=false;demoMode=false;accessInfo={role:'blocked'};cloudUser=null;authGeneration++;
 $('workspace').hidden=true;$('workspace').inert=true;$('authScreen').hidden=false;
 $('authMessage').textContent=text;
 for(const name of stores)state[name]=[];
 for(const key of Object.keys(schemas))resetForm(key);
 currentProfile={id:'profile',name:'Seu nome',photo:''};renderProfile();
 if(cloudChannel){cloud.removeChannel(cloudChannel);cloudChannel=null;}
}
async function connectSession(session){
 if(!session){if(new URLSearchParams(location.search).has('entrar'))showAuth();else startDemo();return;}
 if(openingUser===session.user.id)return;
 if(cloudUser?.id===session.user.id&&ready)return;
 openingUser=session.user.id;const generation=++authGeneration;
 try{
  demoMode=false;cloudUser=session.user;
  $('authMessage').textContent='Carregando seu espaço…';
  const {error}=await cloud.rpc('teha_seed_demo');if(error)throw error;
  await refresh();await loadProfile();
  if(generation!==authGeneration)return;
  ready=true;$('signOut').textContent='Sair';$('authScreen').hidden=true;$('workspace').hidden=false;$('workspace').inert=false;
  $('dbStatus').textContent='Supabase conectado';$('connectionState').textContent='Conectado à nuvem';
  document.querySelector('#inicio .notice').textContent='Dados da sua conta salvos no banco Clinica. Acesso compartilhado por equipe e assinatura digital ainda pendentes.';page(accessInfo.role==='management'?'relatorios':'inicio');
  cloudChannel=cloud.channel('teha-'+session.user.id).on('postgres_changes',{event:'*',schema:'public',table:'teha_records',filter:'owner_id=eq.'+session.user.id},()=>{if(ready)refresh().catch(()=>{$('connectionState').textContent='Falha ao atualizar — tente novamente';})}).subscribe();
 }catch(error){showAuth('Não foi possível carregar sua conta: '+error.message);}
 finally{openingUser=null;}
}
$('authMode').hidden=true;
$('authMode').onclick=()=>{signupMode=!signupMode;$('authSubmit').textContent=signupMode?'Criar conta':'Entrar';$('authMode').textContent=signupMode?'Já tenho conta':'Criar minha conta';$('authPassword').autocomplete=signupMode?'new-password':'current-password';$('authPassword').minLength=signupMode?12:1;$('authMessage').textContent='';};
$('authForm').onsubmit=async e=>{
 e.preventDefault();const b=$('authSubmit');b.disabled=true;
 try{
  const credentials={email:$('authEmail').value.trim(),password:$('authPassword').value};
  const result=signupMode?await cloud.auth.signUp({...credentials,options:{emailRedirectTo:'https://teha-odontologia.pages.dev/confirmar'}}):await cloud.auth.signInWithPassword(credentials);
  if(result.error)throw result.error;
  $('authPassword').value='';
  if(result.data.session)await connectSession(result.data.session);
  else $('authMessage').textContent='Conta criada. Confirme seu e-mail e depois entre com sua senha.';
 }catch(error){$('authMessage').textContent=error.message;}
 finally{b.disabled=false;}
};
$('signOut').onclick=async()=>{if(demoMode){showAuth();return;}const {error}=await cloud.auth.signOut();if(error){msg('Não foi possível encerrar a sessão: '+error.message);return}showAuth('Sessão encerrada.');};
cloud.auth.onAuthStateChange((event,session)=>{if(event==='SIGNED_OUT')showAuth('Sessão encerrada.');else if(event==='SIGNED_IN')setTimeout(()=>connectSession(session),0);});
const {data:{session},error:sessionError}=await cloud.auth.getSession();
if(sessionError)showAuth(sessionError.message);else await connectSession(session);
window.addEventListener('offline',()=>{$('connectionState').textContent='Sem conexão — gravações indisponíveis';});
window.addEventListener('online',()=>{if(ready)refresh().then(()=>{$('connectionState').textContent='Conectado à nuvem';}).catch(e=>msg(e.message));});
// Polling fallback also detects updates if the realtime service is temporarily unavailable.
setInterval(()=>{if(ready&&navigator.onLine&&!document.hidden)refresh().catch(()=>{$('connectionState').textContent='Falha ao atualizar — seus registros não foram apagados';});},15000);

function startDemo(){
 demoMode=true;accessInfo={role:'doctor'};cloudUser=null;ready=true;
 for(const name of stores)demoRecords[name]=[];
 ['Ana Oliveira','Bruno Almeida','Carla Souza','Diego Martins','Elisa Ferreira','Fábio Costa'].forEach((name,i)=>demoRecords.patients.push({id:'demo-patient-'+i,name:name+' (teste)',phone:'',remarks:'Paciente fictício de demonstração',createdAt:now(),_revision:1}));
 demoRecords.team.push({id:'demo-dentist',name:'Dentista de demonstração',role:'Dentista',_revision:1});
 demoRecords.patients[1].allergies='Penicilina (exemplo fictício)';
 const arrived=minutes=>new Date(Date.now()-minutes*60000).toISOString();
 const examples=[['09:00',0,'Avaliação inicial','Em atendimento',25],['09:45',1,'Restauração','Na sala de espera',12],['10:30',2,'Retorno','Na sala de espera',5],['11:15',3,'Limpeza','Confirmado',0]];
 demoRecords.appointments=examples.map(([time,index,procedure,status,minutes],i)=>({id:'demo-appointment-'+i,patient:'demo-patient-'+index,professional:'demo-dentist',date:day(),time,duration:30,chair:'Sala 1',procedure,status,...(minutes?{arrivedAt:arrived(minutes)}:{}),createdAt:now(),_revision:1}));

 $('authScreen').hidden=true;$('workspace').hidden=false;$('workspace').inert=false;
 $('signOut').textContent='Entrar na nuvem';
 $('connectionState').textContent='Demonstração • dados temporários';$('dbStatus').textContent='Clinica • entre para salvar na nuvem';
 document.querySelector('#inicio .notice').textContent='Demonstração com dados fictícios e temporários. Entre na sua conta para salvar os registros no banco Clinica. Recarregar a página reinicia os exemplos.';
 refresh().then(()=>page(accessInfo.role==='management'?'relatorios':'inicio')).catch(e=>msg(e.message));
}
$('viewDemo').onclick=startDemo;
