const $ = s => document.querySelector(s);
const chat = $('#chat'), panel = $('#panel');
const els = {
  empty: $('#empty'), steps: $('#steps'), ticket: $('#ticket'),
  abstain: $('#abstain'), abtext: $('#abtext'), failed: $('#failed'),
};
const LANG = { en:'English', fr:'Français', rw:'Kinyarwanda', sw:'Kiswahili' };
let busy = false;

/* ── health ── */
fetch('/api/health').then(r => r.json()).then(d => {
  const s = $('#status');
  s.className = 'status ' + (d.ok ? 'ok' : 'bad');
  s.querySelector('span').textContent = d.ok ? `${d.backend} · ready` : 'backend unavailable';
}).catch(() => {
  const s = $('#status'); s.className = 'status bad';
  s.querySelector('span').textContent = 'offline';
});

/* ── chat helpers ── */
function bubble(text, dir, tag) {
  const b = document.createElement('div');
  b.className = `bub ${dir}`;
  b.textContent = text;
  if (tag) {
    const t = document.createElement('span');
    t.className = 'tag'; t.textContent = tag;
    b.appendChild(t);
  }
  chat.appendChild(b);
  chat.scrollTop = chat.scrollHeight;
  return b;
}
function typingOn() {
  const t = document.createElement('div');
  t.className = 'typing'; t.id = 'typing';
  t.innerHTML = '<i></i><i></i><i></i>';
  chat.appendChild(t); chat.scrollTop = chat.scrollHeight;
  $('#presence').textContent = 'typing…';
}
function typingOff() {
  document.getElementById('typing')?.remove();
  $('#presence').textContent = 'online';
}

/* ── step animation ──
   The backend is one blocking call, so steps are paced to the observed
   latency of each stage rather than driven by real progress events.
   They show the user what the system is doing, and are cosmetic only. */
let stepTimers = [];
function runSteps() {
  stepTimers.forEach(clearTimeout); stepTimers = [];
  const steps = [...document.querySelectorAll('.step')];
  steps.forEach(s => s.className = 'step');
  const at = [0, 9000, 13000, 22000, 40000];
  steps.forEach((s, i) => {
    stepTimers.push(setTimeout(() => {
      steps.slice(0, i).forEach(p => p.className = 'step done');
      s.className = 'step active';
    }, at[i]));
  });
}
function stopSteps(done) {
  stepTimers.forEach(clearTimeout); stepTimers = [];
  if (done) document.querySelectorAll('.step').forEach(s => s.className = 'step done');
}

function show(which) {
  for (const k of ['empty','steps','ticket','abstain','failed']) els[k].hidden = (k !== which);
}

/* ── ticket rendering ── */
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function renderTicket(d) {
  const conf = Math.round((d.confidence || 0) * 100);
  const causes = (d.causes || []).map(c => `
    <div class="cause ${esc(c.likelihood || 'low')}">
      <b>${esc(c.cause)}</b><span class="lk">${esc(c.likelihood || '')}</span>
      ${c.check ? `<p>${esc(c.check)}</p>` : ''}
    </div>`).join('');

  els.ticket.innerHTML = `
    <div class="tkhead">
      <span class="badge ${esc(d.urgency)}">${esc(d.urgency)}</span>
      <span class="tid">#${Math.random().toString(36).slice(2, 8).toUpperCase()}</span>
    </div>
    <h3 class="tkname">${esc(d.subcategory)}</h3>
    <div class="tkcat">category: ${esc(d.category)} · reported in ${esc(LANG[d.language] || d.language)}</div>

    <div class="conf">
      <div class="conflabel"><span>classification confidence</span><span>${conf}%</span></div>
      <div class="confbar"><div class="conffill" style="width:0%"></div></div>
    </div>

    ${d.symptoms?.length ? `<div class="sec"><h4>Symptoms extracted</h4>
      <div class="sym">${d.symptoms.map(s => `<span>${esc(s)}</span>`).join('')}</div></div>` : ''}

    ${d.immediate_action ? `<div class="sec"><h4>Immediate action</h4>
      <div class="act">${esc(d.immediate_action)}</div></div>` : ''}

    ${causes ? `<div class="sec"><h4>Likely causes</h4>${causes}</div>` : ''}

    ${d.parts?.length ? `<div class="sec"><h4>Parts likely needed</h4>
      <div class="parts">${d.parts.map(p => `<span>${esc(p)}</span>`).join('')}</div></div>` : ''}

    ${d.environmental ? `<div class="sec"><h4>Environmental note</h4>
      <div class="env">${esc(d.environmental)}</div></div>` : ''}

    <details><summary>Raw ticket (JSON)</summary><pre>${esc(JSON.stringify(d, null, 2))}</pre></details>`;

  show('ticket');
  requestAnimationFrame(() => {
    const f = els.ticket.querySelector('.conffill');
    if (f) f.style.width = conf + '%';
  });
}

/* ── submit ── */
async function send(text) {
  if (busy || !text.trim()) return;
  busy = true;
  $('#send').disabled = true;
  $('#msg').value = '';

  bubble(text, 'out');
  typingOn();
  show('steps');
  runSteps();

  try {
    const res = await fetch('/api/triage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const d = await res.json();
    typingOff();
    stopSteps(true);

    if (!res.ok || d.error) {
      els.failed.textContent = 'Pipeline error: ' + (d.error || res.status);
      show('failed');
      bubble('Sorry — something went wrong. Please try again.', 'in');
    } else if (d.needs_human || !d.subcategory) {
      els.abtext.textContent = `“${text}” could not be classified safely.`;
      show('abstain');
      bubble(d.reply || 'We could not identify this fault. A technician will contact you.',
             'in', 'escalated to a human');
    } else {
      renderTicket(d);
      bubble(d.reply, 'in', `replied in ${LANG[d.language] || d.language}`);
    }
  } catch (err) {
    typingOff(); stopSteps(false);
    els.failed.textContent = 'Network error: ' + err.message;
    show('failed');
  } finally {
    busy = false;
    $('#send').disabled = false;
    $('#msg').focus();
  }
}

$('#composer').addEventListener('submit', e => { e.preventDefault(); send($('#msg').value); });
document.querySelectorAll('.chip').forEach(c =>
  c.addEventListener('click', () => { $('#msg').value = c.dataset.msg; $('#msg').focus(); }));
