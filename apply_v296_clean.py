from pathlib import Path

p = Path('index.html')
html = p.read_text(encoding='utf-8')
html = html.replace("const APP_VERSION = '2.9.5';", "const APP_VERSION = '2.9.6';")

old = '''      <div class="management-actions">
        <button class="management-action primary" data-manager-reset="${escapeHtml(m.id)}" data-manager-email="${escapeHtml(m.email)}">Şifre Sıfırla</button>
        <button class="management-action ${m.active?'danger':'success'}" data-manager-toggle="${escapeHtml(m.id)}" data-manager-active="${m.active?'1':'0'}">${m.active?'Pasif Yap':'Aktif Yap'}</button>
      </div>'''
new = '''      <div class="management-actions">
        <button class="management-action edit" data-manager-edit="${escapeHtml(m.id)}">Düzenle</button>
        <button class="management-action primary" data-manager-reset="${escapeHtml(m.id)}" data-manager-email="${escapeHtml(m.email)}">Şifre Sıfırla</button>
        <button class="management-action ${m.active?'danger':'success'}" data-manager-toggle="${escapeHtml(m.id)}" data-manager-active="${m.active?'1':'0'}">${m.active?'Pasif Yap':'Aktif Yap'}</button>
      </div>'''
if old not in html:
    raise SystemExit('Manager action block not found')
html = html.replace(old, new, 1)

anchor = 'function bindManagementCenter(){'
pos = html.find(anchor)
if pos < 0:
    raise SystemExit('bindManagementCenter not found')

helpers = '''
function closeManagerEditModal(){
  document.querySelector('.manager-edit-modal')?.remove();
}
function openManagerEditModal(managerId){
  const data=window.__visiteenManagementData;
  const manager=(data?.managers||[]).find(m=>m.id===managerId);
  if(!manager)return toast('Yönetici kaydı bulunamadı.','error');
  const institutions=(data?.institutions||[]).filter(i=>i.active);
  closeManagerEditModal();
  const modal=document.createElement('div');
  modal.className='manager-edit-modal';
  modal.innerHTML=`<div class="manager-edit-panel">
    <button class="manager-edit-close" aria-label="Kapat">×</button>
    <div class="manager-edit-kicker">SUPER ADMIN İŞLEMİ</div>
    <h2>Yönetici Bilgilerini Düzenle</h2>
    <p>Yönetici hesabının temel bilgilerini ve bağlı olduğu kurumu güncelleyebilirsiniz.</p>
    <label class="manager-edit-field"><span>Ad Soyad</span><input id="editManagerName" value="${escapeHtml(manager.full_name||'')}" placeholder="Yönetici adı soyadı"></label>
    <label class="manager-edit-field"><span>E-posta</span><input id="editManagerEmail" type="email" value="${escapeHtml(manager.email||'')}" placeholder="yonetici@okul.com"></label>
    <label class="manager-edit-field"><span>Bağlı Kurum</span><select id="editManagerInstitution">${institutions.map(i=>`<option value="${escapeHtml(i.id)}" ${i.id===manager.institution_id?'selected':''}>${escapeHtml(i.name)} • ${escapeHtml(i.code)}</option>`).join('')}</select></label>
    <div class="manager-edit-info"><strong>Not:</strong> Şifre değişikliği bu ekrandan yapılmaz. Şifre işlemleri kart üzerindeki <b>Şifre Sıfırla</b> butonundan yönetilir.</div>
    <div class="manager-edit-actions"><button class="btn btn-ghost" id="cancelManagerEdit">Vazgeç</button><button class="btn btn-primary" id="saveManagerEdit">Değişiklikleri Kaydet</button></div>
  </div>`;
  document.body.appendChild(modal);
  const save=async()=>{
    const fullName=(document.getElementById('editManagerName')?.value||'').trim();
    const email=(document.getElementById('editManagerEmail')?.value||'').trim().toLowerCase();
    const institutionId=document.getElementById('editManagerInstitution')?.value||'';
    if(!email||!institutionId)return toast('E-posta ve kurum alanları zorunludur.','error');
    const btn=document.getElementById('saveManagerEdit');
    if(btn){btn.disabled=true;btn.textContent='Kaydediliyor…';}
    try{
      const auth=centralManagerSession();
      const result=await visiteenRpc('superadmin_update_manager',{p_token:auth.token,p_manager_id:managerId,p_full_name:fullName||null,p_email:email,p_institution_id:institutionId});
      if(!result?.ok)throw new Error(result?.error||'Yönetici bilgileri güncellenemedi.');
      toast('Yönetici bilgileri başarıyla güncellendi.','success');
      closeManagerEditModal();
      await renderAcademyDashboard();
    }catch(e){
      toast(e.message||'Yönetici bilgileri güncellenemedi.','error');
      if(btn){btn.disabled=false;btn.textContent='Değişiklikleri Kaydet';}
    }
  };
  modal.querySelector('.manager-edit-close').onclick=closeManagerEditModal;
  document.getElementById('cancelManagerEdit').onclick=closeManagerEditModal;
  document.getElementById('saveManagerEdit').onclick=save;
  modal.addEventListener('click',e=>{if(e.target===modal)closeManagerEditModal();});
}
'''
html = html[:pos] + helpers + html[pos:]

