const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const pageName = location.pathname.split('/').pop() || 'index.html';
const API_BASE = location.protocol === 'file:' ? 'http://127.0.0.1:5000/api' : `${location.origin}/api`;

const money = value => `Rs. ${Number(value || 0).toLocaleString('en-IN')}`;
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[s]));
const authToken = () => localStorage.getItem('roomiesToken') || '';
const authUser = () => JSON.parse(localStorage.getItem('roomiesUser') || 'null');
const storeAuth = data => {
  if (data.token) localStorage.setItem('roomiesToken', data.token);
  if (data.user) localStorage.setItem('roomiesUser', JSON.stringify(data.user));
};

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = authToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function toast(message, type = 'success') {
  let stack = $('.toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    document.body.appendChild(stack);
  }
  const item = document.createElement('div');
  item.className = `toast ${type}`;
  item.textContent = message;
  stack.appendChild(item);
  setTimeout(() => item.remove(), 3600);
}

function formDataObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function setButtonLoading(button, loadingText = 'Saving...') {
  if (!button) return () => {};
  const oldText = button.textContent;
  button.disabled = true;
  button.textContent = loadingText;
  return () => { button.disabled = false; button.textContent = oldText; };
}

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    if (!file) return resolve(null);
    if (file.size > 5 * 1024 * 1024) return reject(new Error('Image must be below 5MB'));
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Unable to read image file'));
    reader.readAsDataURL(file);
  });
}

$$('[data-nav]').forEach(link => {
  const target = link.getAttribute('href');
  if (target === pageName || (pageName === '' && target === 'index.html')) link.classList.add('active');
});

const navToggle = $('#navToggle');
if (navToggle) navToggle.addEventListener('click', () => $('.navbar')?.classList.toggle('open'));

function refreshNavbar() {
  const user = authUser();
  const navActions = $('.nav-actions');
  if (!navActions || !user) return;
  navActions.innerHTML = `<a class="btn btn-outline" href="dashboard.html">Dashboard</a><button class="btn btn-primary" id="logoutBtn" type="button">Logout</button>`;
  $('#logoutBtn')?.addEventListener('click', logout);
  if (user.role === 'admin') injectAdminLinks();
}

async function logout(event) {
  event?.preventDefault();
  try { await api('/logout', { method: 'POST', body: '{}' }); } catch (_) {}
  localStorage.removeItem('roomiesToken');
  localStorage.removeItem('roomiesUser');
  toast('Logged out successfully.');
  setTimeout(() => location.href = 'login.html', 550);
}

function injectAdminLinks() {
  $$('.sidebar-menu').forEach(menu => {
    if (!$('a[href="admin.html"]', menu)) {
      const logoutLink = [...menu.children].find(a => a.textContent.toLowerCase().includes('logout'));
      const admin = document.createElement('a');
      admin.href = 'admin.html';
      admin.innerHTML = '<span>◆</span>Admin Panel';
      if (pageName === 'admin.html') admin.className = 'active';
      menu.insertBefore(admin, logoutLink || null);
    }
  });
}

$$('.sidebar-menu a').forEach(link => {
  if (link.textContent.toLowerCase().includes('logout')) link.addEventListener('click', logout);
});
refreshNavbar();

const budgetRange = $('#budgetRange');
const budgetText = $('#budgetText');
if (budgetRange && budgetText) {
  const updateBudget = () => budgetText.textContent = `Up to ${money(budgetRange.value)}`;
  budgetRange.addEventListener('input', updateBudget);
  updateBudget();
}

function roomCard(room) {
  const amenities = (room.amenities || []).slice(0, 4).map(a => `<span>${escapeHtml(a)}</span>`).join('');
  const typeLabel = escapeHtml(room.room_type || 'private');
  return `<article class="room-card" data-room data-id="${room.id}" data-location="${escapeHtml(room.city)}" data-type="${typeLabel}" data-price="${room.price}">
    <a class="room-img" href="room-details.html?id=${room.id}"><img src="${escapeHtml(room.image_url)}" alt="${escapeHtml(room.title)}"></a>
    <button class="icon-btn heart" data-room-id="${room.id}" aria-label="Save listing">♡</button>
    <div class="room-body">
      <div class="room-top"><div><h3 class="room-title"><a href="room-details.html?id=${room.id}">${escapeHtml(room.title)}</a></h3><p class="muted small">📍 ${escapeHtml(room.location)}</p></div><div class="price">${money(room.price)}<span class="small muted"> /month</span></div></div>
      <div class="meta"><span>🛏 ${room.bedrooms || 1} Bed</span><span>🚿 ${room.bathrooms || 1} Bath</span><span>🪑 ${room.furnished ? 'Furnished' : 'Unfurnished'}</span><span>📶 ${room.wifi ? 'WiFi' : 'No WiFi'}</span></div>
      <div class="amenities">${amenities}</div>
    </div>
  </article>`;
}

function miniCard(room) {
  return `<article class="mini-card"><a href="room-details.html?id=${room.id}"><img src="${escapeHtml(room.image_url)}" alt="${escapeHtml(room.title)}"></a><div class="mini-card-body"><h3>${escapeHtml(room.title)}</h3><p class="muted small">${escapeHtml(room.location)}</p><b class="text-purple">${money(room.price)}/month</b></div></article>`;
}

function tableRows(rooms, withDelete = false) {
  if (!rooms.length) return `<tr><td colspan="6" class="muted">No listings yet. Post your first room and it will bloom here.</td></tr>`;
  return rooms.map(room => `<tr>
    <td><a href="room-details.html?id=${room.id}">${escapeHtml(room.title)}</a></td>
    <td>${money(room.price)}/month</td>
    <td>${Number(room.views || 0).toLocaleString('en-IN')}</td>
    <td>${Number(room.inquiries || 0).toLocaleString('en-IN')}</td>
    <td><span class="badge ${room.status === 'active' ? 'green' : 'pink'}">${escapeHtml(room.status || 'active')}</span></td>
    <td><a href="post-room.html?id=${room.id}" title="Edit">✎</a> ${withDelete ? `<button class="link-btn delete-room" data-room-id="${room.id}" title="Delete">🗑</button>` : ''}</td>
  </tr>`).join('');
}

