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

const SESSION_STATE = "SESSION-STATE.md";
const LESSONS = "LESSONS.md";
const MEMORY_DIR = "memory";

function getWorkspace(cfg: any): string {
  return cfg?.agents?.defaults?.workspace || "~/.openclaw/workspace";
}

function resolvePath(workspace: string, file: string): string {
  const home = process.env.HOME || process.env.USERPROFILE || "~";
  const ws = workspace.replace(/^~/, home);
  return join(ws, file);
}

function getPluginDir(): string {
  return dirname(new URL(import.meta.url).pathname);
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

function getHighRiskLessons(lessonsPath: string): string[] {
  const content = readMarkdown(lessonsPath);
  if (!content) return [];
  
  const lines = content.split("\n").filter(l => 
    l.match(/^\-\s+\[.*\]\[(critical|high)\]/i)
  );
  return lines.slice(0, 5); // Max 5 high-risk lessons
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
  const cfg = api.config || {};
  const workspace = getWorkspace(cfg);
  
  // --- Scheduled janitor (daily at 00:15 UTC) ---
  let janitorTimer: ReturnType<typeof setInterval> | null = null;
  let lastJanitorDate = "";
  
  function maybeRunJanitor() {
    const today = new Date().toISOString().split("T")[0];
    if (today === lastJanitorDate) return;
    
    const hour = new Date().getUTCHours();
    const minute = new Date().getUTCMinutes();
    
    // Run once per day after 00:15 UTC
    if (hour === 0 && minute >= 15) {
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
    
    if (cfg.injectSessionState !== false) {
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
        
        results.prependContext = summary;
      }
    }
    
    if (cfg.injectHighRiskLessons !== false) {
      const lessonsPath = resolvePath(workspace, LESSONS);
      const lessons = getHighRiskLessons(lessonsPath);
      if (lessons.length > 0) {
        const lessonBlock = "\n## High-Risk Operational Lessons\n" + 
          lessons.map((l: string) => "  " + l).join("\n");
        results.appendSystemContext = lessonBlock;
      }
    }
    
    return Object.keys(results).length > 0 ? results : undefined;
  }, { priority: 50 });
  
  // --- Hook: command:new ---
  api.registerHook(
    "command:new",
    async (ctx: any) => {
      ensureDailyLog(workspace);
      return { handled: true };
    },
    {
      name: "memory-bridge.command-new",
      description: "Ensure daily log exists on /new",
    },
  );
  
  // --- Hook: agent_end ---
  api.on("agent_end", (event: any, ctx: any) => {
    if (cfg.autoDailyLog === false) return;
    
    const run = event.run || {};
    const messages = event.messages || [];
    
    const lastAssistant = messages.filter((m: any) => m.role === "assistant").slice(-1)[0];
    const toolCalls = (lastAssistant?.tool_calls || []).length;
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