old_bind = '''  document.querySelectorAll('[data-manager-reset]').forEach(b=>b.onclick=()=>resetManagerPassword(b.dataset.managerReset,b.dataset.managerEmail));
  document.querySelectorAll('[data-manager-toggle]').forEach(b=>b.onclick=()=>toggleManagerActive(b.dataset.managerToggle,b.dataset.managerActive==='1'));
  document.querySelectorAll('[data-inst-toggle]').forEach(b=>b.onclick=()=>toggleInstitutionActive(b.dataset.instToggle,b.dataset.instActive==='1'));'''
new_bind = '''  document.querySelectorAll('[data-manager-edit]').forEach(b=>b.onclick=()=>openManagerEditModal(b.dataset.managerEdit));
  document.querySelectorAll('[data-manager-reset]').forEach(b=>b.onclick=()=>resetManagerPassword(b.dataset.managerReset,b.dataset.managerEmail));
  document.querySelectorAll('[data-manager-toggle]').forEach(b=>b.onclick=()=>toggleManagerActive(b.dataset.managerToggle,b.dataset.managerActive==='1'));
  document.querySelectorAll('[data-inst-toggle]').forEach(b=>b.onclick=()=>toggleInstitutionActive(b.dataset.instToggle,b.dataset.instActive==='1'));'''
if old_bind not in html:
    raise SystemExit('Management binding block not found')
html = html.replace(old_bind, new_bind, 1)

needle = '''    const rows=dashboardRowsFromCentral(data);
    const isSuper=data.role==='super_admin';'''
replacement = '''    const rows=dashboardRowsFromCentral(data);
    const isSuper=data.role==='super_admin';
    window.__visiteenManagementData=data;'''
if needle not in html:
    raise SystemExit('Dashboard data marker not found')
html = html.replace(needle, replacement, 1)

css = '''
/* V2.9.6 • Super Admin kullanıcı düzenleme */
.management-action.edit{background:linear-gradient(135deg,#EEF4FF,#F4EEFF);border-color:#D8DEFF;color:#3E2ACF}
.management-action.edit:hover{background:linear-gradient(135deg,#E4EDFF,#EEE5FF)}
.manager-edit-modal{position:fixed;inset:0;z-index:1400;display:grid;place-items:center;padding:18px;background:rgba(20,26,66,.72);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.manager-edit-panel{width:min(520px,100%);position:relative;padding:28px;border-radius:26px;background:#fff;border:1px solid rgba(91,44,255,.14);box-shadow:0 30px 90px rgba(16,25,76,.32)}
.manager-edit-close{position:absolute;right:15px;top:15px;width:40px;height:40px;border-radius:12px;border:1px solid #DDE4F1;background:#fff;color:#2F4296;font-size:22px;cursor:pointer}
.manager-edit-kicker{color:#11A996;font-size:10px;font-weight:950;letter-spacing:.11em}
.manager-edit-panel h2{margin:7px 46px 7px 0;color:#4329CF;font-size:24px}
.manager-edit-panel>p{margin:0 0 18px;color:#6C7891;font-size:12px;line-height:1.5}
.manager-edit-field{display:block;margin-top:13px}
.manager-edit-field span{display:block;margin-bottom:7px;color:#475A80;font-size:11px;font-weight:900}
.manager-edit-field input,.manager-edit-field select{width:100%;height:47px;border-radius:13px;border:1px solid #DCE4F1;background:#FBFCFF;padding:0 13px;color:#253964;outline:none}
.manager-edit-field input:focus,.manager-edit-field select:focus{border-color:#6840EB;box-shadow:0 0 0 4px rgba(104,64,235,.09)}
.manager-edit-info{margin-top:15px;padding:12px 13px;border-radius:13px;background:#F5F7FC;border:1px solid #E2E8F2;color:#66728C;font-size:10.5px;line-height:1.45}
.manager-edit-info strong{color:#3C4F83}
.manager-edit-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:19px}
@media(max-width:560px){.manager-edit-panel{padding:22px 18px}.manager-edit-actions{flex-direction:column-reverse}.manager-edit-actions .btn{width:100%}}
'''
html = html.replace('</style>', css + '\n</style>', 1)
p.write_text(html, encoding='utf-8')
print('V2.9.6 safe patch applied')
