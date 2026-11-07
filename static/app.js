// static/app.js
// Tim kiem user realtime
const us = document.getElementById('userSearch');
if (us) {
  us.addEventListener('input', () => {
    const q = us.value.toLowerCase();
    document.querySelectorAll('#userTable tbody tr').forEach(tr => {
      const n = tr.querySelector('.uname').textContent.toLowerCase();
      tr.style.display = n.includes(q) ? '' : 'none';
    });
  });
}

// Goi API JSON
async function api(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: body || ''
  });
  try { return await res.json(); } catch { return {ok:false}; }
}

document.querySelectorAll('.btn-add').forEach(b => b.addEventListener('click', async () => {
  const v = prompt('So tien can cong:'); if (!v) return;
  const r = await api(`/admin/user/${b.dataset.id}/balance`, `delta=${encodeURIComponent(v)}`);
  if (r.ok) b.closest('tr').querySelector('.ubal').textContent = Number(r.balance).toLocaleString('vi-VN');
  else alert('Loi');
}));

document.querySelectorAll('.btn-sub').forEach(b => b.addEventListener('click', async () => {
  const v = prompt('So tien can tru:'); if (!v) return;
  const r = await api(`/admin/user/${b.dataset.id}/balance`, `delta=${-Math.abs(Number(v))}`);
  if (r.ok) b.closest('tr').querySelector('.ubal').textContent = Number(r.balance).toLocaleString('vi-VN');
  else alert('Loi');
}));

document.querySelectorAll('.btn-role').forEach(b => b.addEventListener('click', async () => {
  if (!confirm('Doi quyen?')) return;
  const r = await api(`/admin/user/${b.dataset.id}/role`);
  if (r.ok) b.closest('tr').querySelector('.urole').textContent = r.role;
  else alert('Khong the doi quyen admin goc');
}));

document.querySelectorAll('.btn-del').forEach(b => b.addEventListener('click', async () => {
  if (!confirm('Xoa vinh vien?')) return;
  const r = await api(`/admin/user/${b.dataset.id}/delete`);
  if (r.ok) b.closest('tr').remove();
  else alert('Khong the xoa admin goc');
}));