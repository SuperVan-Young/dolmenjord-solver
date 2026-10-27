"""Generate a self-contained HTML gallery and one SVG per solved level."""
from project_paths import LEVELS, SOLUTIONS, LAYOUTS
import html
import json
from pathlib import Path
from solve_dolmenjord import geometry

root=LAYOUTS
root.mkdir(parents=True,exist_ok=True)
data=json.loads(LEVELS.read_text(encoding='utf8'))
results=json.loads(SOLUTIONS.read_text(encoding='utf8'))['results']
catalog={c['name']:c for c in data['catalog']}
house_colors=['#e7ac61','#f0c584','#d58a51','#e4b79a','#cf9d69','#f0d19f']
road_colors=['#76b9b0','#90cdc2','#5da69b','#a8d9cc','#70b4bc','#a2ccc7']


def svg(level,result):
    board={(c['x'],c['z']) for c in level['gridCells']}
    starts=[(s['gridPosition'][0],s['gridPosition'][2]) for s in level['startPoints']]
    allcells=board|set(starts);xmin=min(x for x,z in allcells);xmax=max(x for x,z in allcells)
    zmin=min(z for x,z in allcells);zmax=max(z for x,z in allcells)
    cell=46;margin=40;w=(xmax-xmin+1)*cell+2*margin;h=(zmax-zmin+1)*cell+2*margin
    def xy(p):return margin+(p[0]-xmin)*cell,margin+(zmax-p[1])*cell
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Level {level["number"]} solution">',
         '<style>text{font-family:system-ui,sans-serif}.axis{fill:#68786f;font-size:11px}.label{font-size:12px;font-weight:700;fill:#233a34;paint-order:stroke;stroke:#ffffffaa;stroke-width:2px}</style>',
         f'<rect width="{w}" height="{h}" fill="#f5f7f2" rx="12"/>']
    for x in range(xmin,xmax+1):
        sx,_=xy((x,zmax));out.append(f'<text class="axis" x="{sx+23}" y="23" text-anchor="middle">{x}</text>')
    for z in range(zmin,zmax+1):
        _,sy=xy((xmin,z));out.append(f'<text class="axis" x="25" y="{sy+27}" text-anchor="end">{z}</text>')
    for p in board:
        x,y=xy(p);out.append(f'<rect x="{x}" y="{y}" width="46" height="46" fill="#fff" stroke="#d6ded7"/>')
    counts={0:0,1:0};legend=[];doors=[]
    for p in result['placements']:
        shape=catalog[p['name']];kind=shape['type'];counts[kind]+=1
        label=('H' if kind==0 else 'R')+str(counts[kind]);color=(house_colors if kind==0 else road_colors)[(counts[kind]-1)%6]
        cells=geometry(shape,p['anchor'],p['rotation']);fronts=geometry(shape,p['anchor'],p['rotation'],'fronts')
        out.append(f'<g class="{"house" if kind==0 else "road"}"><title>{label}: {p["name"]}; anchor {p["anchor"]}; yaw {p["rotation"]*90}°</title>')
        for point in cells:
            x,y=xy(point);out.append(f'<rect x="{x}" y="{y}" width="46" height="46" fill="{color}" stroke="#ffffff55"/>')
            px,pz=point
            for neighbor,line in [((px-1,pz),(x,y,x,y+46)),((px+1,pz),(x+46,y,x+46,y+46)),
                                  ((px,pz+1),(x,y,x+46,y)),((px,pz-1),(x,y+46,x+46,y+46))]:
                if neighbor not in cells:
                    a,b,c,d=line;out.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="#36564a" stroke-width="2"/>')
        anchor=min(cells,key=lambda p:(-p[1],p[0]));x,y=xy(anchor)
        out.append(f'<text class="label" x="{x+23}" y="{y+27}" text-anchor="middle">{label}</text></g>')
        doors.extend(fronts)
        legend.append(f'<tr><td><span class="swatch" style="background:{color}"></span>{label}</td><td>{p["name"]}</td><td>{p["anchor"]}</td><td>{p["rotation"]*90}°</td></tr>')
    for point in set(doors):
        x,y=xy(point);out.append(f'<circle class="door" cx="{x+23}" cy="{y+35}" r="5" fill="#fff9ec" stroke="#8a4b18" stroke-width="2"><title>Required door cell</title></circle>')
    for i,p in enumerate(starts,1):
        x,y=xy(p);out.append(f'<circle cx="{x+23}" cy="{y+23}" r="17" fill="#334f47"/><text x="{x+23}" y="{y+27}" fill="white" font-size="12" text-anchor="middle">S{i}</text>')
    out.append('</svg>')
    return ''.join(out),''.join(legend)


