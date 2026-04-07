## About Me [P0]
- [P0] Timezone: Asia/Hong_Kong (HKT, UTC+8)
- [P0] System operations timezone remains UTC (cron schedules unchanged)

## Operational Rules [P0]
- [P0] 读取顺序：memory/.abstract → MEMORY.md → SESSION-STATE.md；高风险操作先查 lessons。
- [P0] 查历史细节：优先读 insights（memory/insights/YYYY-MM.md），不够再读 daily logs（memory/YYYY-MM-DD.md）。
- [P0] 文件改动默认发你预览：凡我修改/生成任何文件，都会在对话里给你预览（至少列出文件路径+关键 diff/片段），除非你明确说不用。
- [P0] 决策顺序（稳定性优先）：(1) 若能在 **2 分钟内**低风险直接交付结果→先交付；(2) 否则→优先写 scripts/（可复用/可定时/可审计，尽量支持 dry-run）；(3) 仅当你明确要“自然语言复用/参数化”时再把脚本封装成 skill（skill=脚本外壳）；(4) **不做模型切换**。
- [P0] Daily log 采用「半自动」策略：当完成阶段性任务/发生文件改动/修复错误时，助手先给出 6-sections 草稿并询问；你回复“写”才追加到 `memory/YYYY-MM-DD.md`。
- [P0] Lessons 采用「半自动」策略：当出现报错/失败、高风险操作或稳定规律时，助手先给出候选 lesson 并询问；你回复“记”才写入 `memory/lessons/operational-lessons.jsonl`。
- [P0] “脑内记住”的内容不可信：除非已写入文件（MEMORY.md / SESSION-STATE.md / memory/日志 / lessons），否则一律当作可能的幻觉。

## Active Projects [P1]
- 
  