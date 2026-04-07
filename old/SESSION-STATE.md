# SESSION-STATE.md

> 工作缓冲（防止长对话被压缩后丢失关键上下文）。
> 每次开始新任务先看这里；每次任务有阶段性变化就更新。

## 当前任务
- 记忆系统（文件 + 定时维护）已落地并跑通

## 状态
- 阶段：已完成（v1）
- 上次更新时间：2026-03-01

## 已落地内容（v1）
- 目录：MEMORY.md / SESSION-STATE.md / memory(L0/L1/L2) / lessons / archive / scripts
- TTL：P1=90天、P2=30天（由 `scripts/memory_janitor.py` 执行）
- Insights：每天从“昨天”日志规则抽取 6 sections 写入 `memory/insights/YYYY-MM.md`
- Abstract：`scripts/update_abstracts.py` 自动维护 3 个 .abstract
- Lessons：手动/半自动（你确认“记”后写入）

## 定时任务（UTC）
- 00:05 `memory-daily-log`：确保今日 `memory/YYYY-MM-DD.md` 存在
- 00:15 `memory-janitor`：TTL + insights + 更新 abstracts，并 Telegram 通知

## Next (可选增强)
- [ ] 让 janitor 支持 `--date YYYY-MM-DD`（补跑历史/首次初始化更方便）
- [ ] 自动生成 lessons/.abstract 的分类统计（目前仅列最近 N 条）
- [ ] 引入 LLM reflection（每周/月做一次真正 10:1 insights）

## Last updated
- 2026-03-04 12:36 UTC
