#!/usr/bin/env python3
"""诊断3：让盒体 4 边圆滑——fillet 各取边变体 + chamfer 正确签名"""
import gmsh

gmsh.initialize()
b = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
gmsh.model.occ.synchronize()

def try_fillet(edges, label):
    try:
        r = gmsh.model.occ.fillet([(3, b)], edges, [0.4])
        gmsh.model.occ.synchronize()
        print(label, "OK", [(d, t) for d, t in r])
        return True
    except Exception as e:
        print(label, "ERR", repr(e))
        return False

# 变体A：oriented=True 取边
fA = [(d, t) for d, t in gmsh.model.getBoundary([(3, b)], True, True, False) if d == 1]
try_fillet([t for d, t in fA], "fillet_oriented")

# 变体B：全部面边组合（不去重）
edgesB = []
for d, t in gmsh.model.getBoundary([(3, b)], False, False, False):
    if d == 2:
        for d2, t2 in gmsh.model.getBoundary([(d, t)], False, True, False):
            if d2 == 1:
                edgesB.append(t2)
try_fillet(edgesB, "fillet_allface")

# chamfer：双距离
try:
    faces = [(d, t) for d, t in gmsh.model.getBoundary([(3, b)], False, False, False) if d == 2]
    edgesC = []
    seen = set()
    for f in faces:
        for d2, t2 in gmsh.model.getBoundary([f], False, False, False):
            if d2 == 1 and t2 not in seen:
                seen.add(t2); edgesC.append(t2)
    r = gmsh.model.occ.chamfer([(3, b)], edgesC, [0.3, 0.3] * len(edgesC))
    gmsh.model.occ.synchronize()
    print("chamfer_dist OK", [(d, t) for d, t in r])
except Exception as e:
    print("chamfer_dist ERR", repr(e))
gmsh.finalize()
