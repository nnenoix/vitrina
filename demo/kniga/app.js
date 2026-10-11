/* Книга достижений: каталог из Google-таблицы.
   Таблица = панель управления: одна строка = один участник.
   Колонки (первая строка): Опубликовать | ФИО | Категория | Достижение | Описание | Фото | Дата
   Карточка видна на сайте, только если в «Опубликовать» стоит «да». */
var SHEET_ID = '1tFlNbtrdMR4I_06VyCr22guCmzBJRONtNgZ6MsBIf-s';            // id таблицы из её адреса: docs.google.com/spreadsheets/d/<ID>/edit
var SHEET_TAB = 'Участники';  // имя листа
var FALLBACK = 'data/sample.csv';
// приём заявок: веб-приложение Apps Script в той же таблице (письмо админу + лист «Заявки»)
var FORM_URL = 'https://script.google.com/macros/s/AKfycbyFEDAeESRqGfBaNWtjdPV9q__ClBhnM2XMJ9HLn8c3iv09IDpl8TAyDP9_lTxKk1LJ/exec';

var CATS = {
  'Академические достижения': 'acad',
  'Спортивные рекорды': 'sport',
  'Творчество и активизм': 'art'
};
var people = [], curCat = '', curQ = '';

function parseCSV(text) {
  var rows = [], row = [], cell = '', q = false;
  for (var i = 0; i < text.length; i++) {
    var ch = text[i];
    if (q) {
      if (ch === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; }
      else cell += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') { row.push(cell); cell = ''; }
    else if (ch === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; }
    else if (ch !== '\r') cell += ch;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  return rows.filter(function (r) { return r.some(function (c) { return c.trim() !== ''; }); });
}

function toObjects(rows) {
  var head = rows[0].map(function (h) { return h.trim().toLowerCase(); });
  function col(name) { return head.indexOf(name); }
  var iPub = col('опубликовать');
  return rows.slice(1).map(function (r) {
    function v(name) { var i = col(name); return i >= 0 && r[i] ? r[i].trim() : ''; }
    return {
      pub: iPub < 0 ? true : /^(да|yes|\+|1|true|✓|✔)$/i.test((r[iPub] || '').trim()),
      name: v('фио'), cat: v('категория'), ach: v('достижение'),
      desc: v('описание'), photo: photoUrl(v('фото')), date: v('дата')
    };
  }).filter(function (p) { return p.pub && p.name; });
}

// ссылку «поделиться» с Google Диска превращаем в прямую картинку
function photoUrl(u) {
  if (!u) return '';
  var m = u.match(/drive\.google\.com\/(?:file\/d\/|open\?id=|uc\?(?:export=\w+&)?id=)([\w-]+)/);
  return m ? 'https://drive.google.com/thumbnail?id=' + m[1] + '&sz=w1200' : u;
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
function initials(n) { return n.split(/\s+/).slice(0, 2).map(function (w) { return w[0] || ''; }).join('').toUpperCase(); }
var PALETTE = ['#2f6fe4', '#e2572b', '#8b3fd9', '#0f9d76', '#d9a521'];
function colorFor(n) { var h = 0; for (var i = 0; i < n.length; i++) h = (h * 31 + n.charCodeAt(i)) >>> 0; return PALETTE[h % PALETTE.length]; }

function imgBlock(p, cls) {
  if (p.photo) return '<div class="' + cls + '" style="background-image:url(\'' + esc(p.photo) + '\')"></div>';
  return '<div class="' + cls + '" style="background:' + colorFor(p.name) + '"><span class="initials">' + esc(initials(p.name)) + '</span></div>';
}
function tag(p) { return '<span class="tag tag-' + (CATS[p.cat] || 'other') + '">' + esc(p.cat || 'Без категории') + '</span>'; }

function render() {
  var q = curQ.toLowerCase();
  var list = people.filter(function (p) {
    return (!curCat || p.cat === curCat) &&
      (!q || (p.name + ' ' + p.ach + ' ' + p.desc).toLowerCase().indexOf(q) >= 0);
  });
  var grid = document.getElementById('grid');
  if (!list.length) { grid.innerHTML = '<p class="empty">В этой категории пока никого нет.</p>'; return; }
  grid.innerHTML = list.map(function (p) {
    return '<button class="card" data-i="' + people.indexOf(p) + '">' + imgBlock(p, 'card-img') +
      '<div class="card-body">' + tag(p) + '<h3>' + esc(p.name) + '</h3>' +
      (p.ach ? '<div class="ach">' + esc(p.ach) + '</div>' : '') +
      '<p>' + esc(p.desc) + '</p></div></button>';
  }).join('');
}

function openModal(id) { document.getElementById(id).hidden = false; document.body.style.overflow = 'hidden'; }
function closeModals() {
  document.querySelectorAll('.modal').forEach(function (m) { m.hidden = true; });
  document.body.style.overflow = '';
}
function showPerson(p) {
  document.querySelector('#person .person-in').innerHTML = imgBlock(p, 'person-img') +
    '<div class="person-body">' + tag(p) + '<h3>' + esc(p.name) + '</h3>' +
    (p.ach ? '<p class="ach">' + esc(p.ach) + '</p>' : '') + '<p>' + esc(p.desc) + '</p>' +
    (p.date ? '<div class="date">' + esc(p.date) + '</div>' : '') + '</div>';
  openModal('person');
}

function load() {
  var url = SHEET_ID
    ? 'https://docs.google.com/spreadsheets/d/' + SHEET_ID + '/gviz/tq?tqx=out:csv&sheet=' + encodeURIComponent(SHEET_TAB) + '&t=' + Date.now()
    : FALLBACK;
  return fetch(url, { cache: 'no-store' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
    .catch(function () { return fetch(FALLBACK).then(function (r) { return r.text(); }); });
}

document.addEventListener('DOMContentLoaded', function () {
  load().then(function (t) { people = toObjects(parseCSV(t)); render(); })
    .catch(function () { document.getElementById('grid').innerHTML = '<p class="empty">Не удалось загрузить каталог. Обновите страницу.</p>'; });

  document.querySelectorAll('.chip').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.chip').forEach(function (x) { x.classList.remove('is-on'); });
      b.classList.add('is-on'); curCat = b.getAttribute('data-cat'); render();
    });
  });
  document.querySelector('.search').addEventListener('input', function (e) { curQ = e.target.value.trim(); render(); });
  document.getElementById('grid').addEventListener('click', function (e) {
    var c = e.target.closest('.card'); if (c) showPerson(people[+c.getAttribute('data-i')]);
  });
  document.querySelectorAll('[data-open-form]').forEach(function (b) { b.addEventListener('click', function () { openModal('form'); }); });
  document.querySelectorAll('.modal').forEach(function (m) {
    m.addEventListener('click', function (e) { if (e.target === m || e.target.hasAttribute('data-close')) closeModals(); });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModals(); });

  var form = document.querySelector('.rec-form');
  var err = form.querySelector('.form-err'), btn = form.querySelector('button[type=submit]');
  function fail(msg) { err.textContent = msg; err.hidden = false; }
  function readFile(f) {
    return new Promise(function (res, rej) {
      if (!f) return res(null);
      var r = new FileReader();
      r.onload = function () { res({ name: f.name, type: f.type, data: String(r.result).split(',')[1] }); };
      r.onerror = rej; r.readAsDataURL(f);
    });
  }
  form.addEventListener('submit', function (e) {
    e.preventDefault(); err.hidden = true;
    var fd = new FormData(form), f = form.querySelector('input[type=file]').files[0];
    if (!fd.get('fio').trim() || !fd.get('cat') || !fd.get('desc').trim()) return fail('Заполните ФИО, категорию и описание.');
    if (f && f.size > 5 * 1024 * 1024) return fail('Файл больше 5 МБ. Лучше пришлите ссылку.');
    btn.disabled = true; btn.textContent = 'Отправляем…';
    readFile(f).then(function (file) {
      var body = new URLSearchParams();
      ['fio', 'cat', 'desc', 'link', '_honey'].forEach(function (k) { body.append(k, fd.get(k) || ''); });
      if (file) { body.append('fileName', file.name); body.append('fileType', file.type); body.append('fileData', file.data); }
      return fetch(FORM_URL, { method: 'POST', body: body });
    }).then(function (r) { return r.json(); }).then(function (j) {
      if (!j.ok) throw new Error(j.error || 'ошибка');
      form.reset(); closeModals();
      var t = document.getElementById('toast'); t.hidden = false;
      setTimeout(function () { t.hidden = true; }, 5000);
    }).catch(function () {
      fail('Не получилось отправить. Проверьте интернет и попробуйте ещё раз.');
    }).then(function () { btn.disabled = false; btn.textContent = 'Отправить заявку'; });
  });
});
