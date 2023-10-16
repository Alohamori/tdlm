from datasette import hookimpl, Response
import os
from markupsafe import Markup
import json, re

TEAM_ABBRS = '_ F+T JR+R J+R DJ+K R+S AD+P H+M JL+N M+N AB+S A+R AL+T J+K JP+R J+S IL+P D+J EK+R D+E JK+R D+R JK+M D+K JM+R L+M CJ+S A+V DG+M A+C BJ+S M+S DF+J F+I JK+M S+S JL+S'.split()
TAG_SYMS = { 'adapted': '🧬', 'bonus-points': '➕', 'combination': '🔗', 'creative': '🎨', 'filmed': '🎞️', 'hidden-clues': '🔎', 'hidden-rules': '🚫', 'homework': '📓', 'live': '🎪', 'mental': '🧠', 'multiple-brief': '📑', 'novel-brief': '📝', 'objective': '🎯', 'original': '💡', 'physical': '💪', 'point-deductions': '➖', 'prize': '🎁', 'single-brief': '📄', 'social': '📣', 'solo': '👤', 'special': '✨', 'split': '🧾', 'subjective': '⚖️', 'team': '👥', 'tie-breaker': '❗', 'unjudged': '⚫', 'winner-takes-all': '👑' , 'handly': '🖋️', 'Greg': '🗿'}

with open('clip_slugs.json') as f:
    CLIP_SLUGS = json.loads(f.read())

def clean(v):
    return v if type(v) == str else str(int(v)) if v % 1 == 0 else v

def clockify(t):
    s = str(t)
    if t < 60: return clean(t)

    n, frac = int(t), None
    if '.' in s: n, frac = map(int, s.split('.'))

    d, n = divmod(n, 86400)
    h, n = divmod(n, 3600)
    m, n = divmod(n, 60)

    g = [str(v) if u == 'd' else f'{v:02}' for u, v in zip('dhms', [d, h, m, n])]
    c = ':'.join(g[next(i for i, e in enumerate(g) if int(e) > 0):])
    return f'{c}.{frac}' if frac else c

def get_value(row, column):
    v = row[column]
    return v if type(v) == int else v['value']

@hookimpl
def extra_template_vars(table, columns, request):
    modal = table and 'YT' in columns
    def ctype(v):
        s = str(v)
        return 'int' if s[0].isdigit() or s[0] == '-' and s[1].isdigit() else 'str'

    return {'modal': modal, 'cell_type': ctype}

@hookimpl
def extra_body_script(table, request):
    if table == 'tasks':
        tl = set(request.args.getlist('tags__contains') + request.args.getlist('tags__contains'))
        return ';'.join(f'favor_tag("{tag}")' for tag in tl)

@hookimpl
def extra_js_urls(table, columns, view_name):
    if table and 'YT' in columns:
        return ['https://www.youtube.com/player_api']
    if table == None and view_name in ('database', 'table'):
        return ['https://cdn.jsdelivr.net/gh/tofsjonas/sortable@latest/sortable.min.js']

@hookimpl
def extra_css_urls(table, view_name):
    if view_name == 'table' and table in ('attempts', 'discrepancies', 'episodes', 'episode_scores', 'measurements', 'normalized_scores', 'people', 'podcast', 'series', 'series_scores', 'task_readers', 'task_winners', 'title_coiners', 'intros'):
        return ['/static/series.css']

@hookimpl(trylast=True)
def render_cell(datasette, database, table, row, column, value):
    BASE = datasette.setting("base_url") + 'taskmaster'

    if column == 'location' and type(value) == dict:
        u = BASE + '/special_locations/'
        return Markup(f'<a href="{u}{value["value"]}" title="{value["label"]}">special</a>')
        value['label'] = 'special'

    if table == 'measurements' and column == 'measurement':
        if value and type(value) == str and value.startswith('ongoing'):
            return Markup(f'<abbr title="time since {value.split("|")[1]}">ongoing')
        if row['objective']['value'] in (2, 35) and value not in ('?', None):
            return Markup(f'<div class="col-rank">{clockify(value)}')
        return Markup('<center><em>DNF / DQ') if value == None else Markup('<center><em>INCONCLUSIVE') if value == '?' else clean(value)

    if table and column == 'base':
        return value if value != None else Markup('<center><em>DQ')

    if table and column == 'roots':
        return Markup('<br>'.join(json.loads(value)))

    if table == 'intros' and column == 'task' and str(value).startswith('un'):
        return Markup('<center><em>' + value.upper())

    if table == 'intros' and column == 'clip':
        slug = CLIP_SLUGS[0][int(value[1]) - 1] if type(value) == str else CLIP_SLUGS[row['series']['value']][value - 1]
        return Markup(f'<a href="https://i.imgur.com/{slug}.mp4" target="_blank">▶</a>')

    if type(value) == float:
        return clean(value)

    if table and column == 'tags':
        u = BASE + f"/tasks?tags__contains="

        syms = ''.join(f'<a href="{u}{v}"><span title="{v}">{TAG_SYMS[v]}</span></a>' for v in json.loads(value))
        return Markup(syms)

    if table and column == 'TMI':
        kind = {'standard_tasks': 'task', 'tasks': 'task', 'episodes': 'episode', 'series': 'season', 'people': 'person'}[table]
        return Markup(f'<a href="https://taskmaster.info/{kind}.php?id={value}" target="_blank"><span class="out-arrow">➚</span></a>')

    if table and column == 'YT' and value:
        v, t = value.split('|')
        rid = row['id']
        return Markup(f'<a href="https://youtu.be/{v}?t={t}" onclick="javascript:play_task({rid}, \'{v}\', {t}, event);" oncontextmenu="javascript:play_task({rid}, \'{v}\', {int(t) + 10}, event);">▶</a>')

    if table and column in ('finale', 'irregular', 'live', 'special', 'std', 'win', 'studio'):
        return (' ✓')[value]

    if table in ('task_readers', 'task_winners') and column == 'team':
        return (' ✓')[value]

    if table == 'people' and column == 'champion':
        return (' ✓')[value]

    if column == 'np':
        return int(value) if '0' in str(value) else value

    if column == 'latlong':
        ll = ','.join(value.split(',')[::-1])
        return Markup(f'<a href="https://www.google.com/maps/d/u/0/viewer?mid=13aVAoqSldUqiXbfMEAkU2liIX6WL0z-J&ll={ll}" target="_blank"><span class="out-arrow">➚</span></a>')

    if table == 'attempts' and column == 'team' and value:
        value = value['value']
        u = BASE + f'/teams/{value}'
        return Markup(f'<a href="{u}">{TEAM_ABBRS[value]}</a>')

    if table == None and type(value) == str and '[link' in value:
        return Markup(re.sub('\[link\|([^|]+)\|([^]]+)]', r'<a href="taskmaster/\1">\2</a>', value))

@hookimpl
def table_actions(datasette, table):
    acts = []
    tables = datasette.metadata('databases')['taskmaster']['tables']

    if table in tables and 'columns' in tables[table]:
        acts.append({'href': f'javascript:toggle_notes("{table}");', 'label': 'Toggle column notes'})

    return acts

async def cached_static(request):
    sp = '/'.join(request.url.split('/')[-2:])
    cts = {'css': 'text/css', 'js': 'text/javascript', 'png': 'image/png'}
    with open(sp, 'rb') as f:
        return Response(f.read(), content_type=cts[sp.split('.')[-1]], headers={'Cache-Control': 'max-age=3600'})

@hookimpl
def register_routes():
    return [(r"/static/.*", cached_static)]
