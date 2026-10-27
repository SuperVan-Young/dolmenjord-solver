"""Large-level fallback: placement exact cover + road-flow constraints using OR-Tools.
Install: pip install ortools
Run: python solve_constraint.py
"""
from project_paths import LEVELS, SOLUTIONS
import json,time
from pathlib import Path
from collections import defaultdict
from ortools.sat.python import cp_model
from solve_dolmenjord import rotate,verify

def solve_constraint(level,catalog,timeout=180,depth=False):
    t0=time.perf_counter();board=sorted((c['x'],c['z']) for c in level['gridCells']);bs=set(board)
    model=cp_model.CpModel();covered=defaultdict(list);bytype=defaultdict(list);roadcover=defaultdict(list);placements=[]
    road={p:model.new_bool_var(f'r_{p}') for p in board}
    for name,count in level['placedPieceCounts'].items():
        shape=catalog[name];seen=set()
        for r in range(4):
            offsets={rotate(p,r) for p in shape['cells']};front={rotate(p,r) for p in shape['fronts']};ox,oz=next(iter(offsets))
            for x,z in board:
                a=(x-ox,z-oz);cells=frozenset((a[0]+u,a[1]+v) for u,v in offsets);doors=frozenset((a[0]+u,a[1]+v) for u,v in front)
                if not cells<=bs or not doors<=bs or cells&doors or (cells,doors) in seen:continue
                seen.add((cells,doors));v=model.new_bool_var('p'+str(len(placements)))
                placements.append((v,{'name':name,'anchor':list(a),'rotation':r}));bytype[name].append(v)
                for c in cells:
                    covered[c].append(v)
                    if shape['type']==1:roadcover[c].append(v)
                for c in doors:model.add_implication(v,road[c])
        model.add(sum(bytype[name])==count)
    for c in board:
        model.add_exactly_one(covered[c]);model.add(road[c]==sum(roadcover[c]))
    y=round(level['gridWorldHeight']);starts=level['startPoints']
    seeds={s['componentId']:{(x,z) for x,z in board if (x-s['gridPosition'][0])**2+(y-s['gridPosition'][1])**2+(z-s['gridPosition'][2])**2<=1} for s in starts}
    neighbors={p:[q for q in [(p[0]+1,p[1]),(p[0]-1,p[1]),(p[0],p[1]+1),(p[0],p[1]-1)] if q in bs] for p in board}
    def add_flow(source,target=None):
        cap=len(board) if target is None else 1
        incoming=defaultdict(list);outgoing=defaultdict(list)
        # Restrict pair flow to its board component.
        region=set(source);queue=list(source)
        while queue:
            p=queue.pop()
            for q in neighbors[p]:
                if q not in region:region.add(q);queue.append(q)
        for p in region:
            for q in neighbors[p]:
                f=model.new_int_var(0,cap,'f');model.add(f<=cap*road[p]);model.add(f<=cap*road[q]);outgoing[p].append(f);incoming[q].append(f)
        supplies=[];sinks=[]
        for p in region:
            supply=0;sink=road[p] if target is None else 0
            if p in source:
                supply=model.new_int_var(0,cap,'s');model.add(supply<=cap*road[p]);supplies.append(supply)
            if target is not None and p in target:
                sink=model.new_int_var(0,1,'t');model.add(sink<=road[p]);sinks.append(sink)
            model.add(sum(incoming[p])+supply==sum(outgoing[p])+sink)
        if target is not None:model.add(sum(supplies)==1);model.add(sum(sinks)==1)
    if not depth:
        add_flow(set().union(*seeds.values()))
        for s in starts:
            for target in s['pointNeedConnect']:add_flow(seeds[s['componentId']],seeds[target])
    else:
        unseen=set(board)
        while unseen:
            region={unseen.pop()};queue=list(region)
            while queue:
                p=queue.pop()
                for q in neighbors[p]:
                    if q in unseen:unseen.remove(q);region.add(q);queue.append(q)
            local=[s for s in starts if seeds[s['componentId']]&region]
            if not local:raise ValueError('Region has no start')
            linked={local[0]['componentId']}
            while True:
                before=len(linked)
                for s in local:
                    for target in s['pointNeedConnect']:
                        if s['componentId'] in linked or target in linked:linked|={s['componentId'],target}
                if len(linked)==before:break
            if linked!={s['componentId'] for s in local}:raise ValueError('Depth fallback requires one connected start group per island')
            roots=seeds[local[0]['componentId']]&region
            ranks={p:model.new_int_var(0,len(region),'depth') for p in region}
            for p in region:
                model.add(ranks[p]>=road[p]);model.add(ranks[p]<=len(region)*road[p])
                if p in roots:model.add(ranks[p]==road[p]);continue
                parents=[]
                for q in neighbors[p]:
                    parent=model.new_bool_var('parent');parents.append(parent)
                    model.add_implication(parent,road[q]);model.add_implication(parent,road[p])
                    model.add(ranks[q]<ranks[p]).only_enforce_if(parent)
                model.add(sum(parents)>=road[p])
            for s in local[1:]:model.add(sum(road[p] for p in seeds[s['componentId']]&region)>=1)
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=timeout;solver.parameters.num_search_workers=8
    print('Constraint model:',len(placements),'placements',len(board),'cells',flush=True)
    status=solver.solve(model)
    found=status in (cp_model.OPTIMAL,cp_model.FEASIBLE)
    selected=[p for v,p in placements if solver.value(v)] if found else []
    check=verify(level,catalog,selected) if found else None
    if check:assert check['valid'],check
    return {'level':level['number'],'name':level['name'],'status':'solved' if found else solver.status_name(status),
            'seconds':round(time.perf_counter()-t0,6),'strategy':'CP-SAT exact cover + '+('rooted road depths' if depth else 'road flows'),
            'placements':selected,'validation':check,'stats':{'branches':solver.num_branches,'conflicts':solver.num_conflicts,'candidatePlacements':len(placements)}}

if __name__=='__main__':
    SOLUTIONS.parent.mkdir(parents=True,exist_ok=True);data=json.loads(LEVELS.read_text(encoding='utf8'))
    result=solve_constraint(data['levels'][59],{c['name']:c for c in data['catalog']},180,depth=True)
    (SOLUTIONS.parent/'level60_constraint.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(result['status'],result['seconds'],result['stats'])
