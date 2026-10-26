"""Two-stage macro placement / road exact-cover solver. Python standard library only.
Run: python solve_dolmenjord.py --levels 10
"""
import argparse
import json
import time
import random
from collections import Counter, deque
from pathlib import Path


def rotate(p, r):
    x,z=p
    for _ in range(r): x,z=z,-x
    return x,z


def geometry(shape, anchor, rotation, field='cells'):
    return {(anchor[0]+x,anchor[1]+z) for x,z in (rotate(p,rotation) for p in shape[field])}


def verify(level, catalog, placements):
    """Independent set-based validation; no search masks or candidate cache used."""
    errors=[]; board={(c['x'],c['z']) for c in level['gridCells']}
    expected=Counter(level['placedPieceCounts']); actual=Counter(p['name'] for p in placements)
    if actual!=expected: errors.append('inventory mismatch')
    occupied=set(); roads=[]; doors=set()
    for p in placements:
        shape=catalog[p['name']]
        cells=geometry(shape,p['anchor'],p['rotation'])
        if not cells<=board: errors.append('outside board')
        if cells & occupied: errors.append('overlap')
        occupied |= cells
        if shape['type']==1: roads.append(cells)
        else: doors |= geometry(shape,p['anchor'],p['rotation'],'fronts')
    if occupied!=board: errors.append('incomplete coverage')
    road_cells=set().union(*roads) if roads else set()
    if not doors<=road_cells: errors.append('door without road')
    y=round(level['gridWorldHeight'])
    roads3=[{(x,y,z) for x,z in cells} for cells in roads]
    starts={p['componentId']:tuple(p['gridPosition']) for p in level['startPoints']}
    def adjacent(a,b): return sum((a[i]-b[i])**2 for i in range(3))<=1
    def expand(seeds):
        reached=set(seeds); pending=list(roads3)
        while True:
            rest=[]; changed=False
            for cells in pending:
                if any(adjacent(a,b) for a in cells for b in reached):
                    reached |= cells; changed=True
                else: rest.append(cells)
            pending=rest
            if not changed:return reached,pending
    _,unreached=expand(starts.values())
    if unreached: errors.append('road piece disconnected from all starts')
    for s in level['startPoints']:
        reached,_=expand([starts[s['componentId']]])
        for target in s['pointNeedConnect']:
            if target not in starts or not any(adjacent(starts[target],v) for v in reached):
                errors.append('required start connection missing')
    return {'valid':not errors,'errors':errors,'coveredCells':len(occupied),
            'roadCells':len(road_cells),'doorCells':len(doors),
            'checks':['inventory','bounds','overlap','full coverage','all fronts on road',
                      'road components reach a start','required start connections']}