cards=[];image_dir=root/'level_images';image_dir.mkdir(exist_ok=True)
for result in results:
    if result['status']!='solved':continue
    level=data['levels'][result['level']-1];image,legend=svg(level,result)
    (image_dir/f'level_{result["level"]:02}.svg').write_text(image,encoding='utf8')
    requirements=[];sids={s['componentId']:i+1 for i,s in enumerate(level['startPoints'])}
    for s in level['startPoints']:
        for target in s['pointNeedConnect']:requirements.append(f'S{sids[s["componentId"]]} ↔ S{sids[target]}')
    stats=result['stats']
    method='CP-SAT：精确覆盖与道路连通约束' if 'CP-SAT' in str(result.get('strategy','')) else '房屋剪枝搜索 + 道路精确覆盖'
    stattext=(f"候选摆法 {stats.get('candidatePlacements',0)} · 分支 {stats.get('branches',0)} · 冲突 {stats.get('conflicts',0)}" if 'CP-SAT' in method else f"Macro 节点 {stats.get('macroNodes',0)} · 完整房屋方案 {stats.get('completeMacroLayouts',0)} · 道路节点 {stats.get('roadNodes',0)}")
    cards.append(f'''<article class="{'wide' if len(level['gridCells'])>200 else ''}" id="level-{result['level']}"><div class="cardhead"><h2>第 {result['level']:02} 关</h2><span class="pass">已校验</span></div>
    <p class="meta">{len(level['gridCells'])} 格 · {len(result['placements'])} 件 · successful attempt: {result['seconds']:.6f} s</p>
    <div class="drawing">{image}</div><p class="hint">{('指定连通：'+', '.join(requirements)) if requirements else '道路每个连通区域须接入至少一个起点'}</p>
    <details><summary>摆放坐标与搜索统计</summary><p>{method} · {stattext}</p>
    <table><thead><tr><th>ID</th><th>物件</th><th>锚点 [x,z]</th><th>Unity Y 旋转</th></tr></thead><tbody>{legend}</tbody></table></details></article>''')

page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dolmenjord · 前 10 关求解</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf1e9;color:#233a34;font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}
header{background:#233f35;color:#f6f3e7;padding:40px max(5vw,24px)}h1{font-size:32px;letter-spacing:.02em;margin:0}header p{max-width:850px;color:#ccdbce}
nav{position:sticky;top:0;background:#edf1e9ee;backdrop-filter:blur(8px);padding:14px 5vw;display:flex;gap:8px;align-items:center;flex-wrap:wrap;z-index:2;border-bottom:1px solid #d0dbce}
button,nav a{border:1px solid #b4c5b8;padding:7px 13px;border-radius:7px;background:#fff;color:#233a34;font:inherit;text-decoration:none;cursor:pointer}
button.active{background:#315747;color:white}main{max-width:1500px;margin:auto;padding:28px 4vw;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
article{background:white;border:1px solid #d4ddd0;border-radius:15px;padding:22px;scroll-margin-top:100px}.cardhead{display:flex;justify-content:space-between;align-items:center}h2{margin:0;font-size:23px}.pass{background:#e4f3e7;color:#27613a;padding:3px 10px;border-radius:20px;font-size:12px}.meta,.hint{color:#65766c;font-size:13px}.drawing{background:#f5f7f2;border-radius:10px;text-align:center;padding:10px}.drawing svg{width:100%;max-height:530px;vertical-align:middle}.macro-only .road{display:none}summary{cursor:pointer;font-weight:600}table{width:100%;font-size:11px;border-collapse:collapse;margin-top:12px}td,th{padding:5px;text-align:left;border-bottom:1px solid #e7ece3}.swatch{display:inline-block;width:10px;height:10px;margin-right:5px;border-radius:2px}footer{padding:24px 5vw;color:#64766a;font-size:13px}@media(max-width:800px){main{grid-template-columns:1fr}header{padding:25px}h1{font-size:25px}nav{position:static}}@media print{nav{display:none}article{break-inside:avoid}main{display:block}details{display:none}}
</style><header><h1>Dolmenjord · Macro placement → Road tiling</h1><p>前 10 关：房屋由大到小搜索，保留门口、检查可达性；道路用精确覆盖填满剩余格子。每个解均经独立校验器检查。</p><p>暖色 H = 房屋 · 青色 R = 道路 · 小圆圈 = 必须铺路的门口格 · 深色 S = 起点。横轴 x，纵轴 z；同一物件有连续深色外框。</p></header>
<nav><button id="full" class="active" onclick="setMode(false)">完整布局</button><button id="macro" onclick="setMode(true)">只看房屋阶段</button>'''
page+='<label for="jump">跳转关卡</label><select id="jump" onchange="location.hash=\'level-\'+this.value" style="font:inherit;padding:8px;border-radius:7px;border:1px solid #b4c5b8">'
page+=''.join(f'<option value="{r["level"]}">第 {r["level"]:02} 关</option>' for r in results if r['status']=='solved')+'</select>'
page+='</nav><main>'+''.join(cards)+'''</main><footer>验证依据：本地 Assembly-CSharp.dll 的通关规则。此处为离线规则校验，尚未自动回放到游戏内。原始关卡里的摆放不参与搜索；只使用地图、物件形状与数量、门口及起点约束。</footer>
<script>function setMode(m){document.body.classList.toggle('macro-only',m);document.getElementById('full').classList.toggle('active',!m);document.getElementById('macro').classList.toggle('active',m)}</script></html>'''
page=page.replace('前 10 关',f'全部 {len(cards)} 关' if len(cards)==60 else f'已求解 {len(cards)} 关')
page=page.replace('</style>','.wide{grid-column:1 / -1}.wide .drawing svg{max-height:1400px}</style>')
if any('CP-SAT' in str(r.get('strategy','')) for r in results):
    page=page.replace('每个解均经独立校验器检查。','第 60 关采用 CP-SAT 精确覆盖与道路连通约束。每个解均经独立校验器检查。')
(root/'solutions.html').write_text(page,encoding='utf8')
print(f'Wrote solutions.html and {len(cards)} SVG files')
