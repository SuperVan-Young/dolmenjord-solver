# 逐关求解耗时

数据来源：[保存的解与搜索统计](../data/solutions/solutions.json)。生成文档时不重新计时。

## 测量口径

- `seconds` 是成功那次调用的墙钟耗时，包含候选/模型构建、搜索与调用内校验，不包含提取、绘图或外部独立验证。
- 历史结果未保存完整 attempts 列表，含超时和失败尝试的累计耗时未知。表中时间与合计不能当作从零执行整套命令的总耗时。
- 这是单次成功记录，未保存完整硬件和负载信息，不是重复基准测试。CP-SAT 使用 8 个 worker。
- 历史结果未记录 strategy 的 DFS 关卡标为原顺序；47、58、59 关明确保存了边界优先策略。

## 汇总与讨论

- 成功 60/60 关；成功尝试耗时合计 167.871476 秒，中位数 0.015636 秒。
- 1–10 关均低于 0.01 秒，适合快速验证流程；11–37 关均低于 0.3 秒。
- 38、41、46、48、49、51、55、57 关搜索开销较明显。格子数量不能单独预测耗时，候选顺序及房屋方案的道路可铺性也影响搜索树。
- 50 关约 40.88 秒，54 关约 11.09 秒，是原顺序 DFS 的慢关。表中房屋/道路节点数可用于观察工作量，但它们不是分阶段计时。
- 47、58、59 关采用边界优先，成功尝试分别约 0.016、9.29、17.37 秒；此前尝试不计入，不能据此计算策略加速比。
- 60 关有 395 格、83 个物件、8 个独立区域，使用 CP-SAT 道路层级模型，成功尝试约 74.91 秒。CP 分支与 DFS 节点的计数口径不同。
- 后续性能对比应固定机器、依赖、策略与并行数，多次重复，并保存每次尝试和端到端时间。

## 每关记录

“—”表示没有对应指标。关卡链接打开该关布局。

