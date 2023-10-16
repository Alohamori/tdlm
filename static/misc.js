let modal, player, prev, resume;

const $E = (tag, props={}, ch=[]) => ch.reduce((e,c) => (e.appendChild(c),e),Object.assign(document.createElement(tag),props));

const qs = s => document.querySelector(s);
const qsa = s => document.querySelectorAll(s);
const hide = s => { if (e = qs(s)) e.style.display = 'none'; }
const show = (s, d) => { if (e = qs(s)) e.style.display = d || 'block'; }

const ls_toggle = key =>
  localStorage[key] ? localStorage.removeItem(key) : localStorage[key] = 1;

const toggle_notes = table => {
  (ls_toggle(`hide_${table}_notes`) ? hide : show)('.column-descriptions');
  qs('.actions-menu-links summary').click();
};

function populate_sub(e) {
  const opt = e.options[e.selectedIndex];
  const foreign = opt.getAttribute('data-foreign');
  const sub = `#sub${e.name}`;
  if (!foreign) {
    return hide(sub);
  }

  const [ftab, ...fcols] = foreign.split(',');
  const subsel = qs(`${sub} select`);
  subsel.innerHTML = '<option>- subcolumn -</option>' + fcols.map(c => `<option>${c}</option>`).join('');
  show(sub, 'inline-block');
}

function update_main(e, targ) {
  const main = e.form[targ];
  const opt = main.options[main.selectedIndex];
  opt.value = opt.innerText + (e.value[0] != '-' ? `.${e.value}` : '');
}

function play_task(task, vid, ts, ev) {
  if (!modal) modal = document.getElementById('modal');
  modal.style.display = 'flex';
  if (task != prev) player.loadVideoById(vid, ts);
  else {
    player.seekTo(resume);
    player.playVideo();
  }
  ev.preventDefault();
  prev = task;
}

function hide_player() {
  modal.style.display = 'none';
  player.pauseVideo();
  resume = player.getCurrentTime();
}

function hide_if_irrelevant(column) {
  const cells = qsa(`td.col-${column}`);
  const empty = Array.from(cells).every(e => e.innerText == '\xa0');
  if (empty)
    document.styleSheets[0].insertRule(`.col-${column} { display: none !important; }`);
}

function favor_tag(t) {
  qsa('td.col-tags').forEach(e => {
    const c = e.querySelector(`a[href*='${t}']`);
    e.prepend(e.removeChild(c));
  });
}

const divmod = (x, y) => [Math.floor(x / y), x % y];

function start_timer(e, dt) {
  let elapsed = Math.floor((new Date() - new Date(dt)) / 1000);
  let d, h, m, s;
  setInterval(function() {
    elapsed += 1;
    s = elapsed;
    [d, s] = divmod(s, 86400);
    [h, s] = divmod(s, 3600);
    [m, s] = divmod(s, 60);
    [h, m, s] = [h, m, s].map(v => String(v).padStart(2, '0'));
    e.innerText = `${d}:${[h, m, s].join(':')}`;
  }, 1000);
}

function onYouTubeIframeAPIReady() {
  modal = document.getElementById('modal');
  player = new YT.Player('player', {
    events: { 'onReady': ev => ev.target.setVolume(30) }
  });

  window.addEventListener('click', ev => ev.target == modal && hide_player());
  window.addEventListener('keyup', ev => ev.keyCode == 27 && hide_player());
}

window.addEventListener('DOMContentLoaded', () => {
  if (location.search.indexOf('_simple=1') != -1) {
    qsa('.content > :not(.table-wrapper)').forEach(e => e.style.display = 'none');
    qs('.table-wrapper').style.marginTop = '1em';
  }

  if (qs('details') && localStorage[`hide_${qs('h1').innerText}_notes`])
      hide('.column-descriptions');

  qsa('.col-measurement abbr').forEach(e => start_timer(e, e.title.split(' ')[2]));
});