async function loadRooms() {
  const list = $('.room-list');
  if (!list) return;
  list.innerHTML = `<div class="soft-card about-card muted">Loading rooms...</div>`;
  const params = new URLSearchParams(location.search);
  const selectedLocation = $('#filterLocation')?.value || params.get('location') || '';
  if ($('#filterLocation') && selectedLocation) {
    const clean = selectedLocation.toLowerCase();
    const option = [...$('#filterLocation').options].find(o => clean.includes(o.value));
    if (option) $('#filterLocation').value = option.value;
  }
  const query = new URLSearchParams();
  const locationValue = $('#filterLocation')?.value || selectedLocation;
  const checkedType = $('input[name="type"]:checked')?.value || '';
  const sortValue = $('.sorter select')?.value || 'Recommended';
  if (locationValue) query.set('location', locationValue);
  if (budgetRange?.value) query.set('budget', budgetRange.value);
  if (checkedType) query.set('type', checkedType);
  if (sortValue) query.set('sort', sortValue);
  try {
    const data = await api(`/rooms?${query.toString()}`);
    list.innerHTML = data.rooms.length ? data.rooms.map(roomCard).join('') : `<div class="empty-state"><h3>No rooms matched</h3><p class="muted">Try a wider budget or a different location.</p></div>`;
    $('#resultCount') && ($('#resultCount').textContent = `${data.count} rooms found`);
    $('.filter-box .small') && ($('.filter-box .small').textContent = `${data.count} rooms found`);
    attachHeartHandlers();
  } catch (err) {
    list.innerHTML = `<div class="empty-state"><h3>API not connected</h3><p class="muted">Run <b>python app.py</b> then refresh this page.</p></div>`;
    toast(err.message, 'error');
  }
}

const filterForm = $('#filterForm');
if (filterForm) {
  filterForm.addEventListener('submit', e => { e.preventDefault(); loadRooms(); });
  $('#clearFilters')?.addEventListener('click', () => {
    filterForm.reset();
    if (budgetRange) budgetRange.value = budgetRange.max || 12000;
    if (budgetRange && budgetText) budgetText.textContent = `Up to ${money(budgetRange.value)}`;
    loadRooms();
  });
  $('.sorter select')?.addEventListener('change', loadRooms);
  loadRooms();
}

function attachHeartHandlers() {
  $$('.heart').forEach(btn => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', async e => {
      e.preventDefault();
      const roomId = btn.dataset.roomId || btn.closest('[data-room]')?.dataset.id;
      if (!authToken()) return toast('Please login to save favorites.', 'error');
      try {
        const data = await api(`/favorites/${roomId}`, { method: 'POST', body: '{}' });
        btn.classList.toggle('active', data.saved);
        btn.textContent = data.saved ? '♥' : '♡';
        toast(data.saved ? 'Saved to favorites.' : 'Removed from favorites.');
      } catch (err) { toast(err.message, 'error'); }
    });
  });
}
attachHeartHandlers();

async function loadRoomDetails() {
  if (pageName !== 'room-details.html') return;
  const id = new URLSearchParams(location.search).get('id') || '1';
  const grid = $('.details-grid');
  if (!grid) return;
  try {
    const { room } = await api(`/rooms/${id}`);
    const amenities = (room.amenities || []).map(a => `<span>${escapeHtml(a)}</span>`).join('');
    const images = (room.images || [room.image_url]).slice(0, 4);
    const thumbHtml = images.slice(1).map(img => `<div class="thumb"><img src="${escapeHtml(img)}" alt="Room photo"></div>`).join('') || `<div class="thumb"><img src="${escapeHtml(room.image_url)}" alt="Room photo"></div>`;
    grid.innerHTML = `<div>
      <div class="gallery">
        <div class="gallery-main"><img src="${escapeHtml(images[0] || room.image_url)}" alt="${escapeHtml(room.title)}"></div>
        <div class="thumbs">${thumbHtml}</div>
      </div>
      <div class="details-card">
        <div class="details-title"><div><h1>${escapeHtml(room.title)}</h1><p class="muted">📍 ${escapeHtml(room.location)}, Nepal</p></div><div class="price">${money(room.price)} <span class="small muted">/month</span></div></div>
        <div class="meta"><span>🛏 ${room.bedrooms || 1} Bed</span><span>🚿 ${room.bathrooms || 1} Bath</span><span>🪑 ${room.furnished ? 'Furnished' : 'Unfurnished'}</span><span>📶 ${room.wifi ? 'WiFi' : 'No WiFi'}</span></div>
        <h3>About This Room</h3><p class="muted">${escapeHtml(room.description)}</p>
        <div class="amenities">${amenities}</div>
      </div>
      <div class="details-card"><h3>Location</h3><div class="map-card"><img src="assets/map.svg" alt="Map with location marker"></div><p class="small"><a class="text-purple" target="_blank" href="https://www.google.com/maps?q=${room.lat},${room.lng}">Open live map</a></p></div>
      <div class="details-card"><h3>Reviews</h3>${(room.reviews || []).length ? room.reviews.map(r => `<p class="muted"><b>${escapeHtml(r.user_name)}</b> ${'★'.repeat(r.rating)}<br>${escapeHtml(r.comment)}</p>`).join('') : '<p class="muted">No reviews yet.</p>'}</div>
    </div>
    <aside class="contact-card details-card">
      <div class="owner"><img src="${escapeHtml(room.owner?.avatar_url || 'assets/avatar.svg')}" alt="Owner"><div><b>${escapeHtml(room.owner_name || 'Room Owner')}</b><p class="muted small">Verified owner<br>4.8 ★ reviews</p></div></div>
      <div class="owner-actions"><button class="btn btn-primary" id="messageOwner" type="button">Message</button><a class="btn btn-outline" href="tel:${escapeHtml(room.owner_phone || '+9779800000000')}">Call</a></div>
      <button class="btn btn-ghost btn-full heart" data-room-id="${room.id}" type="button">♡ Save Listing</button>
      <h3>Book a Visit</h3>
      <form id="bookingForm" class="stack-sm"><input name="room_id" type="hidden" value="${room.id}"><div class="field"><label>Date</label><input name="visit_date" type="date" required></div><div class="field"><label>Time</label><input name="visit_time" type="time"></div><div class="field"><label>Note</label><textarea name="note" rows="3" placeholder="I want to visit this room..."></textarea></div><button class="btn btn-primary btn-full">Request Visit</button></form>
      <h3>Room Details</h3><div class="detail-list"><div class="detail-row"><span>Move In</span><b>${escapeHtml(room.move_in || 'Flexible')}</b></div><div class="detail-row"><span>Min Stay</span><b>${escapeHtml(room.min_stay || '1 month')}</b></div><div class="detail-row"><span>Room Type</span><b>${escapeHtml(room.room_type)}</b></div><div class="detail-row"><span>Deposit</span><b>${money(room.deposit || room.price)}</b></div><div class="detail-row"><span>Bills Included</span><b>${(room.amenities || []).slice(0,3).join(', ') || 'Ask owner'}</b></div><div class="detail-row"><span>Bedrooms</span><b>${room.bedrooms || 1}</b></div><div class="detail-row"><span>Bathrooms</span><b>${room.bathrooms || 1}</b></div></div>
    </aside>`;
    attachHeartHandlers();
    $('#bookingForm')?.addEventListener('submit', async e => {
      e.preventDefault();
      if (!authToken()) return toast('Login first to book a visit.', 'error');
      try { const data = await api('/bookings', { method: 'POST', body: JSON.stringify(formDataObject(e.currentTarget)) }); e.currentTarget.reset(); toast(data.message || 'Visit request sent.'); }
      catch (err) { toast(err.message, 'error'); }
    });
    $('#messageOwner')?.addEventListener('click', async () => {
      if (!authToken()) return toast('Login first to message owner.', 'error');
      try {
        await api('/messages', { method: 'POST', body: JSON.stringify({ receiver_id: room.owner_id, room_id: room.id, body: `Hi, I am interested in ${room.title}. Is it available?` }) });
        location.href = 'messages.html';
      } catch (err) { toast(err.message, 'error'); }
    });
  } catch (err) {
    grid.innerHTML = `<div class="empty-state"><h2>Room not found</h2><p class="muted">${escapeHtml(err.message)}</p><a class="btn btn-primary" href="search.html">Back to Search</a></div>`;
  }
}
loadRoomDetails();

