"""Export static Dolmenjord level data from an unmodified Unity installation.

Install: pip install UnityPy TypeTreeGeneratorAPI
Run: python export_dolmenjord_levels.py "F:\\software\\steam\\steamapps\\common\\Dolmenjord" levels.json

The game generates grids at runtime from each Building.colliders transform.
This exporter reconstructs those positions from serialized transforms.
"""
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


def ptr_id(value):
    return value.get("m_PathID", 0)


def xyz(value):
    return {axis: round(float(getattr(value, axis)), 6) for axis in ("x", "y", "z")}


def xyzw(value):
    return {axis: round(float(getattr(value, axis)), 6) for axis in ("x", "y", "z", "w")}


def main(game_dir: Path, target: Path):
    data_dir = game_dir / "Dolmenjord_Data"
    env = UnityPy.load(*(str(data_dir / name) for name in (
        "globalgamemanagers.assets", "sharedassets1.assets", "level1")))
    generator = TypeTreeGenerator("2021.3.24f1")
    generator.load_local_dll_folder(str(data_dir / "Managed"))
    env.typetree_generator = generator
    files = {file.name: file for file in env.files.values() if hasattr(file, "objects")}
    shared = files["sharedassets1.assets"].objects
    scene = files["level1"].objects
    scripts = {obj.path_id: obj.read().m_ClassName
               for obj in files["globalgamemanagers.assets"].objects.values()
               if obj.type.name == "MonoScript"}

    def component_type(obj):
        if obj.type.name != "MonoBehaviour":
            return obj.type.name
        head = obj.parse_monobehaviour_head()
        return scripts.get(head.m_Script.path_id, "UnknownMonoBehaviour")

    def game_object(pid):
        return shared[pid].read()

    def transform_of(go):
        for component in go.m_Component:
            obj = shared[component.component.path_id]
            if obj.type.name == "Transform":
                return obj.read()
        raise ValueError(f"No Transform on {go.m_Name}")

    def object_summary(go_id):
        if not go_id:
            return None
        go = game_object(go_id)
        tr = transform_of(go)
        tid = next(x.component.path_id for x in go.m_Component if shared[x.component.path_id].type.name=='Transform')
        wp,wq,ws = world_transform(tid)
        return {
            "gameObjectId": go_id,
            "name": go.m_Name,
            "localPosition": xyz(tr.m_LocalPosition),
            "localRotation": xyzw(tr.m_LocalRotation),
            "localScale": xyz(tr.m_LocalScale),
            "worldPosition": dict(zip('xyz',wp)),
            "worldRotation": dict(zip('xyzw',wq)),
        }

    def quat_mul(a, b):
        ax, ay, az, aw = a
        bx, by, bz, bw = b
        return (aw*bx + ax*bw + ay*bz - az*by,
                aw*by - ax*bz + ay*bw + az*bx,
                aw*bz + ax*by - ay*bx + az*bw,
                aw*bw - ax*bx - ay*by - az*bz)

    def rotate(q, v):
        x, y, z, w = q
        vx, vy, vz = v
        uv = (y*vz-z*vy, z*vx-x*vz, x*vy-y*vx)
        uuv = (y*uv[2]-z*uv[1], z*uv[0]-x*uv[2], x*uv[1]-y*uv[0])
        return tuple(v[i] + 2*(w*uv[i]+uuv[i]) for i in range(3))

    @lru_cache(maxsize=None)
    def world_transform(transform_id):
        tr = shared[transform_id].read()
        p = tuple(float(getattr(tr.m_LocalPosition, a)) for a in 'xyz')
        q = tuple(float(getattr(tr.m_LocalRotation, a)) for a in 'xyzw')
        s = tuple(float(getattr(tr.m_LocalScale, a)) for a in 'xyz')
        parent_id = tr.m_Father.path_id
        if not parent_id:
            return p, q, s
        pp, pq, ps = world_transform(parent_id)
        shifted = rotate(pq, tuple(ps[i]*p[i] for i in range(3)))
        return (tuple(pp[i]+shifted[i] for i in range(3)),
                quat_mul(pq, q), tuple(ps[i]*s[i] for i in range(3)))

    def component_go(component_id):
        obj = shared[component_id]
        if obj.type.name == "GameObject":
            return component_id
        if obj.type.name == "Transform":
            return obj.read().m_GameObject.path_id
        return ptr_id(obj.read_typetree()["m_GameObject"])

    def descendant_building_ids(transform_id):
        found = []
        tr = shared[transform_id].read()
        go = game_object(tr.m_GameObject.path_id)
        if not go.m_IsActive:
            return found
        for component in go.m_Component:
            obj = shared[component.component.path_id]
            if component_type(obj) == "Building":
                found.append(obj.path_id)
        for child in tr.m_Children:
            found.extend(descendant_building_ids(child.path_id))
        return found

    manager = scene[357].read_typetree()
    catalog = [{"name": x["name"], "buildingId": ptr_id(x["building"]),
                "blueprintId": ptr_id(x["blueprint"])}
               for x in manager["buildingsData"]]
    def local_point(tid, root_id):
        p = (0.0, 0.0, 0.0)
        while tid != root_id:
            tr = shared[tid].read()
            q = tuple(getattr(tr.m_LocalRotation, a) for a in 'xyzw')
            p = rotate(q, tuple(p[i]*getattr(tr.m_LocalScale, a) for i,a in enumerate('xyz')))
            p = tuple(p[i]+getattr(tr.m_LocalPosition,a) for i,a in enumerate('xyz'))
            tid = tr.m_Father.path_id
            if not tid:
                raise ValueError('Point not under building root')
        return p
    for item in catalog:
        b = shared[item['buildingId']].read_typetree()
        go = game_object(ptr_id(b['m_GameObject']))
        tid = next(x.component.path_id for x in go.m_Component if shared[x.component.path_id].type.name=='Transform')
        item['type'] = b['type']
        for field, dest in [('colliders','cells'),('fronts','fronts')]:
            points = [local_point(ptr_id(ref),tid) for ref in b[field]]
            if any(abs(p[i]-round(p[i]))>0.01 for p in points for i in (0,2)):
                raise ValueError(f'Non-grid shape {item["name"]}: {points}')
            item[dest] = [[round(p[0]),round(p[2])] for p in points]
    levels = []
    for number, ref in enumerate(manager["levels"], start=1):
        manager_id = ptr_id(ref)
        level = shared[manager_id].read_typetree()
        root_go = game_object(ptr_id(level["m_GameObject"]))
        root_transform = transform_of(root_go)
        grid_spacing = None
        for component in root_go.m_Component:
            obj = shared[component.component.path_id]
            if component_type(obj) == "customGrid":
                grid_spacing = obj.read_typetree()["size"]
        grid = None
        grid_transform_id = None
        for child in root_transform.m_Children:
            child_transform = shared[child.path_id].read()
            child_go = game_object(child_transform.m_GameObject.path_id)
            if child_go.m_Name == "Grid" or child_go.m_Name.startswith("Grid ("):
                grid = child_transform
                grid_transform_id = child.path_id
                break
        if grid is None:
            names = [game_object(shared[x.path_id].read().m_GameObject.path_id).m_Name
                     for x in root_transform.m_Children]
            raise ValueError(f"Grid node missing in {root_go.m_Name}; children={names}")
        pieces = []
        grid_entries = []
        start_points = []
        other_grid_objects = []
        for child in grid.m_Children:
            transform = shared[child.path_id].read()
            go_id = transform.m_GameObject.path_id
            go = game_object(go_id)
            if not go.m_IsActive:
                continue
            summary = object_summary(go_id)
            for component in go.m_Component:
                obj = shared[component.component.path_id]
                kind = component_type(obj)
                if kind == "Building":
                    value = obj.read_typetree()
                    pieces.append({**summary, "componentId": obj.path_id,
                                   "nameId": value["nameID"], "type": value["type"]})
                    for collider in value["colliders"]:
                        collider_id = ptr_id(collider)
                        position = world_transform(collider_id)[0]
                        grid_entries.append({
                            "x": round(position[0]),
                            "z": round(position[2]),
                            "sourceWorldPosition": {"x": round(position[0], 6),
                                                    "y": round(position[1], 6),
                                                    "z": round(position[2], 6)},
                            "sourceBuildingId": obj.path_id,
                            "sourceType": value["type"],
                            "sourceColliderTransformId": collider_id,
                        })
                elif kind == "PointStart":
                    value = obj.read_typetree()
                    start_points.append({**summary, "componentId": obj.path_id,
                                         "gridPosition": [round(v) for v in world_transform(child.path_id)[0]],
                                         "pointNeedConnect": [ptr_id(x) for x in value["pointNeedConnect"]]})
            if not any(x["gameObjectId"] == go_id for x in pieces + start_points):
                other_grid_objects.append(summary)
        final_effect_id = component_go(ptr_id(level["finalToten"])) if ptr_id(level["finalToten"]) else 0
        root_transform_id = next(x.component.path_id for x in root_go.m_Component
                                 if shared[x.component.path_id].type.name == "Transform")
        all_buildings = set(descendant_building_ids(root_transform_id))
        exported_buildings = {x["componentId"] for x in pieces}
        if all_buildings != exported_buildings:
            raise ValueError(f"Unexported buildings in {root_go.m_Name}: {all_buildings-exported_buildings}")
        grid_world_height = world_transform(grid_transform_id)[0][1]
        grid_cells = sorted({(x["x"], x["z"]) for x in grid_entries})
        levels.append({
            "number": number,
            "name": root_go.m_Name,
            "levelManagerId": manager_id,
            "levelType": level["type"],
            "gridSpacing": grid_spacing,
            "gridNode": object_summary(grid.m_GameObject.path_id),
            "gridWorldHeight": round(grid_world_height, 6),
            "serializedGridsCount": len(level["grids"]),
            "generatedGridEntries": grid_entries,
            "gridCells": [{"x": x, "z": z} for x, z in grid_cells],
            "finalEffect": object_summary(final_effect_id),
            "startPoints": start_points,
            "placedPieces": pieces,
            "placedPieceCounts": dict(Counter(x["nameId"] for x in pieces)),
            "otherGridObjects": other_grid_objects,
        })
    result = {"game": "Dolmenjord", "unityVersion": "2021.3.24f1",
              "source": "GameManager.levels order and sharedassets1.assets",
              "note": "Grid cells reconstructed from Building.colliders world positions, rounded like InitCreateGrid. Serialized LevelManager.grids is empty.",
              "catalog": catalog, "levels": levels}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(levels)} levels to {target}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python export_dolmenjord_levels.py GAME_DIR OUTPUT_JSON")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
