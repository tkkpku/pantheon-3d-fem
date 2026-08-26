#!/usr/bin/env python3
"""万神殿 3D FEM · 环境验证脚本（源自学习材料文档0）"""

import sys


def check(name, extra=None):
    try:
        mod = __import__(name)
        ver = getattr(mod, "__version__", "未知")
        print(f"  ✅ {name:12s} v{ver}")
        if extra:
            extra(mod)
        return True
    except ImportError as e:
        print(f"  ❌ {name:12s} 导入失败: {e}")
        return False


def main():
    print("=" * 56)
    print("  万神殿 3D FEM · 环境验证")
    print(f"  Python {sys.version.split()[0]}")
    print("=" * 56)
    results = []

    print("\n📐 数值计算")
    results.append(check("numpy"))
    results.append(check("scipy"))

    print("\n📊 绘图")
    results.append(check("matplotlib"))

    print("\n🔷 网格与前处理")
    results.append(check("gmsh"))
    results.append(check("meshio"))

    print("\n🔺 有限元求解 (FEniCSx)")
    results.append(check("dolfinx"))
    results.append(check("ufl"))
    results.append(check("basix"))
    results.append(check("mpi4py"))

    print("\n🎨 三维可视化")
    results.append(check("pyvista"))

    print("\n" + "=" * 56)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"  🎉 全部通过！{passed}/{total} 工具就绪，可以开始阶段一。")
    else:
        print(f"  ⚠️ {passed}/{total} 通过，{total - passed} 个失败，请排错后重跑。")
    print("=" * 56)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