const wizard = $('#postWizard');
if (wizard) {
  let step = 0;
  const panels = $$('.form-panel');
  const dots = $$('.wizard-step');
  const next = $('#nextStep');
  const prev = $('#prevStep');
  const finish = $('#finishPost');
  const form = wizard.closest('form');
  const showStep = () => {
    panels.forEach((panel, i) => panel.classList.toggle('active', i === step));
    dots.forEach((dot, i) => { dot.classList.toggle('active', i === step); dot.classList.toggle('done', i < step); });
    if (prev) prev.style.visibility = step === 0 ? 'hidden' : 'visible';
    next?.classList.toggle('hidden', step === panels.length - 1);
    finish?.classList.toggle('hidden', step !== panels.length - 1);
  };
  next?.addEventListener('click', () => { if (step < panels.length - 1) step++; showStep(); });
  prev?.addEventListener('click', () => { if (step > 0) step--; showStep(); });
  finish?.addEventListener('click', () => form?.requestSubmit());
  showStep();
}

async function prepareRoomPayload(form) {
  const fields = formDataObject(form);
  const amenities = $$('input[name="amenities"]:checked', form).map(x => x.value || x.closest('label')?.textContent.trim()).filter(Boolean);
  const file = form.querySelector('input[type="file"]')?.files?.[0];
  const imageData = await fileToDataURL(file);
  const payload = {
    title: fields.title,
    location: fields.location,
    city: (fields.location || '').split(',').pop()?.trim().toLowerCase() || '',
    price: Number(String(fields.price || '').replace(/[^0-9.]/g, '')),
    deposit: Number(String(fields.deposit || '').replace(/[^0-9.]/g, '')) || undefined,
    room_type: fields.room_type,
    description: fields.description,
    amenities,
    move_in: fields.move_in || fields.available_from,
    min_stay: fields.min_stay,
    image_url: fields.image_url,
    image_data: imageData,
    image_name: file?.name
  };
  return payload;
}

const postForm = $('#postRoomForm');
if (postForm) {
  postForm.addEventListener('submit', async e => {
    e.preventDefault();
    if (!authToken()) {
      toast('Login first, then post your room.', 'error');
      setTimeout(() => location.href = 'login.html', 900);
      return;
    }
    const restore = setButtonLoading($('#finishPost'), 'Posting...');
    const editId = new URLSearchParams(location.search).get('id');
    try {
      const payload = await prepareRoomPayload(postForm);
      const data = await api(editId ? `/rooms/${editId}` : '/rooms', { method: editId ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      toast(editId ? 'Room updated successfully.' : 'Room posted successfully. The database has swallowed it safely. 🟣');
      setTimeout(() => location.href = `room-details.html?id=${data.room_id || editId}`, 700);
    } catch (err) { toast(err.message, 'error'); }
    finally { restore(); }
  });
}

const loginForm = $('#loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const restore = setButtonLoading(loginForm.querySelector('button[type="submit"]'), 'Logging in...');
    try { const data = await api('/login', { method: 'POST', body: JSON.stringify(formDataObject(loginForm)) }); storeAuth(data); toast('Welcome back.'); setTimeout(() => location.href = 'dashboard.html', 500); }
    catch (err) { toast(err.message, 'error'); }
    finally { restore(); }
  });
}

const signupForm = $('#signupForm');
if (signupForm) {
  signupForm.addEventListener('submit', async e => {
    e.preventDefault();
    const fields = formDataObject(signupForm);
    if (fields.password !== fields.confirm_password) return toast('Passwords do not match.', 'error');
    const restore = setButtonLoading(signupForm.querySelector('button[type="submit"]'), 'Creating...');
    try { const data = await api('/signup', { method: 'POST', body: JSON.stringify(fields) }); storeAuth(data); toast('Account created successfully.'); setTimeout(() => location.href = 'dashboard.html', 500); }
    catch (err) { toast(err.message, 'error'); }
    finally { restore(); }
  });
}

const contactForm = $('#contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', async e => {
    e.preventDefault();
    const restore = setButtonLoading(contactForm.querySelector('button[type="submit"]'), 'Sending...');
    try { const data = await api('/contact', { method: 'POST', body: JSON.stringify(formDataObject(contactForm)) }); contactForm.reset(); toast(data.message || 'Message sent.'); }
    catch (err) { toast(err.message, 'error'); }
    finally { restore(); }
  });
}

$$('.newsletter').forEach(form => {
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const email = form.querySelector('input')?.value;
    try { await api('/newsletter', { method: 'POST', body: JSON.stringify({ email }) }); form.reset(); toast('Newsletter subscribed.'); }
    catch (err) { toast(err.message, 'error'); }
  });
});

async function loadDashboard() {
  if (pageName !== 'dashboard.html') return;
  const user = authUser();
  if (user) {
    $('.dash-top h1') && ($('.dash-top h1').textContent = `Welcome back, ${user.full_name.split(' ')[0]}! 👋`);
    $('.user-chip b') && ($('.user-chip b').textContent = user.full_name);
    $('.user-chip img') && ($('.user-chip img').src = user.avatar_url || 'assets/avatar.svg');
  }
  try {
    const data = await api('/dashboard/stats');
    const values = [data.stats.active_listings, data.stats.new_inquiries, data.stats.total_views, data.stats.bookings];
    $$('.stat b').forEach((b, i) => b.textContent = Number(values[i] || 0).toLocaleString('en-IN'));
    $('.table-card tbody') && ($('.table-card tbody').innerHTML = tableRows(data.rooms));
  } catch (_) { toast('Login to see personal dashboard data.', 'error'); }
}
loadDashboard();

async function loadMyListings() {
  if (pageName !== 'listings.html') return;
  const tbody = $('.table-card tbody');
  if (!tbody) return;
  if (!authToken()) { tbody.innerHTML = `<tr><td colspan="6">Please <a href="login.html">login</a> to manage listings.</td></tr>`; return; }
  try {
    const data = await api('/my-listings');
    tbody.innerHTML = tableRows(data.rooms, true);
    $$('.delete-room').forEach(btn => btn.addEventListener('click', async () => {
      if (!confirm('Delete this room?')) return;
      try { await api(`/rooms/${btn.dataset.roomId}`, { method: 'DELETE' }); toast('Listing deleted.'); loadMyListings(); }
      catch (err) { toast(err.message, 'error'); }
    }));
  } catch (err) { toast(err.message, 'error'); }
}
loadMyListings();