| 关卡 | 格数 | 物件数 | 方法 | 成功尝试（秒） | 房屋节点 | 道路节点 | CP 分支 |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| [01](layouts/level_images/level_01.svg) | 3 | 2 | DFS 原顺序（历史记录） | 0.000172 | 3 | 2 | — |
| [02](layouts/level_images/level_02.svg) | 4 | 3 | DFS 原顺序（历史记录） | 0.000134 | 3 | 2 | — |
| [03](layouts/level_images/level_03.svg) | 10 | 4 | DFS 原顺序（历史记录） | 0.000261 | 7 | 2 | — |
| [04](layouts/level_images/level_04.svg) | 18 | 6 | DFS 原顺序（历史记录） | 0.000811 | 10 | 3 | — |
| [05](layouts/level_images/level_05.svg) | 25 | 9 | DFS 原顺序（历史记录） | 0.001748 | 120 | 34 | — |
| [06](layouts/level_images/level_06.svg) | 19 | 5 | DFS 原顺序（历史记录） | 0.000743 | 15 | 9 | — |
| [07](layouts/level_images/level_07.svg) | 17 | 7 | DFS 原顺序（历史记录） | 0.001002 | 75 | 15 | — |
| [08](layouts/level_images/level_08.svg) | 28 | 10 | DFS 原顺序（历史记录） | 0.009156 | 1113 | 124 | — |
| [09](layouts/level_images/level_09.svg) | 32 | 10 | DFS 原顺序（历史记录） | 0.002042 | 9 | 12 | — |
| [10](layouts/level_images/level_10.svg) | 38 | 11 | DFS 原顺序（历史记录） | 0.003988 | 73 | 5 | — |
| [11](layouts/level_images/level_11.svg) | 34 | 9 | DFS 原顺序（历史记录） | 0.004188 | 78 | 6 | — |
| [12](layouts/level_images/level_12.svg) | 34 | 9 | DFS 原顺序（历史记录） | 0.004921 | 230 | 56 | — |
| [13](layouts/level_images/level_13.svg) | 34 | 9 | DFS 原顺序（历史记录） | 0.002379 | 18 | 5 | — |
| [14](layouts/level_images/level_14.svg) | 32 | 9 | DFS 原顺序（历史记录） | 0.009095 | 1499 | 39 | — |
| [15](layouts/level_images/level_15.svg) | 31 | 10 | DFS 原顺序（历史记录） | 0.002827 | 44 | 7 | — |
| [16](layouts/level_images/level_16.svg) | 33 | 10 | DFS 原顺序（历史记录） | 0.003549 | 138 | 6 | — |
| [17](layouts/level_images/level_17.svg) | 43 | 10 | DFS 原顺序（历史记录） | 0.005426 | 523 | 50 | — |
| [18](layouts/level_images/level_18.svg) | 64 | 17 | DFS 原顺序（历史记录） | 0.287764 | 25303 | 16 | — |
| [19](layouts/level_images/level_19.svg) | 50 | 10 | DFS 原顺序（历史记录） | 0.004137 | 18 | 8 | — |
| [20](layouts/level_images/level_20.svg) | 47 | 10 | DFS 原顺序（历史记录） | 0.004153 | 15 | 8 | — |
| [21](layouts/level_images/level_21.svg) | 55 | 12 | DFS 原顺序（历史记录） | 0.006480 | 66 | 9 | — |
| [22](layouts/level_images/level_22.svg) | 62 | 13 | DFS 原顺序（历史记录） | 0.008719 | 32 | 35 | — |
| [23](layouts/level_images/level_23.svg) | 75 | 16 | DFS 原顺序（历史记录） | 0.031808 | 138 | 409 | — |
| [24](layouts/level_images/level_24.svg) | 92 | 16 | DFS 原顺序（历史记录） | 0.021431 | 151 | 95 | — |
| [25](layouts/level_images/level_25.svg) | 55 | 12 | DFS 原顺序（历史记录） | 0.011203 | 175 | 70 | — |
| [26](layouts/level_images/level_26.svg) | 43 | 10 | DFS 原顺序（历史记录） | 0.003404 | 10 | 5 | — |
| [27](layouts/level_images/level_27.svg) | 63 | 12 | DFS 原顺序（历史记录） | 0.009270 | 36 | 35 | — |
| [28](layouts/level_images/level_28.svg) | 66 | 13 | DFS 原顺序（历史记录） | 0.010469 | 96 | 28 | — |
| [29](layouts/level_images/level_29.svg) | 85 | 15 | DFS 原顺序（历史记录） | 0.015310 | 44 | 63 | — |
| [30](layouts/level_images/level_30.svg) | 69 | 14 | DFS 原顺序（历史记录） | 0.023959 | 472 | 27 | — |
| [31](layouts/level_images/level_31.svg) | 70 | 14 | DFS 原顺序（历史记录） | 0.052933 | 1106 | 9 | — |
| [32](layouts/level_images/level_32.svg) | 70 | 15 | DFS 原顺序（历史记录） | 0.030032 | 904 | 81 | — |
| [33](layouts/level_images/level_33.svg) | 71 | 17 | DFS 原顺序（历史记录） | 0.017444 | 31 | 164 | — |
| [34](layouts/level_images/level_34.svg) | 93 | 16 | DFS 原顺序（历史记录） | 0.018479 | 20 | 10 | — |
| [35](layouts/level_images/level_35.svg) | 90 | 16 | DFS 原顺序（历史记录） | 0.019909 | 47 | 17 | — |
| [36](layouts/level_images/level_36.svg) | 72 | 16 | DFS 原顺序（历史记录） | 0.022866 | 777 | 22 | — |
| [37](layouts/level_images/level_37.svg) | 82 | 18 | DFS 原顺序（历史记录） | 0.013667 | 298 | 95 | — |
| [38](layouts/level_images/level_38.svg) | 64 | 17 | DFS 原顺序（历史记录） | 4.239824 | 261527 | 128 | — |
| [39](layouts/level_images/level_39.svg) | 84 | 17 | DFS 原顺序（历史记录） | 0.014214 | 185 | 9 | — |
| [40](layouts/level_images/level_40.svg) | 82 | 18 | DFS 原顺序（历史记录） | 0.033650 | 207 | 29 | — |
| [41](layouts/level_images/level_41.svg) | 93 | 19 | DFS 原顺序（历史记录） | 0.547888 | 28802 | 683 | — |
| [42](layouts/level_images/level_42.svg) | 92 | 19 | DFS 原顺序（历史记录） | 0.040126 | 671 | 70 | — |
| [43](layouts/level_images/level_43.svg) | 93 | 19 | DFS 原顺序（历史记录） | 0.055660 | 1752 | 597 | — |
| [44](layouts/level_images/level_44.svg) | 82 | 19 | DFS 原顺序（历史记录） | 0.012044 | 41 | 9 | — |
| [45](layouts/level_images/level_45.svg) | 77 | 19 | DFS 原顺序（历史记录） | 0.011181 | 54 | 17 | — |
| [46](layouts/level_images/level_46.svg) | 88 | 20 | DFS 原顺序（历史记录） | 0.779584 | 41227 | 4620 | — |
| [47](layouts/level_images/level_47.svg) | 78 | 22 | DFS 边界优先 | 0.015962 | 59 | 15 | — |
| [48](layouts/level_images/level_48.svg) | 103 | 23 | DFS 原顺序（历史记录） | 1.019751 | 29688 | 56 | — |
| [49](layouts/level_images/level_49.svg) | 111 | 25 | DFS 原顺序（历史记录） | 0.328567 | 10738 | 28 | — |
| [50](layouts/level_images/level_50.svg) | 110 | 26 | DFS 原顺序（历史记录） | 40.880739 | 1817058 | 5391 | — |
| [51](layouts/level_images/level_51.svg) | 128 | 28 | DFS 原顺序（历史记录） | 1.770856 | 65900 | 262 | — |
| [52](layouts/level_images/level_52.svg) | 161 | 28 | DFS 原顺序（历史记录） | 0.045950 | 94 | 71 | — |
| [53](layouts/level_images/level_53.svg) | 104 | 28 | DFS 原顺序（历史记录） | 0.309422 | 9971 | 127 | — |
| [54](layouts/level_images/level_54.svg) | 145 | 32 | DFS 原顺序（历史记录） | 11.091610 | 357018 | 1424 | — |
| [55](layouts/level_images/level_55.svg) | 160 | 32 | DFS 原顺序（历史记录） | 2.067561 | 47459 | 1942 | — |
| [56](layouts/level_images/level_56.svg) | 153 | 33 | DFS 原顺序（历史记录） | 0.228163 | 3950 | 75 | — |
| [57](layouts/level_images/level_57.svg) | 167 | 34 | DFS 原顺序（历史记录） | 2.146112 | 53076 | 702 | — |
| [58](layouts/level_images/level_58.svg) | 181 | 36 | DFS 边界优先 | 9.292990 | 247456 | 58830 | — |
| [59](layouts/level_images/level_59.svg) | 179 | 39 | DFS 边界优先 | 17.367848 | 358177 | 465 | — |
| [60](layouts/level_images/level_60.svg) | 395 | 83 | CP-SAT 道路层级 | 74.905895 | — | — | 2814582 |
