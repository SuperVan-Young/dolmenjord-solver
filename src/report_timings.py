"""Generate per-level timing documentation and layout index from saved results."""
import json
import statistics
from project_paths import DOC, LAYOUTS, LEVELS, SOLUTIONS


def main():
    levels = {x['number']: x for x in json.loads(LEVELS.read_text(encoding='utf8'))['levels']}
    results = json.loads(SOLUTIONS.read_text(encoding='utf8'))['results']
    solved = [r for r in results if r['status'] == 'solved']
    times = [r['seconds'] for r in solved]
    lines = [
        '# 逐关求解耗时', '',
        '数据来源：[保存的解与搜索统计](../data/solutions/solutions.json)。生成文档时不重新计时。', '',
        '## 测量口径', '',
        '- `seconds` 是成功那次调用的墙钟耗时，包含候选/模型构建、搜索与调用内校验，不包含提取、绘图或外部独立验证。',
        '- 历史结果未保存完整 attempts 列表，含超时和失败尝试的累计耗时未知。表中时间与合计不能当作从零执行整套命令的总耗时。',
        '- 这是单次成功记录，未保存完整硬件和负载信息，不是重复基准测试。CP-SAT 使用 8 个 worker。',
        '- 历史结果未记录 strategy 的 DFS 关卡标为原顺序；47、58、59 关明确保存了边界优先策略。', '',
        '## 汇总与讨论', '',
        f'- 成功 {len(solved)}/{len(results)} 关；成功尝试耗时合计 {sum(times):.6f} 秒，中位数 {statistics.median(times):.6f} 秒。',
        '- 1–10 关均低于 0.01 秒，适合快速验证流程；11–37 关均低于 0.3 秒。',
        '- 38、41、46、48、49、51、55、57 关搜索开销较明显。格子数量不能单独预测耗时，候选顺序及房屋方案的道路可铺性也影响搜索树。',
        '- 50 关约 40.88 秒，54 关约 11.09 秒，是原顺序 DFS 的慢关。表中房屋/道路节点数可用于观察工作量，但它们不是分阶段计时。',
        '- 47、58、59 关采用边界优先，成功尝试分别约 0.016、9.29、17.37 秒；此前尝试不计入，不能据此计算策略加速比。',
        '- 60 关有 395 格、83 个物件、8 个独立区域，使用 CP-SAT 道路层级模型，成功尝试约 74.91 秒。CP 分支与 DFS 节点的计数口径不同。',
        '- 后续性能对比应固定机器、依赖、策略与并行数，多次重复，并保存每次尝试和端到端时间。', '',
        '## 每关记录', '',
        '“—”表示没有对应指标。关卡链接打开该关布局。', '',
        '| 关卡 | 格数 | 物件数 | 方法 | 成功尝试（秒） | 房屋节点 | 道路节点 | CP 分支 |',
        '| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |',
    ]
    index = ['# 每关布局', '', '[文档入口](../README.md) · [耗时分析](../timings.md)', '',
             '下载后打开 [交互总览](solutions.html)，可切换只看房屋并查看坐标。下面的 SVG 可在 GitHub 直接查看。', '',
             '暖色 H 为房屋，青色 R 为道路，小圆圈为门口，深色 S 为起点。', '']
    for r in solved:
        n = r['level']; level = levels[n]; stats = r['stats']; strategy = r.get('strategy')
        method = ('CP-SAT 道路层级' if isinstance(strategy, str) else
                  'DFS 边界优先' if strategy == 1 else
                  'DFS 原顺序（历史记录）' if strategy is None else f'DFS 策略 {strategy}')
        lines.append(f"| [{n:02}](layouts/level_images/level_{n:02}.svg) | {len(level['gridCells'])} | {len(r['placements'])} | {method} | {r['seconds']:.6f} | {stats.get('macroNodes', '—')} | {stats.get('roadNodes', '—')} | {stats.get('branches', '—')} |")
        index += [f'## 第 {n:02} 关', '', f"{method}，成功尝试 {r['seconds']:.6f} 秒。", '', f'![第 {n:02} 关布局](level_images/level_{n:02}.svg)', '']
    DOC.mkdir(parents=True, exist_ok=True)
    LAYOUTS.mkdir(parents=True, exist_ok=True)
    (DOC / 'timings.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    (LAYOUTS / 'README.md').write_text('\n'.join(index).rstrip() + '\n', encoding='utf8')
    print(f'Wrote timing report and layout index for {len(solved)} levels')


if __name__ == '__main__':
    main()
