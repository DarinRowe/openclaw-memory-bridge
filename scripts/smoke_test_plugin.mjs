#!/usr/bin/env node
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

function transpilePluginSource(source) {
  return source
    .replace(/function getPluginConfig\(api: any\): any \{/g, "function getPluginConfig(api) {")
    .replace(/function getGlobalConfig\(api: any\): any \{/g, "function getGlobalConfig(api) {")
    .replace(/function getWorkspace\(api: any\): string \{/g, "function getWorkspace(api) {")
    .replace(/function resolvePath\(workspace: string, file: string\): string \{/g, "function resolvePath(workspace, file) {")
    .replace(/function getPluginDir\(\): string \{/g, "function getPluginDir() {")
    .replace(/function getConfigBoolean\(cfg: any, key: string, defaultValue: boolean\): boolean \{/g, "function getConfigBoolean(cfg, key, defaultValue) {")
    .replace(/function getConfigNumber\(cfg: any, key: string, defaultValue: number\): number \{/g, "function getConfigNumber(cfg, key, defaultValue) {")
    .replace(/function readMarkdown\(path: string\): string \| null \{/g, "function readMarkdown(path) {")
    .replace(/function extractSections\(content: string\): Record<string, string\[]> \{/g, "function extractSections(content) {")
    .replace(/const sections: Record<string, string\[]> = \{\};/g, "const sections = {};")
    .replace(/let current: string \| null = null;/g, "let current = null;")
    .replace(/function trimToLimit\(text: string, maxChars: number\): string \{/g, "function trimToLimit(text, maxChars) {")
    .replace(/function getHighRiskLessons\(lessonsPath: string, maxLessons: number\): string\[] \{/g, "function getHighRiskLessons(lessonsPath, maxLessons) {")
    .replace(/function ensureDailyLog\(workspace: string\): string \{/g, "function ensureDailyLog(workspace) {")
    .replace(/function appendToDailyLog\(workspace: string, entry: string\): void \{/g, "function appendToDailyLog(workspace, entry) {")
    .replace(/function runJanitor\(workspace: string\): void \{/g, "function runJanitor(workspace) {")
    .replace(/export default function register\(api: any\) \{/g, "export default function register(api) {")
    .replace(/let janitorTimer: ReturnType<typeof setInterval> \| null = null;/g, "let janitorTimer = null;")
    .replace(/\(event: any, ctx: any\)/g, "(event, ctx)")
    .replace(/\(ctx: any\)/g, "(ctx)")
    .replace(/const results: Record<string, string> = \{\};/g, "const results = {};")
    .replace(/map\(\(l: string\) =>/g, "map((l) =>")
    .replace(/filter\(\(m: any\) =>/g, "filter((m) =>")
    .replace(/reduce\(\(count: number, message: any\) =>/g, "reduce((count, message) =>");
}

async function loadPluginModule() {
  const source = readFileSync(new URL("../index.ts", import.meta.url), "utf-8");
  const transpiled = transpilePluginSource(source);
  const encoded = Buffer.from(transpiled, "utf-8").toString("base64");
  return import(`data:text/javascript;base64,${encoded}`);
}

function createApi(config) {
  const listeners = new Map();
  const hooks = new Map();
  return {
    config,
    listeners,
    hooks,
    on(name, handler) {
      listeners.set(name, handler);
    },
    registerHook(name, handler, meta) {
      hooks.set(name, { handler, meta });
    },
  };
}

function run() {
  const workspace = mkdtempSync(join(tmpdir(), "openclaw-memory-bridge-smoke-"));
  mkdirSync(join(workspace, "memory"), { recursive: true });
  writeFileSync(
    join(workspace, "SESSION-STATE.md"),
    "# SESSION-STATE.md\n\n## Current Focus\n- " + "x".repeat(5000) + "\n\n## Next Step\n- verify\n\n## Blockers\n- none\n",
  );
  writeFileSync(
    join(workspace, "LESSONS.md"),
    [
      "# LESSONS.md",
      "",
      "- [2026-03-13][critical][ops] first",
      "- [2026-03-13][high][ops] second",
      "- [2026-03-13][high][ops] third",
    ].join("\n"),
  );

  const api = createApi({
    plugins: {
      entries: {
        "memory-bridge": {
          config: {
            workspace,
            maxSessionStateChars: 200,
            maxHighRiskLessons: 2,
            maxLessonChars: 80,
          },
        },
      },
    },
  });

  return loadPluginModule().then(({ default: register }) => {
    register(api);

    const beforePromptBuild = api.listeners.get("before_prompt_build");
    assert.ok(beforePromptBuild, "before_prompt_build listener should be registered");
    const injected = beforePromptBuild({}, {});
    assert.ok(injected.prependContext.includes("[truncated]"), "session state should be truncated");
    assert.ok(injected.appendSystemContext.includes("[truncated]"), "lessons block should be truncated");

    const newHook = api.hooks.get("command:new");
    assert.ok(newHook, "command:new hook should be registered");
    return Promise.resolve(newHook.handler({})).then((result) => {
      assert.equal(result, undefined, "command:new should not claim handled");
      const today = new Date().toISOString().split("T")[0];
      const dailyLog = join(workspace, "memory", `${today}.md`);
      assert.ok(readFileSync(dailyLog, "utf-8").includes("Last updated (UTC):"), "daily log should be created");

      const agentEnd = api.listeners.get("agent_end");
      assert.ok(agentEnd, "agent_end listener should be registered");
      agentEnd(
        {
          run: { status: "error", error: "boom" },
          messages: [
            { role: "assistant", tool_calls: [{ id: "1" }] },
            { role: "tool" },
            { role: "assistant", content: "done" },
          ],
        },
        {},
      );

      const logContent = readFileSync(dailyLog, "utf-8");
      assert.ok(logContent.includes("Ran 1 tool call(s)"), "agent_end should count earlier tool calls");
      assert.ok(logContent.includes("**Error**: boom"), "agent_end should log run errors");
      console.log("smoke test passed");
    });
  });
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
