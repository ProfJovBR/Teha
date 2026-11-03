import {createClient} from '@supabase/supabase-js';
const url=new URL(location.href),query=url.searchParams,fragment=new URLSearchParams(url.hash.slice(1));
const tokenHash=query.get('token_hash'),type=query.get('type'),code=query.get('code');
const linkError=query.get('error')||fragment.get('error');
const cloud=createClient(__SUPABASE_URL__,__SUPABASE_KEY__,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storage:sessionStorage}});
const $=id=>document.getElementById(id);
function show(state){
 const states={
  success:['✓','Conta confirmada!','Seu e-mail foi validado. Você já pode acessar seu espaço no Teha.'],
  expired:['↻','Este link não é mais válido','Ele pode ter expirado ou já ter sido usado. Tente entrar na conta ou solicite um novo link abaixo.'],
  missing:['✉','Confirme seu e-mail','Abra o link enviado para seu e-mail. Se precisar, solicite um novo link abaixo.'],
  pending:['✉','Falta só confirmar','Clique abaixo para validar seu e-mail e liberar o acesso à sua conta.'],
  unavailable:['!','Não conseguimos verificar agora','Confira sua conexão e tente abrir o link novamente. Você também pode solicitar um novo link.']
 };
 const [symbol,title,description]=states[state];$('symbol').textContent=symbol;$('title').textContent=title;$('description').textContent=description;
 $('confirm').hidden=state!=='pending';$('continue').hidden=state==='pending';$('resend').hidden=state==='success'||state==='pending';
}
async function verifiedSession(){const {data,error}=await cloud.auth.getUser();if(error||!data.user?.email_confirmed_at)return false;return true;}
async function verifyHash(){
 $('confirm').disabled=true;$('description').textContent='Validando seu e-mail…';
 try{const {error}=await cloud.auth.verifyOtp({token_hash:tokenHash,type:'email'});if(error)throw error;show(await verifiedSession()?'success':'expired');}
 catch(error){show(error.status===0||error.name==='AuthRetryableFetchError'?'unavailable':'expired');}
 finally{history.replaceState(null,'','/confirmar/');$('confirm').disabled=false;}
}
$('confirm').onclick=verifyHash;
$('resend').onsubmit=async event=>{
 event.preventDefault();const button=$('resendButton');button.disabled=true;$('resendMessage').textContent='Enviando…';
 try{
  const {error}=await cloud.auth.resend({type:'signup',email:$('email').value.trim(),options:{emailRedirectTo:'https://teha-odontologia.pages.dev/confirmar'}});
  if(error)throw error;
  $('resendMessage').textContent='Se houver um cadastro pendente para este e-mail, enviaremos um novo link. Confira também o spam.';
  let seconds=60;button.textContent='Aguarde '+seconds+'s para reenviar';const timer=setInterval(()=>{seconds--;button.textContent='Aguarde '+seconds+'s para reenviar';if(seconds<=0){clearInterval(timer);button.disabled=false;button.textContent='Enviar novo link de confirmação';}},1000);
 }catch(error){$('resendMessage').textContent=error.status===429?'Muitas tentativas. Aguarde alguns minutos antes de reenviar.':'Não foi possível enviar agora. Confira o e-mail e tente novamente em alguns instantes.';button.disabled=false;}
};
(async()=>{
 try{
  if(linkError){show('expired');history.replaceState(null,'','/confirmar/');return;}
  if(tokenHash){if(type&&!['email','signup'].includes(type)){show('expired');history.replaceState(null,'','/confirmar/');return;}show('pending');return;}
  if(code){const {error}=await cloud.auth.exchangeCodeForSession(code);if(error)throw error;}
  const {data,error}=await cloud.auth.getSession();if(error)throw error;
  show(data.session&&await verifiedSession()?'success':fragment.has('access_token')||code?'expired':'missing');
  history.replaceState(null,'','/confirmar/');
 }catch(error){show(error.status===0||error.name==='AuthRetryableFetchError'?'unavailable':'expired');history.replaceState(null,'','/confirmar/');}
})();