def solve(level,catalog,timeout=120,strategy=0):
    started=time.perf_counter(); stats=Counter(); board=sorted((c['x'],c['z']) for c in level['gridCells'])
    indices={p:i for i,p in enumerate(board)}; full=(1<<len(board))-1
    def mask(cells):return sum(1<<indices[p] for p in cells)
    neighbors=[]
    for x,z in board:
        neighbors.append(mask({p for p in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)] if p in indices}))
    y=round(level['gridWorldHeight'])
    starts=level['startPoints']
    seed_masks={s['componentId']:mask({(x,z) for x,z in board
        if (x-s['gridPosition'][0])**2+(y-s['gridPosition'][1])**2+(z-s['gridPosition'][2])**2<=1}) for s in starts}
    seed_all=0
    for m in seed_masks.values():seed_all |= m
    def flood(free,seeds):
        seen=seeds & free; todo=seen
        while todo:
            bit=todo & -todo; todo-=bit
            new=neighbors[bit.bit_length()-1] & free & ~seen
            seen |= new; todo |= new
        return seen
    candidates={}; bycell={}
    for name in level['placedPieceCounts']:
        shape=catalog[name]; options=[]; unique=set()
        for r in range(4):
            offsets={rotate(p,r) for p in shape['cells']}; front={rotate(p,r) for p in shape['fronts']}
            ox,oz=next(iter(offsets))
            for bx,bz in board:
                ax,az=bx-ox,bz-oz
                cells={(ax+x,az+z) for x,z in offsets}; doors={(ax+x,az+z) for x,z in front}
                if not cells<=indices.keys() or not doors<=indices.keys() or cells & doors:continue
                m=mask(cells); d=mask(doors); key=(m,d)
                if key in unique:continue
                unique.add(key);options.append({'name':name,'anchor':[ax,az],'rotation':r,'mask':m,'doors':d})
        if strategy:
            rng=random.Random(strategy*1000+sum(map(ord,name)))
            rng.shuffle(options)
            if strategy==1:
                def boundary(p):
                    bits=p['mask']; edges=0
                    while bits:
                        bit=bits & -bits;bits-=bit
                        edges+=4-neighbors[bit.bit_length()-1].bit_count()
                    return -edges
                if shape['type']==0:options.sort(key=boundary)
        candidates[name]=options
        bycell[name]=[[p for p in options if p['mask'] & (1<<i)] for i in range(len(board))]
    houses=[]; roadnames=[]; roadcounts=[]
    for name,count in level['placedPieceCounts'].items():
        if catalog[name]['type']==0:houses.extend([name]*count)
        else:roadnames.append(name);roadcounts.append(count)
    houses.sort(key=lambda n:(-len(catalog[n]['cells']),len(candidates[n]),n))
    road_area=sum(len(catalog[n]['cells'])*c for n,c in zip(roadnames,roadcounts))
    remaining_area=[sum(len(catalog[n]['cells']) for n in houses[i:]) for i in range(len(houses)+1)]
    def check_time():
        if time.perf_counter()-started>timeout:raise TimeoutError()
    road_failed=set()
    def tile(free,counts):
        stats['roadNodes']+=1
        if stats['roadNodes']%2048==0:check_time()
        if not free:return [] if not any(counts) else None
        key=(free,counts)
        if key in road_failed:stats['roadMemoHits']+=1;return None
        best=None; bits=free
        while bits:
            bit=bits & -bits;bits-=bit;i=bit.bit_length()-1
            options=[(k,p) for k,n in enumerate(roadnames) if counts[k]
                     for p in bycell[n][i] if p['mask'] & free==p['mask']]
            if not options:stats['roadDeadCell']+=1;road_failed.add(key);return None
            if best is None or len(options)<len(best):best=options
            if len(best)==1:break
        for k,p in best:
            updated=list(counts);updated[k]-=1
            result=tile(free ^ p['mask'],tuple(updated))
            if result is not None:return [p]+result
        road_failed.add(key);return None
    def macro(i,occupied,reserved,chosen,last_index):
        stats['macroNodes']+=1
        if stats['macroNodes']%1024==0:check_time()
        free=full ^ occupied
        reachable=flood(free,seed_all)
        if reserved & ~reachable or reachable.bit_count()<road_area:
            stats['reachabilityPrunes']+=1;return None
        # Unreachable empty cells may still be occupied by future houses.
        if (free & ~reachable).bit_count()>remaining_area[i]:
            stats['unfillablePocketPrunes']+=1;return None
        for s in starts:
            if not s['pointNeedConnect']:continue
            seen=flood(free,seed_masks[s['componentId']])
            if any(not seen & seed_masks[t] for t in s['pointNeedConnect']):
                stats['requiredConnectionPrunes']+=1;return None
        if i==len(houses):
            stats['completeMacroLayouts']+=1
            roads=tile(free,tuple(roadcounts))
            return chosen+roads if roads is not None else None
        name=houses[i]
        lower=last_index+1 if i and houses[i-1]==name else 0
        for j in range(lower,len(candidates[name])):
            p=candidates[name][j]
            if p['mask'] & (occupied|reserved) or p['doors'] & occupied:continue
            new_occ=occupied|p['mask'];new_res=reserved|p['doors']
            if new_res.bit_count()>road_area:stats['doorBudgetPrunes']+=1;continue
            # Every remaining house type must retain at least one candidate.
            if any(not any(not(q['mask'] & (new_occ|new_res) or q['doors'] & new_occ)
                           for q in candidates[n]) for n in set(houses[i+1:])):
                stats['forwardCheckPrunes']+=1;continue
            result=macro(i+1,new_occ,new_res,chosen+[p],j)
            if result is not None:return result
        return None
    try:
        found=macro(0,0,0,[],-1);status='solved' if found is not None else 'unsatisfiable'
    except TimeoutError:found=None;status='timeout'
    placements=[{k:v for k,v in p.items() if k not in ('mask','doors')} for p in found] if found is not None else []
    validation=verify(level,catalog,placements) if found is not None else None
    if validation and not validation['valid']:raise AssertionError(validation)
    return {'level':level['number'],'name':level['name'],'status':status,'strategy':strategy,
            'seconds':round(time.perf_counter()-started,6),'stats':dict(stats),
            'placements':placements,'validation':validation,
            'candidateCounts':{n:len(v) for n,v in candidates.items()}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--levels',type=int,default=10)
    parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--strategy',type=int,default=0,help='0: original order; 1: boundary first; >=2: seeded shuffle')
    parser.add_argument('--restarts',type=int,default=3,help='Extra candidate-order attempts after timeout')
    parser.add_argument('--resume',action='store_true',help='Reuse existing solutions after independent verification')
    parser.add_argument('--constraint-fallback',action='store_true',help='Use optional OR-Tools model after DFS timeouts')
    parser.add_argument('--input',type=Path,default=Path(__file__).with_name('dolmenjord_levels.json'))
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('solutions.json'))
    args=parser.parse_args();data=json.loads(args.input.read_text(encoding='utf8'))
    catalog={x['name']:x for x in data['catalog']};results=[];previous={}
    if args.resume and args.output.exists():
        previous={r['level']:r for r in json.loads(args.output.read_text(encoding='utf8'))['results']}
    for level in data['levels'][:args.levels]:
        old=previous.get(level['number'])
        if old and old['status']=='solved' and verify(level,catalog,old['placements'])['valid']:
            result=old
        else:
            attempts=[]
            for strategy in range(args.strategy,args.strategy+args.restarts+1):
                result=solve(level,catalog,args.timeout,strategy)
                attempts.append({'strategy':strategy,'status':result['status'],'seconds':result['seconds']})
                if result['status']!='timeout':break
            if result['status']=='timeout' and args.constraint_fallback:
                from solve_constraint import solve_constraint
                result=solve_constraint(level,catalog,args.timeout,depth=level['number']==60)
                attempts.append({'strategy':result['strategy'],'status':result['status'],'seconds':result['seconds']})
            result['attempts']=attempts
        results.append(result)
        print(f"Level {level['number']:02}: {result['status']} {result['seconds']:.3f}s {result['stats']}",flush=True)
        args.output.write_text(json.dumps({'algorithm':'macro DFS + road exact cover; optional CP-SAT fallback for large levels','results':results},indent=2),encoding='utf8')


if __name__=='__main__':main()