async function loadFavorites() {
  if (pageName !== 'favorites.html') return;
  const grid = $('.dash-grid');
  if (!grid) return;
  if (!authToken()) { grid.innerHTML = `<div class="empty-state"><h3>Please login first</h3><p class="muted">Your saved rooms will appear here.</p><a class="btn btn-primary" href="login.html">Login</a></div>`; return; }
  try { const data = await api('/favorites'); grid.innerHTML = data.rooms.length ? data.rooms.map(miniCard).join('') : `<div class="empty-state"><h3>No favorites yet</h3><p class="muted">Tap the heart on any room to save it.</p></div>`; }
  catch (err) { toast(err.message, 'error'); }
}
loadFavorites();

async function loadBookings() {
  if (pageName !== 'bookings.html') return;
  const tbody = $('#bookingsBody');
  if (!tbody) return;
  if (!authToken()) { tbody.innerHTML = `<tr><td colspan="7">Please <a href="login.html">login</a> to view bookings.</td></tr>`; return; }
  try {
    const data = await api('/bookings/my');
    tbody.innerHTML = data.bookings.length ? data.bookings.map(b => `<tr><td>${escapeHtml(b.room_title)}</td><td>${escapeHtml(b.renter_name || '')}</td><td>${escapeHtml(b.visit_date)} ${escapeHtml(b.visit_time || '')}</td><td>${escapeHtml(b.note || '')}</td><td><span class="badge ${b.status === 'accepted' ? 'green' : 'pink'}">${escapeHtml(b.status)}</span></td><td>${money(b.price)}</td><td><button class="link-btn booking-status" data-id="${b.id}" data-status="accepted">Accept</button> <button class="link-btn booking-status" data-id="${b.id}" data-status="declined">Decline</button></td></tr>`).join('') : `<tr><td colspan="7" class="muted">No bookings yet.</td></tr>`;
    $$('.booking-status').forEach(btn => btn.addEventListener('click', async () => { try { await api(`/bookings/${btn.dataset.id}/status`, { method: 'PATCH', body: JSON.stringify({ status: btn.dataset.status }) }); toast('Booking updated.'); loadBookings(); } catch (err) { toast(err.message, 'error'); } }));
  } catch (err) { toast(err.message, 'error'); }
}
loadBookings();

async function loadProfile() {
  if (pageName !== 'profile.html') return;
  if (!authToken()) return;
  try {
    const { user } = await api('/me');
    storeAuth({ user });
    $('#profileName') && ($('#profileName').value = user.full_name || '');
    $('#profilePhone') && ($('#profilePhone').value = user.phone || '');
    $('#profileEmail') && ($('#profileEmail').value = user.email || '');
    $('#profileBio') && ($('#profileBio').value = user.bio || '');
    $('#profileAvatar') && ($('#profileAvatar').src = user.avatar_url || 'assets/avatar.svg');
  } catch (_) {}
}
loadProfile();

const profileForm = $('#profileForm');
if (profileForm) {
  profileForm.addEventListener('submit', async e => {
    e.preventDefault();
    const file = $('#avatarInput')?.files?.[0];
    try {
      const fields = formDataObject(profileForm);
      fields.avatar_data = await fileToDataURL(file);
      fields.avatar_name = file?.name;
      const data = await api('/profile', { method: 'PATCH', body: JSON.stringify(fields) });
      storeAuth(data);
      toast('Profile updated.');
      loadProfile();
    } catch (err) { toast(err.message, 'error'); }
  });
}

const passwordForm = $('#passwordForm');
if (passwordForm) {
  passwordForm.addEventListener('submit', async e => {
    e.preventDefault();
    const fields = formDataObject(passwordForm);
    if (fields.new_password !== fields.confirm_password) return toast('New passwords do not match.', 'error');
    try { await api('/profile/password', { method: 'PATCH', body: JSON.stringify(fields) }); passwordForm.reset(); toast('Password updated.'); }
    catch (err) { toast(err.message, 'error'); }
  });
}

let activeThread = null;
async function loadMessages() {
  if (pageName !== 'messages.html') return;
  const contactList = $('.contacts-list');
  const chatBody = $('.chat-body');
  if (!contactList || !chatBody) return;
  if (!authToken()) { chatBody.innerHTML = `<div class="empty-state"><h3>Please login</h3><p class="muted">Messages need an account.</p></div>`; return; }
  try {
    const data = await api('/messages/threads');
    if (!data.threads.length) { contactList.innerHTML = '<p class="muted" style="padding:1rem">No message threads yet.</p>'; chatBody.innerHTML = '<p class="muted">Message an owner from a room details page.</p>'; return; }
    contactList.innerHTML = data.threads.map((t, i) => `<div class="contact-item ${i === 0 ? 'active' : ''}" data-user="${t.other_id}" data-room="${t.room_id || ''}" data-name="${escapeHtml(t.other_name)}"><img src="${escapeHtml(t.other_avatar || 'assets/avatar.svg')}" alt="Avatar"><div><b>${escapeHtml(t.other_name)}</b><p class="muted small">${escapeHtml(t.body)}</p></div></div>`).join('');
    const open = async item => {
      $$('.contact-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      activeThread = { user: item.dataset.user, room: item.dataset.room };
      $('#chatName') && ($('#chatName').textContent = item.dataset.name);
      const q = new URLSearchParams({ with_user: activeThread.user });
      if (activeThread.room) q.set('room_id', activeThread.room);
      const messages = await api(`/messages?${q.toString()}`);
      chatBody.innerHTML = messages.messages.map(m => `<div class="bubble ${m.mine ? 'me' : ''}">${escapeHtml(m.body)}<br><small>${new Date(m.created_at).toLocaleString()}</small></div>`).join('');
      chatBody.scrollTop = chatBody.scrollHeight;
    };
    $$('.contact-item').forEach(item => item.addEventListener('click', () => open(item)));
    open($('.contact-item'));
  } catch (err) { toast(err.message, 'error'); }
}
loadMessages();

const chatInput = $('.chat-input');
if (chatInput) {
  chatInput.addEventListener('submit', async e => {
    e.preventDefault();
    const input = chatInput.querySelector('input');
    if (!activeThread || !input.value.trim()) return;
    try {
      await api('/messages', { method: 'POST', body: JSON.stringify({ receiver_id: activeThread.user, room_id: activeThread.room, body: input.value.trim() }) });
      input.value = '';
      loadMessages();
    } catch (err) { toast(err.message, 'error'); }
  });
}

async function loadAdmin() {
  if (pageName !== 'admin.html') return;
  const root = $('#adminRoot');
  if (!root) return;
  try {
    const data = await api('/admin/overview');
    root.innerHTML = `<div class="stats">${Object.entries(data.stats).map(([k,v]) => `<div class="stat"><span class="stat-icon">◆</span><div><p class="muted small">${escapeHtml(k.replace('_',' '))}</p><b>${Number(v).toLocaleString('en-IN')}</b></div></div>`).join('')}</div>
    <div class="table-card"><div class="dash-top"><h2>Latest Users</h2><button class="btn btn-primary" id="backupDb">Create Backup</button></div><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Phone</th></tr></thead><tbody>${data.users.map(u => `<tr><td>${escapeHtml(u.full_name)}</td><td>${escapeHtml(u.email)}</td><td>${escapeHtml(u.role)}</td><td>${escapeHtml(u.phone || '')}</td></tr>`).join('')}</tbody></table></div>
    <div class="table-card"><h2>Latest Rooms</h2><table><thead><tr><th>Room</th><th>Owner</th><th>City</th><th>Price</th><th>Status</th></tr></thead><tbody>${data.rooms.map(r => `<tr><td>${escapeHtml(r.title)}</td><td>${escapeHtml(r.owner_name)}</td><td>${escapeHtml(r.city)}</td><td>${money(r.price)}</td><td>${escapeHtml(r.status)}</td></tr>`).join('')}</tbody></table></div>
    <div class="table-card"><h2>Contact Messages</h2><table><thead><tr><th>Name</th><th>Email</th><th>Message</th></tr></thead><tbody>${data.contacts.map(c => `<tr><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.email)}</td><td>${escapeHtml(c.message)}</td></tr>`).join('') || '<tr><td colspan="3">No contact messages.</td></tr>'}</tbody></table></div>`;
    $('#backupDb')?.addEventListener('click', async () => { try { const res = await api('/admin/backup', { method: 'POST', body: '{}' }); toast(`Backup created: ${res.backup}`); } catch (err) { toast(err.message, 'error'); } });
  } catch (err) { root.innerHTML = `<div class="empty-state"><h3>Admin login required</h3><p class="muted">Use admin@roomies.local / admin123</p><p class="muted">${escapeHtml(err.message)}</p></div>`; }
}
loadAdmin();

