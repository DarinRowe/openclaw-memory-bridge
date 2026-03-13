/**
 * Memory Bridge Plugin
 * 
 * Bridges file-based memory into agent context:
 * - before_prompt_build: inject SESSION-STATE.md + high-risk lessons
 * - command:new: ensure daily log exists
 * - agent_end: append to daily log
 * - gateway_start: schedule daily janitor
 */
import { readFileSync, existsSync, appendFileSync, writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const SESSION_STATE = "SESSION-STATE.md";
const LESSONS = "LESSONS.md";
const MEMORY_DIR = "memory";
const DEFAULT_WORKSPACE = "~/.openclaw/workspace";
const DEFAULT_MAX_SESSION_STATE_CHARS = 4000;
const DEFAULT_MAX_LESSON_CHARS = 1200;
const DEFAULT_MAX_LESSON_COUNT = 5;

function getPluginConfig(api: any): any {
  const cfg = api?.config || {};
  const entryCfg = cfg?.plugins?.entries?.["memory-bridge"]?.config;
  return {
    ...cfg,
    ...entryCfg,
  };
}

function getGlobalConfig(api: any): any {
  return api?.globalConfig || api?.gatewayConfig || api?.config || {};
}

function getWorkspace(api: any): string {
  const pluginCfg = getPluginConfig(api);
  const globalCfg = getGlobalConfig(api);
  return pluginCfg?.workspace || globalCfg?.agents?.defaults?.workspace || process.env.OPENCLAW_WORKSPACE || DEFAULT_WORKSPACE;
}

function resolvePath(workspace: string, file: string): string {
  const home = process.env.HOME || process.env.USERPROFILE || "~";
  const ws = workspace.replace(/^~/, home);
  return join(ws, file);
}

function getPluginDir(): string {
  return dirname(fileURLToPath(import.meta.url));
}

function getConfigBoolean(cfg: any, key: string, defaultValue: boolean): boolean {
  return typeof cfg?.[key] === "boolean" ? cfg[key] : defaultValue;
}

function getConfigNumber(cfg: any, key: string, defaultValue: number): number {
  const value = Number(cfg?.[key]);
  return Number.isFinite(value) && value > 0 ? value : defaultValue;
}

function readMarkdown(path: string): string | null {
  try {
    if (existsSync(path)) {
      return readFileSync(path, "utf-8");
    }
  } catch (e) {
    // ignore
  }
  return null;
}

function extractSections(content: string): Record<string, string[]> {
  const sections: Record<string, string[]> = {};
  let current: string | null = null;
  
  for (const line of content.split("\n")) {
    const match = line.match(/^##\s+(.+)$/);
    if (match) {
      current = match[1].trim();
      sections[current] = [];
    } else if (current && line.trim()) {
      sections[current].push(line.trim());
    }
  }
  return sections;
}

function trimToLimit(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return text.slice(0, Math.max(0, maxChars - 14)).trimEnd() + "\n[truncated]";
}

function getHighRiskLessons(lessonsPath: string, maxLessons: number): string[] {
  const content = readMarkdown(lessonsPath);
  if (!content) return [];
  
  const lines = content.split("\n").filter(l => 
    l.match(/^\-\s+\[.*\]\[(critical|high)\]/i)
  );
  return lines.slice(0, maxLessons);
}

function ensureDailyLog(workspace: string): string {
  const date = new Date().toISOString().split("T")[0];
  const logPath = resolvePath(workspace, join(MEMORY_DIR, `${date}.md`));
  
  if (!existsSync(logPath)) {
    mkdirSync(dirname(logPath), { recursive: true });
    const now = new Date().toISOString().replace("Z", "+00:00");
    const template = `# Daily Log — ${date} (UTC)

Created (UTC): ${now}
Last updated (UTC): ${now}

## Session Intent
- None

## Files Modified
- None

## Decisions Made
- None

## Lessons Learned
- None

## Patterns
- None

## Open Items
- None
`;
    writeFileSync(logPath, template);
  }
  return logPath;
}

function appendToDailyLog(workspace: string, entry: string): void {
  const date = new Date().toISOString().split("T")[0];
  const logPath = resolvePath(workspace, join(MEMORY_DIR, `${date}.md`));
  ensureDailyLog(workspace);
  
  const timestamp = new Date().toISOString().replace("Z", "+00:00");
  const chunk = `\n### ${timestamp}\n${entry}\n`;
  appendFileSync(logPath, chunk);
  try {
    const content = readFileSync(logPath, "utf-8");
    const updated = content.replace(/^Last updated \(UTC\): .*$/m, `Last updated (UTC): ${timestamp}`);
    if (updated !== content) {
      writeFileSync(logPath, updated);
    }
  } catch (e) {
    console.error("[memory-bridge] failed to update daily log timestamp:", e);
  }
}

function runJanitor(workspace: string): void {
  const pluginDir = getPluginDir();
  const janitorPath = join(pluginDir, "scripts", "memory_janitor.py");
  
  if (!existsSync(janitorPath)) return;
  
  const result = spawnSync("python3", [janitorPath], {
    env: { ...process.env, OPENCLAW_WORKSPACE: workspace },
    timeout: 30000,
  });
  
  if (result.status !== 0) {
    console.error(`[memory-bridge] janitor failed: ${result.stderr?.toString()}`);
  }
}

export default function register(api: any) {
  const cfg = getPluginConfig(api);
  const workspace = getWorkspace(api);
  const maxSessionStateChars = getConfigNumber(cfg, "maxSessionStateChars", DEFAULT_MAX_SESSION_STATE_CHARS);
  const maxLessonChars = getConfigNumber(cfg, "maxLessonChars", DEFAULT_MAX_LESSON_CHARS);
  const maxLessons = getConfigNumber(cfg, "maxHighRiskLessons", DEFAULT_MAX_LESSON_COUNT);
  
  // --- Scheduled janitor (daily at 00:15 UTC) ---
  let janitorTimer: ReturnType<typeof setInterval> | null = null;
  let lastJanitorDate = "";
  
  function maybeRunJanitor() {
    const today = new Date().toISOString().split("T")[0];
    if (today === lastJanitorDate) return;
    
    const hour = new Date().getUTCHours();
    const minute = new Date().getUTCMinutes();
    
    // Run once per day after 00:15 UTC
    if (hour > 0 || (hour === 0 && minute >= 15)) {
      lastJanitorDate = today;
      try {
        runJanitor(workspace);
      } catch (e) {
        console.error("[memory-bridge] janitor error:", e);
      }
    }
  }
  
  // Check every 10 minutes
  janitorTimer = setInterval(maybeRunJanitor, 10 * 60 * 1000);
  
  // Also run on startup (if past 00:15)
  maybeRunJanitor();
  
  // --- Hook: before_prompt_build ---
  api.on("before_prompt_build", (event: any, ctx: any) => {
    const results: Record<string, string> = {};
    
    if (getConfigBoolean(cfg, "injectSessionState", true)) {
      const statePath = resolvePath(workspace, SESSION_STATE);
      const stateContent = readMarkdown(statePath);
      if (stateContent) {
        const sections = extractSections(stateContent);
        let summary = "\n## Current Session State\n";
        
        if (sections["Current Focus"]) {
          summary += "\n**Current Focus:**\n" + sections["Current Focus"].map((l: string) => "  " + l).join("\n");
        }
        if (sections["Next Step"]) {
          summary += "\n**Next Step:**\n" + sections["Next Step"].map((l: string) => "  " + l).join("\n");
        }
        if (sections["Blockers"]) {
          summary += "\n**Blockers:**\n" + sections["Blockers"].map((l: string) => "  " + l).join("\n");
        }
        
        results.prependContext = trimToLimit(summary, maxSessionStateChars);
      }
    }
    
    if (getConfigBoolean(cfg, "injectHighRiskLessons", true)) {
      const lessonsPath = resolvePath(workspace, LESSONS);
      const lessons = getHighRiskLessons(lessonsPath, maxLessons);
      if (lessons.length > 0) {
        const lessonBlock = "\n## High-Risk Operational Lessons\n" + 
          lessons.map((l: string) => "  " + l).join("\n");
        results.appendSystemContext = trimToLimit(lessonBlock, maxLessonChars);
      }
    }
    
    return Object.keys(results).length > 0 ? results : undefined;
  }, { priority: 50 });
  
  // --- Hook: command:new ---
  api.registerHook(
    "command:new",
    async (ctx: any) => {
      ensureDailyLog(workspace);
    },
    {
      name: "memory-bridge.command-new",
      description: "Ensure daily log exists on /new",
    },
  );
  
  // --- Hook: agent_end ---
  api.on("agent_end", (event: any, ctx: any) => {
    if (!getConfigBoolean(cfg, "autoDailyLog", true)) return;
    
    const run = event.run || {};
    const messages = event.messages || [];
    
    const toolCalls = messages
      .filter((m: any) => m.role === "assistant")
      .reduce((count: number, message: any) => count + ((message?.tool_calls || []).length), 0);
    const hadError = run.status === "error";
    
    let entry = "";
    if (toolCalls > 0) {
      entry += `\n- Ran ${toolCalls} tool call(s)`;
    }
    if (hadError) {
      entry += `\n- **Error**: ${run.error || "unknown"}`;
    }
    
    if (entry) {
      appendToDailyLog(workspace, entry.trim());
    }
  }, { priority: 50 });
}
