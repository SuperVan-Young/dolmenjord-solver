"""Validate solutions, extraction/rotation against source geometry, and rejection cases."""
from project_paths import LEVELS, SOLUTIONS, DOC, VALIDATION
import json
import math
from pathlib import Path
from solve_dolmenjord import geometry, verify

DOC.mkdir(parents=True,exist_ok=True)
data=json.loads(LEVELS.read_text(encoding='utf8'))
solutions=json.loads(SOLUTIONS.read_text(encoding='utf8'))
catalog={c['name']:c for c in data['catalog']}
report={'solutions':[],'sourceFootprintsChecked':0,'rejectedMutations':[]}
for result in solutions['results']:
    level=data['levels'][result['level']-1]
    assert result['status']=='solved'
    check=verify(level,catalog,result['placements'])
    assert check['valid'],check
    report['solutions'].append({'level':result['level'],**check})
    for piece in level['placedPieces']:
        q=piece.get('worldRotation',piece['localRotation']); yaw=math.atan2(2*(q['w']*q['y']+q['x']*q['z']),1-2*(q['y']**2+q['z']**2))
        r=round(yaw/(math.pi/2))%4
        p=piece.get('worldPosition',piece['localPosition']); a=(round(p['x']),round(p['z']))
        expected={(e['x'],e['z']) for e in level['generatedGridEntries'] if e['sourceBuildingId']==piece['componentId']}
        actual=geometry(catalog[piece['nameId']],a,r)
        assert actual==expected,(level['number'],piece['nameId'],actual,expected)
        report['sourceFootprintsChecked']+=1
    # Negative checks independently exercise inventory, bounds/coverage, and doors.
    original=result['placements']
    mutations={'missing_piece':original[:-1],
               'out_of_bounds':[{**p,'anchor':[1000,1000]} if i==0 else p for i,p in enumerate(original)]}
    for label,placements in mutations.items():
        check=verify(level,catalog,placements)
        assert not check['valid'],label
        report['rejectedMutations'].append({'level':level['number'],'case':label,'errors':check['errors']})
# A one-cell house keeps its occupied cell while turning its door off the road.
l=data['levels'][0];p=solutions['results'][0]['placements']
mut=[{**x,'rotation':(x['rotation']+2)%4} if catalog[x['name']]['type']==0 else x for x in p]
check=verify(l,catalog,mut);assert 'door without road' in check['errors']
report['rejectedMutations'].append({'level':1,'case':'door_rotated_away','errors':check['errors']})
fixture={'gridCells':[{'x':x,'z':0} for x in (0,1,5,6)],'gridWorldHeight':0,
         'placedPieceCounts':{'Walkway_02_1':2},
         'startPoints':[{'componentId':1,'gridPosition':[0,0,-1],'pointNeedConnect':[]},
                        {'componentId':2,'gridPosition':[5,0,-1],'pointNeedConnect':[]}]}
placements=[{'name':'Walkway_02_1','anchor':[x,0],'rotation':0} for x in (0,5)]
assert verify(fixture,catalog,placements)['valid']
fixture['startPoints'][0]['pointNeedConnect']=[2]
assert 'required start connection missing' in verify(fixture,catalog,placements)['errors']
fixture['startPoints']=fixture['startPoints'][:1]
fixture['startPoints'][0]['pointNeedConnect']=[]
assert 'road piece disconnected from all starts' in verify(fixture,catalog,placements)['errors']
report['connectivityFixtures']={'separate_networks_with_own_starts':'accepted',
    'required_pair_disconnected':'rejected','road_network_without_start':'rejected'}
VALIDATION.write_text(json.dumps(report,indent=2),encoding='utf8')
print(f"Validated {len(report['solutions'])} solutions; matched {report['sourceFootprintsChecked']} source footprints; rejected {len(report['rejectedMutations'])} mutations.")