// ---------------- Roomies Pro no-payment upgrade ----------------
function compareIds() {
  return JSON.parse(localStorage.getItem('roomiesCompareIds') || '[]').map(String).slice(0, 4);
}
function setCompareIds(ids) {
  localStorage.setItem('roomiesCompareIds', JSON.stringify([...new Set(ids.map(String))].slice(0, 4)));
}
function addToCompare(id) {
  const ids = compareIds();
  if (!ids.includes(String(id))) ids.push(String(id));
  setCompareIds(ids);
  toast(`Added to compare (${compareIds().length}/4).`);
}
function formQuery(form) {
  const data = formDataObject(form);
  Object.keys(data).forEach(k => { if (data[k] === '') delete data[k]; });
  return data;
}
function queryStringFromObject(obj) {
  const qs = new URLSearchParams();
  Object.entries(obj).forEach(([k, v]) => {
    if (v !== undefined && v !== null && String(v).trim() !== '') qs.set(k, v);
  });
  return qs.toString();
}
function badge(text, cls = '') { return `<span class="badge ${cls}">${escapeHtml(text)}</span>`; }
function roomProBadges(room) {
  const items = [];
  if (room.owner_verified) items.push('<span class="trust-chip">✓ Verified owner</span>');
  if (room.distance_km) items.push(`<span class="distance-chip">${room.distance_km} km away</span>`);
  if (room.avg_rating) items.push(`<span class="trust-chip">★ ${room.avg_rating}</span>`);
  if (room.safety_score) items.push(`<span class="trust-chip">Safety ${room.safety_score}</span>`);
  return items.length ? `<div class="pro-badge-row">${items.join('')}</div>` : '';
}

async function readFilesAsDataList(files) {
  const list = [];
  for (const file of [...(files || [])].slice(0, 10)) {
    const data = await fileToDataURL(file);
    if (data) list.push({ name: file.name, data });
  }
  return list;
}

async function prepareRoomPayload(form) {
  const fields = formDataObject(form);
  const amenities = $$('input[name="amenities"]:checked', form).map(x => x.value || x.closest('label')?.textContent.trim()).filter(Boolean);
  const fileInput = form.querySelector('input[type="file"]');
  const imageDataList = await readFilesAsDataList(fileInput?.files);
  return {
    title: fields.title,
    location: fields.location,
    city: fields.city || (fields.location || '').split(',').pop()?.trim().toLowerCase() || '',
    price: Number(String(fields.price || '').replace(/[^0-9.]/g, '')),
    deposit: Number(String(fields.deposit || '').replace(/[^0-9.]/g, '')) || undefined,
    room_type: fields.room_type,
    bedrooms: Number(fields.bedrooms || 1),
    bathrooms: Number(fields.bathrooms || 1),
    furnished: fields.furnished === 'on' || fields.furnished === 'true' || !('furnished' in fields),
    wifi: fields.wifi === 'on' || fields.wifi === 'true' || !('wifi' in fields),
    description: fields.description,
    amenities,
    move_in: fields.move_in || fields.available_from,
    min_stay: fields.min_stay,
    available_until: fields.available_until,
    floor: fields.floor,
    preferred_tenant: fields.preferred_tenant,
    rules: fields.rules,
    lat: fields.lat || 27.7172,
    lng: fields.lng || 85.3240,
    video_url: fields.video_url,
    virtual_tour_url: fields.virtual_tour_url,
    image_url: fields.image_url,
    image_data_list: imageDataList,
    replace_images: imageDataList.length > 0,
    verified_location: fields.verified_location === 'on'
  };
}

