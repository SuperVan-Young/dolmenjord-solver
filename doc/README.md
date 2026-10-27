# 文档

- [算法原理](algorithm.md)：规则、房屋 DFS、道路精确覆盖、CP-SAT 和验证。
- [逐关耗时](timings.md)：60 关成功尝试耗时、搜索规模、慢关讨论和测量限制。
- [布局索引](layouts/README.md)：每关独立 SVG。
- [交互总览](layouts/solutions.html)：下载后在浏览器打开，可查看摆放坐标。
- [验证报告](validation_report.json)：关卡校验、资源几何交叉检查和错误注入检查。

从仓库根目录运行 `python src/report_timings.py` 更新耗时文档与布局索引；`python src/render_solutions.py` 更新 HTML/SVG；`python src/validate_solutions.py` 更新验证报告。它们读取保存的数据，不会重新求解。
