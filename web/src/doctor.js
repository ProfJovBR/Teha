// Clinical dashboard. All counts and alerts derive from the current account's records.
const doctorPaths={
 calendar:'M8 2v4m8-4v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2Z',
 waiting:'M4 13V9a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v4M3 12h18v6H3Zm2 6v3m14-3v3',
 return:'M4 10a8 8 0 1 1 1 8M4 3v7h7',
 care:'M6 3v6a4 4 0 0 0 8 0V3M4 3h4m4 0h4m-6 10v3a5 5 0 0 0 10 0v-3m0-4a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z',
 alert:'m12 3 10 18H2L12 3Zm0 6v5m0 3v1',
 notes:'M9 4h6v4H9ZM7 6H4v16h16V6h-3M8 12h8m-8 4h8',
 tooth:'M12 5c-3-3-9-2-9 3 0 4 2 6 3 11 1 4 3 3 4-2 1-4 3-4 4 0 1 5 3 6 4 2 1-5 3-7 3-11 0-5-6-6-9-3Z',
 treatment:'m12 2 10 5-10 5L2 7l10-5Zm-10 10 10 5 10-5M2 17l10 5 10-5',
 patients:'M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m14-15a4 4 0 0 1 0 8m6 7v-2a4 4 0 0 0-3-4M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
 home:'m3 10 9-8 9 8v11h-6v-7H9v7H3V10Z',
 documents:'M14 2H4v20h16V8l-6-6Zm0 0v6h6'
};
function doctorIcon(name){return '<svg class="doctor-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="'+(doctorPaths[name]||doctorPaths.notes)+'"/></svg>';}
document.querySelectorAll('[data-icon]').forEach(el=>el.innerHTML=doctorIcon(el.dataset.icon));
for(const [pageId,iconName] of Object.entries({inicio:'home',agenda:'calendar',pacientes:'patients',prontuario:'notes',odontograma:'tooth',tratamentos:'treatment',documentos:'documents'})){const icon=document.querySelector('nav [data-page="'+pageId+'"] .nav-icon');if(icon)icon.innerHTML=doctorIcon(iconName);}
// Keep existing modules available while placing the daily agenda before patients.
const agendaNav=document.querySelector('nav [data-page="agenda"]'),patientsNav=document.querySelector('nav [data-page="pacientes"]');if(agendaNav&&patientsNav)patientsNav.before(agendaNav);
function doctorText(tag,text,className=''){const el=document.createElement(tag);el.textContent=text;if(className)el.className=className;return el;}
function doctorEmpty(host,text){host.append(doctorText('div',text,'doctor-empty'));}
function doctorOpenPatient(patient,section='prontuario',professional=''){
 page(section);
 if(section==='odontograma'){selectedTeeth.clear();$('toothPatient').value=patient;renderTeeth();return;}
 const filter=$('filter-'+section),form=$('form-'+section);
 if(form)resetForm(section);
 if(filter)filter.value=patient;
 if(form?.elements.patient)form.elements.patient.value=patient;
 if(professional&&form?.elements.professional)form.elements.professional.value=professional;
 renderList(section);if(section==='prontuario')renderTriageHistory();
}
async function doctorStartCare(id){if(!canPage('prontuario')){openAssessment(id);return;}let a=state.appointments.find(a=>a.id===id);if(!a)throw new Error('Consulta não encontrada.');if(['Agendado','Confirmado'].includes(a.status)){await arrive(id);a=state.appointments.find(a=>a.id===id);}if(a.status!=='Em atendimento'){if(a.status!=='Na sala de espera')throw new Error('Confirme a chegada antes de iniciar o atendimento.');await write('appointments',{...a,status:'Em atendimento',updatedAt:now()},'Iniciar atendimento');await refresh();}doctorOpenPatient(a.patient,'prontuario',a.professional);}
function doctorTodaysAppointments(){return (state.appointments||[]).filter(a=>a.date===day()).sort((a,b)=>a.time.localeCompare(b.time));}
function renderDoctorDashboard(){
 if(!$('doctorAgenda'))return;
 const registered=typeof cloudUser?.user_metadata?.name==='string'?cloudUser.user_metadata.name.trim():'';
 const name=(registered||(currentProfile?.name!=='Seu nome'?currentProfile?.name:'')||'').trim().split(/\s+/)[0];
 const hour=new Date().getHours(),greeting=hour<12?'Bom dia':hour<18?'Boa tarde':'Boa noite';
 $('doctorGreeting').textContent=name?greeting+', '+name:greeting+'! Seu consultório, em movimento.';
 const today=doctorTodaysAppointments(),waiting=today.filter(a=>a.arrivedAt&&a.status==='Na sala de espera').sort((a,b)=>a.arrivedAt.localeCompare(b.arrivedAt)),ongoing=today.filter(a=>a.status==='Em atendimento');
 $('doctorWaitingCount').textContent=waiting.length;
 $('doctorReturnCount').textContent=(state.appointments||[]).filter(a=>a.date>=day()&&/retorno/i.test(a.procedure||'')&&['Agendado','Confirmado','Na sala de espera'].includes(a.status)).length;
 $('doctorAgendaDate').textContent=new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'});
 const agenda=$('doctorAgenda');agenda.replaceChildren();
 if(!today.length)doctorEmpty(agenda,'Nenhuma consulta agendada para hoje. Use “Agendar consulta” para organizar os atendimentos.');
 for(const a of today){const row=document.createElement('article');row.className='doctor-appointment'+(a.status==='Em atendimento'?' current':'');row.append(doctorText('div',a.time,'doctor-time'));const person=document.createElement('div');person.className='doctor-person';person.append(doctorText('strong',patientName(a.patient)),doctorText('small',a.procedure||'Consulta'));const controls=document.createElement('div');controls.className='doctor-row-actions';const status=doctorText('span',a.status,'doctor-status'+(a.status==='Em atendimento'?' current':a.status==='Na sala de espera'?' waiting':['Cancelado','Faltou','Concluído'].includes(a.status)?' inactive':''));controls.append(status);
  if(a.status==='Em atendimento')controls.append(actionButton(canPage('prontuario')?'Abrir atendimento':'Ver triagem',()=>canPage('prontuario')?doctorOpenPatient(a.patient,'prontuario',a.professional):openAssessment(a.id)));
  else if(a.status==='Na sala de espera')controls.append(actionButton(canPage('prontuario')?'Iniciar atendimento':'Iniciar triagem',()=>doctorStartCare(a.id)));
  else if(['Agendado','Confirmado'].includes(a.status))controls.append(actionButton('Confirmar chegada',()=>arrive(a.id)));
  else if(canPage('prontuario'))controls.append(actionButton('Ver prontuário',()=>doctorOpenPatient(a.patient)));
  const editButton=actionButton('⋯',()=>{page('agenda');edit('agenda',a.id);});editButton.setAttribute('aria-label','Editar consulta de '+patientName(a.patient));controls.append(editButton);row.append(person,controls);agenda.append(row);
 }
 const queue=$('doctorWaitingList');queue.replaceChildren();if(!waiting.length)doctorEmpty(queue,'Nenhum paciente aguardando. Confirme a chegada pela agenda.');
 for(const a of waiting){const minutes=Math.max(0,Math.floor((Date.now()-Date.parse(a.arrivedAt))/60000));const b=actionButton('',()=>openAssessment(a.id));b.className='doctor-wait-row';b.append(doctorText('strong',patientName(a.patient)),doctorText('small',minutes+' min'));queue.append(b);}
 const current=$('doctorCurrent');current.replaceChildren();
 if(!ongoing.length)doctorEmpty(current,'Nenhum atendimento em andamento. Inicie um atendimento após confirmar a chegada do paciente.');
 else{const a=ongoing[0],grid=document.createElement('div');grid.className='doctor-current-grid';const info=document.createElement('div');info.className='doctor-current-info';info.append(doctorText('h3',patientName(a.patient)),doctorText('p',a.procedure||'Consulta'),doctorText('p','Profissional: '+teamName(a.professional)),doctorText('p','Horário agendado: '+a.time));if(a.notes)info.append(doctorText('p',a.notes));if(ongoing.length>1)info.append(doctorText('p',ongoing.length+' atendimentos em andamento. Consulte os demais na agenda.','doctor-summary-note'));const shortcutsHost=document.createElement('div'),shortcuts=document.createElement('div');shortcuts.className='doctor-shortcuts';for(const [label,section,icon] of [['Prontuário','prontuario','notes'],['Odontograma','odontograma','tooth'],['Plano de tratamento','tratamentos','treatment']]){const b=actionButton('',()=>doctorOpenPatient(a.patient,section,a.professional));b.innerHTML=doctorIcon(icon);b.append(document.createTextNode(label));shortcuts.append(b);}shortcutsHost.append(shortcuts);const resume=actionButton('Continuar atendimento →',()=>doctorOpenPatient(a.patient,'prontuario',a.professional));resume.className='doctor-continue';shortcutsHost.append(resume);grid.append(info,shortcutsHost);current.append(grid);}
 const alerts=$('doctorAlerts');alerts.replaceChildren();let alertCount=0;
 for(const id of new Set([...ongoing,...waiting].map(a=>a.patient))){const patient=state.patients?.find(p=>p.id===id);const note=(state.notes||[]).filter(n=>n.patient===id&&n.kind==='Anamnese').sort((a,b)=>(b.createdAt||'').localeCompare(a.createdAt||''))[0];const allergy=note?.allergies||patient?.allergies;if(!allergy)continue;const item=document.createElement('div');item.className='doctor-alert-item';item.append(doctorText('strong',patientName(id)),doctorText('p','Alergia informada: '+allergy),actionButton('Consultar anamnese',()=>{doctorOpenPatient(id);$('prontuario-kind').value='Anamnese';}));alerts.append(item);alertCount++;}
 if(!alertCount)doctorEmpty(alerts,'Nenhum alerta de alergia registrado para quem está aguardando ou em atendimento. Confira a anamnese antes de iniciar.');
}
$('doctorSchedule').onclick=()=>{page('agenda');newAppointment();};$('doctorCalendar').onclick=()=>{page('agenda');chooseDay(day());};$('doctorWaiting').onclick=showWaiting;
$('doctorSearch').onsubmit=e=>{e.preventDefault();const query=$('doctorSearchInput').value.trim();page('pacientes');$('search-pacientes').value=query;renderList('pacientes');};
setInterval(()=>{if(ready&&!document.hidden)renderDoctorDashboard();},30000);