function enhancePostRoomForm() {
  if (pageName !== 'post-room.html') return;
  const form = $('#postRoomForm');
  if (!form || form.dataset.proEnhanced) return;
  form.dataset.proEnhanced = '1';
  const panels = $$('.form-panel', form);
  if (panels[0]) panels[0].querySelector('.form-grid')?.insertAdjacentHTML('beforeend', `
    <div class="field"><label>City</label><input name="city" placeholder="kathmandu"></div>
    <div class="field"><label>Preferred tenant</label><select name="preferred_tenant"><option value="">Any</option><option>Student</option><option>Working professional</option><option>Family</option><option>Female only</option><option>Male only</option></select></div>`);
  if (panels[1]) panels[1].querySelector('.form-grid')?.insertAdjacentHTML('beforeend', `
    <div class="field"><label>Bedrooms</label><input name="bedrooms" type="number" min="1" value="1"></div>
    <div class="field"><label>Bathrooms</label><input name="bathrooms" type="number" min="1" value="1"></div>
    <div class="field"><label>Floor</label><input name="floor" placeholder="2nd floor"></div>
    <div class="field"><label>Video URL</label><input name="video_url" placeholder="YouTube / tour video link"></div>`);
  if (panels[2]) panels[2].insertAdjacentHTML('beforeend', `
    <div class="check-list grid grid-2" style="margin-top:14px"><label><input type="checkbox" name="furnished" checked> Furnished</label><label><input type="checkbox" name="wifi" checked> WiFi available</label><label><input type="checkbox" name="amenities" value="Attached Bathroom"> Attached Bathroom</label><label><input type="checkbox" name="amenities" value="CCTV"> CCTV</label></div>`);
  if (panels[3]) panels[3].insertAdjacentHTML('beforeend', `<div id="imagePreviewGrid" class="image-preview-grid"></div><div class="field" style="margin-top:12px"><label>Virtual tour URL</label><input name="virtual_tour_url" placeholder="360 tour or walkthrough URL"></div>`);
  if (panels[4]) panels[4].insertAdjacentHTML('beforeend', `
    <div class="form-grid" style="margin-top:14px"><div class="field"><label>Available until</label><input name="available_until" type="date"></div><div class="field"><label>Latitude</label><input name="lat" value="27.7172"></div><div class="field"><label>Longitude</label><input name="lng" value="85.3240"></div><label class="check-inline"><input type="checkbox" name="verified_location"> Location pin checked</label></div>
    <div class="field" style="margin-top:14px"><label>House rules</label><textarea name="rules" rows="4" placeholder="Quiet hours, guests, cooking, pets, smoking, deposit conditions..."></textarea></div>`);
  form.querySelector('input[type="file"]')?.addEventListener('change', e => {
    const grid = $('#imagePreviewGrid');
    if (!grid) return;
    grid.innerHTML = '';
    [...e.target.files].slice(0, 8).forEach(file => {
      const img = document.createElement('img');
      img.alt = file.name;
      img.src = URL.createObjectURL(file);
      grid.appendChild(img);
    });
  });
}
enhancePostRoomForm();

function enhanceSearchFilters() {
  if (pageName !== 'search.html') return;
  const form = $('#filterForm');
  if (!form || form.dataset.proEnhanced) return;
  form.dataset.proEnhanced = '1';
  form.insertAdjacentHTML('afterbegin', `<div class="field"><label>Keyword</label><input id="filterKeyword" placeholder="college, quiet, furnished"></div><div class="field"><label>Min price</label><input id="filterMinPrice" type="number" placeholder="4000"></div><div class="field"><label>Bedrooms</label><input id="filterBedrooms" type="number" min="1" placeholder="1+"></div><label class="check-inline"><input id="filterVerified" type="checkbox"> Verified owners only</label>`);
  form.insertAdjacentHTML('beforeend', `<button class="btn btn-outline" type="button" id="saveCurrentSearch">Save this search</button>`);
  const sort = $('.sorter select');
  if (sort) sort.innerHTML = '<option>Recommended</option><option>Low price</option><option>High price</option><option>Newest</option><option>Rating</option><option>Popular</option>';
  form.addEventListener('submit', e => { e.preventDefault(); e.stopImmediatePropagation(); loadRoomsPro(); }, true);
  $('#clearFilters')?.addEventListener('click', () => setTimeout(loadRoomsPro, 30), true);
  sort?.addEventListener('change', () => loadRoomsPro(), true);
  $('#saveCurrentSearch')?.addEventListener('click', async () => {
    if (!authToken()) return toast('Login first to save a search.', 'error');
    const query = currentSearchQuery();
    try { await api('/saved-searches', { method:'POST', body: JSON.stringify({ name: `${query.location || 'All areas'} under ${query.max_price || 'any budget'}`, query, is_alert: true }) }); toast('Search saved.'); }
    catch (err) { toast(err.message, 'error'); }
  });
  setTimeout(loadRoomsPro, 100);
}
function currentSearchQuery() {
  const type = $('input[name="type"]:checked')?.value || '';
  const amenities = $$('.filter-box .check-list input:checked').filter(x => x.name !== 'type').map(x => x.value || x.closest('label')?.textContent.trim()).filter(Boolean).join(',');
  const query = {
    q: $('#filterKeyword')?.value || '',
    location: $('#filterLocation')?.value || '',
    min_price: $('#filterMinPrice')?.value || '',
    max_price: budgetRange?.value || '',
    type,
    bedrooms: $('#filterBedrooms')?.value || '',
    amenities,
    verified: $('#filterVerified')?.checked ? '1' : '',
    sort: $('.sorter select')?.value || 'Recommended'
  };
  Object.keys(query).forEach(k => { if (!query[k]) delete query[k]; });
  return query;
}
async function loadRoomsPro() {
  if (pageName !== 'search.html') return;
  const list = $('.room-list');
  if (!list) return;
  list.innerHTML = `<div class="soft-card about-card muted">Loading upgraded search...</div>`;
  try {
    const data = await api(`/rooms?${queryStringFromObject(currentSearchQuery())}`);
    list.innerHTML = data.rooms.length ? data.rooms.map(room => roomCard(room).replace('<div class="room-body">', `<button class="compare-add" data-compare="${room.id}">＋ Compare</button><div class="room-body">`).replace('</div>\n  </article>', `${roomProBadges(room)}</div>\n  </article>`)).join('') : `<div class="empty-state"><h3>No rooms matched</h3><p class="muted">Try another price, city, or amenity mix.</p></div>`;
    $('#resultCount') && ($('#resultCount').textContent = `${data.count} rooms found`);
    attachHeartHandlers();
    installCompareButtons();
  } catch (err) {
    list.innerHTML = `<div class="empty-state"><h3>API not connected</h3><p class="muted">Run <b>python app.py</b> then refresh.</p></div>`;
  }
}
enhanceSearchFilters();

function installCompareButtons() {
  $$('[data-compare]').forEach(btn => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', e => { e.preventDefault(); addToCompare(btn.dataset.compare); });
  });
}
setInterval(installCompareButtons, 1500);

async function enhanceRoomDetailsPro() {
  if (pageName !== 'room-details.html') return;
  const id = new URLSearchParams(location.search).get('id') || '1';
  try {
    const { room } = await api(`/rooms/${id}`);
    const aside = $('.contact-card');
    if (!aside || aside.dataset.proEnhanced) return;
    aside.dataset.proEnhanced = '1';
    const statusBanner = room.status === 'active' ? '<div class="approved-banner">✓ Active listing with trust checks</div>' : `<div class="pending-banner">Status: ${escapeHtml(room.status || 'pending')}</div>`;
    aside.insertAdjacentHTML('afterbegin', `${statusBanner}${roomProBadges(room)}<button class="btn btn-outline btn-full" id="addCompareDetail" type="button">＋ Add Compare</button><a class="btn btn-primary btn-full" style="margin-top:.6rem" href="applications.html?room_id=${room.id}">Apply as Tenant</a>`);
    aside.insertAdjacentHTML('beforeend', `<div class="application-box"><h3>Application shortcut</h3><p class="muted small">Submit occupation, budget, and move-in details. No payment involved.</p><a class="btn btn-primary btn-full" href="applications.html?room_id=${room.id}">Start Application</a></div><div class="report-box"><h3>Report this listing</h3><p class="muted small">Found fake details, wrong price, or unsafe behavior?</p><button class="btn btn-outline btn-full" id="reportRoomBtn" type="button">Report Listing</button></div>`);
    $('#addCompareDetail')?.addEventListener('click', () => addToCompare(room.id));
    $('#reportRoomBtn')?.addEventListener('click', async () => {
      const reason = prompt('Reason for report? Example: fake photos, wrong price, unsafe owner');
      if (!reason) return;
      const details = prompt('Add details for admin review') || '';
      try { await api('/reports', { method: 'POST', body: JSON.stringify({ room_id: room.id, reason, details }) }); toast('Report sent to admin.'); }
      catch (err) { toast(err.message, 'error'); }
    });
  } catch (_) {}
}
setTimeout(enhanceRoomDetailsPro, 800);

