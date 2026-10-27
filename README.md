# Dolmenjord solver

从本地游戏安装目录提取棋盘，求解房屋与道路布局，独立验证并生成可视化。已完成全部 **60 关**的离线求解，尚未自动回放到游戏。

## 目录

```text
src/                   Python 源码与统一路径配置
requirements/          提取与求解依赖
data/levels/          导出的关卡、形状、库存与规则
data/solutions/       已验证解、摆放坐标与搜索统计
doc/algorithm.md      算法原理与验证方法
doc/timings.md        每关耗时与讨论
doc/layouts/          HTML 总览、60 张 SVG 与索引
doc/validation_report.json   独立校验报告
```

## 查看结果

- [文档入口](doc/README.md)
- [算法原理](doc/algorithm.md)
- [逐关耗时](doc/timings.md)
- [60 关布局索引](doc/layouts/README.md)：GitHub 可直接查看 SVG。
- 下载后用浏览器打开 `doc/layouts/solutions.html`，可以切换房屋视图、查看坐标与搜索统计。

## 运行

Python 3.11 或更高版本，在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/solver.txt
python src/solve_dolmenjord.py --levels 60 --timeout 180 --constraint-fallback --resume
python src/validate_solutions.py
python src/render_solutions.py
python src/report_timings.py
```

仓库已包含关卡输入和 60 关解。`--resume` 校验并复用已有解；去掉它会重新搜索。快速重新测试可使用独立输出，避免覆盖全部结果：

```powershell
python src/solve_dolmenjord.py --levels 10 --output work/smoke_solutions.json
```

默认数据和文档路径根据源码位置解析，不依赖当前工作目录。求解器可通过 `--input`、`--output` 覆盖默认路径；相对参数路径按当前工作目录解析。

## 重新提取

```powershell
python -m pip install -r requirements/export.txt
python src/export_dolmenjord_levels.py "F:\software\steam\steamapps\common\Dolmenjord"
```

替换为自己的安装目录，默认写入 `data/levels/dolmenjord_levels.json`；可传第二个位置参数指定输出。提取器针对 Unity 2021.3.24f1 的已检查资源布局，其他游戏版本可能需要调整。

源码、关卡快照、已验证解和文档均由 Git 管理。仓库不包含游戏可执行文件、DLL 或原始资源包。`work/`、虚拟环境和旧 `outputs/` 预览不提交。
