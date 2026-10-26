# Dolmenjord solver

Dolmenjord 布局求解器：从本地游戏安装目录提取棋盘与物件，使用房屋摆放搜索和道路精确覆盖求解，再独立验证并生成 HTML / SVG 可视化。

已在本地完成全部 60 关的离线求解与校验。1–59 关使用两阶段搜索，第 60 关使用 OR-Tools CP-SAT 后备模型；尚未自动回放到游戏中。

## 安装与运行

使用 Python 3.11 或更高版本，在仓库目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r outputs/requirements_export.txt -r outputs/requirements_solver.txt
cd outputs
python export_dolmenjord_levels.py "F:\software\steam\steamapps\common\Dolmenjord" dolmenjord_levels.json
python solve_dolmenjord.py --levels 60 --timeout 180 --constraint-fallback --resume
python validate_solutions.py
python render_solutions.py
```

请将示例游戏路径替换为自己的安装目录。提取器针对 Unity 2021.3.24f1 的当前游戏资源布局；其他游戏版本可能需要调整。

先验证少量关卡时，可将 `--levels 60` 改成 `--levels 10`。超时关卡可再次运行并复用已有合法解；不同机器上的搜索耗时可能不同。

完成后打开 `outputs/solutions.html`。结构化结果写入 `outputs/solutions.json`，每关 SVG 位于 `outputs/level_images/`。

## 源码

| 文件 | 用途 |
| --- | --- |
| `outputs/export_dolmenjord_levels.py` | 提取关卡棋盘、形状、库存与连接规则 |
| `outputs/solve_dolmenjord.py` | 房屋 DFS、剪枝、道路精确覆盖 |
| `outputs/solve_constraint.py` | CP-SAT 后备求解器 |
| `outputs/validate_solutions.py` | 独立验证、几何交叉检查、错误注入检查 |
| `outputs/render_solutions.py` | 生成 HTML 与 SVG |

算法、坐标与规则详见 [求解器说明](outputs/README_solver.md)。求解过程不使用原始建筑摆放作为提示。

仓库包含源代码；游戏文件、提取的关卡数据、生成的解与图片由上述命令在本地生成。