async function loadMapPage() {
  if (pageName !== 'map.html') return;
  const form = $('#mapSearchForm');
  const root = $('#mapResults');
  const run = async () => {
    root.innerHTML = '<div class="soft-card about-card muted">Searching map...</div>';
    const query = formQuery(form);
    try {
      const data = await api(`/rooms?${queryStringFromObject(query)}`);
      root.innerHTML = data.rooms.length ? data.rooms.map(room => `<article class="map-room"><img src="${escapeHtml(room.image_url)}" alt="${escapeHtml(room.title)}"><div><h3><a href="room-details.html?id=${room.id}">${escapeHtml(room.title)}</a></h3><p class="muted small">📍 ${escapeHtml(room.location)}</p><b>${money(room.price)}/month</b>${roomProBadges(room)}<button class="chip-btn" data-compare="${room.id}">＋ Compare</button></div></article>`).join('') : '<div class="empty-state"><h3>No rooms in this radius</h3></div>';
      installCompareButtons();
      const map = $('#liveMap');
      if (map) map.innerHTML = `<iframe title="OpenStreetMap" style="position:absolute;inset:0;width:100%;height:100%;border:0" src="https://www.openstreetmap.org/export/embed.html?bbox=${Number(query.lng||85.3240)-0.05}%2C${Number(query.lat||27.7172)-0.05}%2C${Number(query.lng||85.3240)+0.05}%2C${Number(query.lat||27.7172)+0.05}&layer=mapnik&marker=${query.lat||27.7172}%2C${query.lng||85.3240}"></iframe>`;
    } catch (err) { root.innerHTML = `<div class="empty-state"><h3>${escapeHtml(err.message)}</h3></div>`; }
  };
  form?.addEventListener('submit', e => { e.preventDefault(); run(); });
  run();
}
loadMapPage();

async function loadSavedSearchesPage() {
  if (pageName !== 'saved-searches.html') return;
  const root = $('#savedSearchesList');
  if (!authToken()) { root.innerHTML = '<div class="empty-state"><h3>Login required</h3><a class="btn btn-primary" href="login.html">Login</a></div>'; return; }
  async function refresh() {
    try {
      const data = await api('/saved-searches');
      root.innerHTML = data.saved_searches.length ? data.saved_searches.map(s => `<article class="saved-search-card"><div class="dash-top"><div><h3>${escapeHtml(s.name)}</h3><p class="muted small">${escapeHtml(JSON.stringify(s.query))}</p></div><button class="chip-btn delete-saved" data-id="${s.id}">Delete</button></div><a class="btn btn-outline btn-small" href="search.html?${queryStringFromObject(s.query)}">Open Search</a></article>`).join('') : '<div class="empty-state"><h3>No saved searches yet</h3></div>';
      $$('.delete-saved').forEach(btn => btn.addEventListener('click', async () => { await api(`/saved-searches/${btn.dataset.id}`, { method:'DELETE' }); toast('Saved search deleted.'); refresh(); }));
    } catch (err) { root.innerHTML = `<div class="empty-state"><h3>${escapeHtml(err.message)}</h3></div>`; }
  }
  $('#savedSearchForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const fields = formDataObject(e.currentTarget);
    const query = { location: fields.location, max_price: fields.max_price, amenities: fields.amenities };
    Object.keys(query).forEach(k => { if (!query[k]) delete query[k]; });
    try { await api('/saved-searches', { method:'POST', body: JSON.stringify({ name: fields.name, query, is_alert: fields.is_alert === 'on' }) }); e.currentTarget.reset(); toast('Search saved.'); refresh(); }
    catch (err) { toast(err.message, 'error'); }
  });
  refresh();
}
loadSavedSearchesPage();

async function loadComparePage() {
  if (pageName !== 'compare.html') return;
  const input = $('#compareIds');
  const params = new URLSearchParams(location.search);
  input.value = params.get('ids') || compareIds().join(',');
  async function run() {
    const ids = input.value || compareIds().join(',');
    $('#compareRoot').innerHTML = '<div class="soft-card about-card muted">Loading comparison...</div>';
    try {
      const data = await api(`/rooms/compare?ids=${encodeURIComponent(ids)}`);
      $('#compareRoot').innerHTML = data.rooms.map(room => `<article class="compare-card"><img src="${escapeHtml(room.image_url)}" alt="${escapeHtml(room.title)}"><div class="compare-card-body"><h3><a href="room-details.html?id=${room.id}">${escapeHtml(room.title)}</a></h3><p class="muted small">${escapeHtml(room.location)}</p>${roomProBadges(room)}<div class="compare-row"><span>Price</span><b>${money(room.price)}</b></div><div class="compare-row"><span>Deposit</span><b>${money(room.deposit)}</b></div><div class="compare-row"><span>Type</span><b>${escapeHtml(room.room_type)}</b></div><div class="compare-row"><span>Bed/Bath</span><b>${room.bedrooms}/${room.bathrooms}</b></div><div class="compare-row"><span>Move-in</span><b>${escapeHtml(room.move_in || 'Flexible')}</b></div><div class="compare-row"><span>Owner trust</span><b>${room.owner_trust_score || 60}</b></div><div class="compare-row"><span>Reviews</span><b>${room.avg_rating || 0} (${room.review_count || 0})</b></div></div></article>`).join('') || '<div class="empty-state"><h3>Add room ids to compare</h3></div>';
    } catch (err) { $('#compareRoot').innerHTML = `<div class="empty-state"><h3>${escapeHtml(err.message)}</h3></div>`; }
  }
  $('#compareForm')?.addEventListener('submit', e => { e.preventDefault(); setCompareIds(input.value.split(',').filter(Boolean)); run(); });
  $('#clearCompare')?.addEventListener('click', () => { setCompareIds([]); input.value = ''; $('#compareRoot').innerHTML = ''; toast('Compare list cleared.'); });
  if (input.value) run();
}
loadComparePage();

