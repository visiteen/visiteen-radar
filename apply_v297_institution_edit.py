from pathlib import Path
p=Path('index.html')
html=p.read_text(encoding='utf-8')
html=html.replace("const APP_VERSION = '2.9.6';", "const APP_VERSION = '2.9.7';")

old='''        <button class="management-action ${i.active?'danger':'success'}" data-inst-toggle="${escapeHtml(i.id)}" data-inst-active="${i.active?'1':'0'}">${i.active?'Kurumu Pasif Yap':'Kurumu Aktif Yap'}</button>'''
new='''        <button class="management-action edit" data-inst-edit="${escapeHtml(i.id)}">Düzenle</button>
        <button class="management-action ${i.active?'danger':'success'}" data-inst-toggle="${escapeHtml(i.id)}" data-inst-active="${i.active?'1':'0'}">${i.active?'Kurumu Pasif Yap':'Kurumu Aktif Yap'}</button>'''
if old not in html: raise SystemExit('Institution action button not found')
html=html.replace(old,new,1)

anchor='function closeManagerEditModal(){'
pos=html.find(anchor)
if pos<0: raise SystemExit('Manager edit helper anchor not found')
helpers='''function closeInstitutionEditModal(){
  document.querySelector('.institution-edit-modal')?.remove();
}
function openInstitutionEditModal(institutionId){
  const data=window.__visiteenManagementData;
  const institution=(data?.institutions||[]).find(i=>i.id===institutionId);
  if(!institution)return toast('Kurum kaydı bulunamadı.','error');
  closeInstitutionEditModal();
  const modal=document.createElement('div');
  modal.className='manager-edit-modal institution-edit-modal';
  modal.innerHTML=`<div class="manager-edit-panel">
    <button class="manager-edit-close" aria-label="Kapat">×</button>
    <div class="manager-edit-kicker">SUPER ADMIN İŞLEMİ</div>
    <h2>Kurum Bilgilerini Düzenle</h2>
    <p>Kurumun görünen adını ve öğretmenlerin girişte kullandığı kurum kodunu güncelleyebilirsiniz.</p>
    <label class="manager-edit-field"><span>Kurum Adı</span><input id="editInstitutionName" value="${escapeHtml(institution.name||'')}" placeholder="Kurum adı"></label>
    <label class="manager-edit-field"><span>Kurum Kodu</span><input id="editInstitutionCode" value="${escapeHtml(institution.code||'')}" placeholder="KURUM2026" autocomplete="off"></label>
    <div class="manager-edit-info"><strong>Kurum ID korunur.</strong> Bu işlem öğretmen, yönetici ve rapor bağlantılarını değiştirmez. Kurum kodu değiştirildiğinde sonraki girişlerde yeni kod kullanılmalıdır.</div>
    <div class="manager-edit-actions"><button class="btn btn-ghost" id="cancelInstitutionEdit">Vazgeç</button><button class="btn btn-primary" id="saveInstitutionEdit">Değişiklikleri Kaydet</button></div>
  </div>`;
  document.body.appendChild(modal);
  const save=async()=>{
    const name=(document.getElementById('editInstitutionName')?.value||'').trim();
    const code=(document.getElementById('editInstitutionCode')?.value||'').trim().toUpperCase().replace(/\\s+/g,'');
    if(!name||!code)return toast('Kurum adı ve kurum kodu zorunludur.','error');
    const btn=document.getElementById('saveInstitutionEdit');
    if(btn){btn.disabled=true;btn.textContent='Kaydediliyor…';}
    try{
      const auth=centralManagerSession();
      const result=await visiteenRpc('superadmin_update_institution',{p_token:auth.token,p_institution_id:institutionId,p_name:name,p_code:code});
      if(!result?.ok)throw new Error(result?.error||'Kurum bilgileri güncellenemedi.');
      toast('Kurum bilgileri başarıyla güncellendi.','success');
      closeInstitutionEditModal();
      await renderAcademyDashboard();
    }catch(e){
      toast(e.message||'Kurum bilgileri güncellenemedi.','error');
      if(btn){btn.disabled=false;btn.textContent='Değişiklikleri Kaydet';}
    }
  };
  modal.querySelector('.manager-edit-close').onclick=closeInstitutionEditModal;
  document.getElementById('cancelInstitutionEdit').onclick=closeInstitutionEditModal;
  document.getElementById('saveInstitutionEdit').onclick=save;
  modal.addEventListener('click',e=>{if(e.target===modal)closeInstitutionEditModal();});
}

'''
html=html[:pos]+helpers+html[pos:]

needle="""  document.querySelectorAll('[data-manager-edit]').forEach(b=>b.onclick=()=>openManagerEditModal(b.dataset.managerEdit));"""
replacement="""  document.querySelectorAll('[data-inst-edit]').forEach(b=>b.onclick=()=>openInstitutionEditModal(b.dataset.instEdit));
  document.querySelectorAll('[data-manager-edit]').forEach(b=>b.onclick=()=>openManagerEditModal(b.dataset.managerEdit));"""
if needle not in html: raise SystemExit('Management binding marker not found')
html=html.replace(needle,replacement,1)
p.write_text(html,encoding='utf-8')
print('V2.9.7 institution edit applied')