async function loadApplicationsPage() {
  if (pageName !== 'applications.html') return;
  const roomId = new URLSearchParams(location.search).get('room_id');
  if (roomId) $('#applicationRoomId') && ($('#applicationRoomId').value = roomId);
  const body = $('#applicationsBody');
  if (!authToken()) { body.innerHTML = '<tr><td colspan="5">Please login first.</td></tr>'; return; }
  async function refresh() {
    try {
      const data = await api('/applications/my');
      body.innerHTML = data.applications.length ? data.applications.map(a => `<tr><td><a href="room-details.html?id=${a.room_id}">${escapeHtml(a.room_title)}</a></td><td>${escapeHtml(a.applicant_name)}</td><td>${badge(a.status, a.status === 'accepted' ? 'green' : 'pink')}</td><td>${money(a.budget)}</td><td><button class="chip-btn app-status" data-id="${a.id}" data-status="shortlisted">Shortlist</button><button class="chip-btn app-status" data-id="${a.id}" data-status="accepted">Accept</button><button class="chip-btn app-status" data-id="${a.id}" data-status="declined">Decline</button></td></tr>`).join('') : '<tr><td colspan="5" class="muted">No applications yet.</td></tr>';
      $$('.app-status').forEach(btn => btn.addEventListener('click', async () => { try { await api(`/applications/${btn.dataset.id}/status`, { method:'PATCH', body: JSON.stringify({ status: btn.dataset.status }) }); toast('Application updated.'); refresh(); } catch (err) { toast(err.message, 'error'); } }));
    } catch (err) { body.innerHTML = `<tr><td colspan="5">${escapeHtml(err.message)}</td></tr>`; }
  }
  $('#applicationForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try { await api('/applications', { method:'POST', body: JSON.stringify(formDataObject(e.currentTarget)) }); toast('Application submitted.'); refresh(); }
    catch (err) { toast(err.message, 'error'); }
  });
  refresh();
}
loadApplicationsPage();

async function loadVerificationPage() {
  if (pageName !== 'verification.html') return;
  async function refreshStatus() {
    if (!authToken()) return;
    try {
      const { user } = await api('/me');
      $('#verificationStatus').innerHTML = `<h2>Status</h2><div class="analytics-row"><div class="stat"><span class="stat-icon">@</span><div><p class="muted small">Email</p><b>${user.email_verified ? 'Verified' : 'Pending'}</b></div></div><div class="stat"><span class="stat-icon">☎</span><div><p class="muted small">Phone</p><b>${user.phone_verified ? 'Verified' : 'Pending'}</b></div></div><div class="stat"><span class="stat-icon">✓</span><div><p class="muted small">Trust Score</p><b>${user.trust_score || 60}</b></div></div></div>`;
    } catch (_) {}
  }
  $('#verificationRequestForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try { const data = await api('/verification/request', { method:'POST', body: JSON.stringify(formDataObject(e.currentTarget)) }); $('#devCodeNote').textContent = `Local testing code: ${data.dev_code}`; toast(data.message); }
    catch (err) { toast(err.message, 'error'); }
  });
  $('#verificationConfirmForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try { const data = await api('/verification/confirm', { method:'POST', body: JSON.stringify(formDataObject(e.currentTarget)) }); toast(data.message); refreshStatus(); }
    catch (err) { toast(err.message, 'error'); }
  });
  refreshStatus();
}
loadVerificationPage();

async function loadModerationPage() {
  if (pageName !== 'moderation.html') return;
  const root = $('#moderationRoot');
  async function refresh() {
    try {
      const data = await api('/admin/moderation');
      root.innerHTML = `<div class="moderation-grid">
        <section class="table-card"><h2>Pending Rooms</h2><table><thead><tr><th>Room</th><th>Owner</th><th>Price</th><th>Status</th><th>Action</th></tr></thead><tbody>${data.pending_rooms.map(r => `<tr><td>${escapeHtml(r.title)}</td><td>${escapeHtml(r.owner_name)}<br><span class="muted small">${escapeHtml(r.owner_email)}</span></td><td>${money(r.price)}</td><td>${escapeHtml(r.status)}</td><td class="moderation-actions"><button class="chip-btn room-status" data-id="${r.id}" data-status="active">Approve</button><button class="chip-btn room-status" data-id="${r.id}" data-status="rejected">Reject</button></td></tr>`).join('') || '<tr><td colspan="5">No pending rooms.</td></tr>'}</tbody></table></section>
        <section class="table-card"><h2>Reports</h2><table><thead><tr><th>Reason</th><th>Room</th><th>Details</th><th>Status</th><th>Action</th></tr></thead><tbody>${data.reports.map(r => `<tr><td>${escapeHtml(r.reason)}</td><td>${escapeHtml(r.room_title || '')}</td><td>${escapeHtml(r.details || '')}</td><td><span class="badge status-${escapeHtml(r.status)}">${escapeHtml(r.status)}</span></td><td><button class="chip-btn report-status" data-id="${r.id}" data-status="reviewing">Review</button><button class="chip-btn report-status" data-id="${r.id}" data-status="resolved">Resolve</button><button class="chip-btn report-status" data-id="${r.id}" data-status="dismissed">Dismiss</button></td></tr>`).join('') || '<tr><td colspan="5">No reports.</td></tr>'}</tbody></table></section>
        <section class="table-card"><h2>User Verification</h2><table><thead><tr><th>User</th><th>Role</th><th>Email</th><th>Trust</th><th>Action</th></tr></thead><tbody>${data.users.map(u => `<tr><td>${escapeHtml(u.full_name)}</td><td>${escapeHtml(u.role)}</td><td>${u.email_verified ? '✓' : '·'} ${u.phone_verified ? '☎' : ''}<br><span class="muted small">${escapeHtml(u.email)}</span></td><td>${u.trust_score}</td><td><button class="chip-btn verify-user" data-id="${u.id}">Verify Owner</button></td></tr>`).join('')}</tbody></table></section>
      </div>`;
      $$('.room-status').forEach(btn => btn.addEventListener('click', async () => { await api(`/admin/rooms/${btn.dataset.id}/status`, { method:'PATCH', body: JSON.stringify({ status: btn.dataset.status }) }); toast('Room status updated.'); refresh(); }));
      $$('.report-status').forEach(btn => btn.addEventListener('click', async () => { await api(`/admin/reports/${btn.dataset.id}/status`, { method:'PATCH', body: JSON.stringify({ status: btn.dataset.status }) }); toast('Report updated.'); refresh(); }));
      $$('.verify-user').forEach(btn => btn.addEventListener('click', async () => { await api(`/admin/users/${btn.dataset.id}/verify`, { method:'PATCH', body: JSON.stringify({ verified_owner: true, trust_score: 95 }) }); toast('Owner verified.'); refresh(); }));
    } catch (err) { root.innerHTML = `<div class="empty-state"><h3>Admin login required</h3><p class="muted">Use admin@roomies.local / admin123</p><p class="muted">${escapeHtml(err.message)}</p></div>`; }
  }
  refresh();
}
loadModerationPage();

if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
