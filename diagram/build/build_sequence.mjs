import { mkdirSync, writeFileSync } from "node:fs";
import { Diagram } from "../drawio-ai-kit/src/builder.mjs";
import {
  box,
  frame,
  icon,
  phantom,
  renderTree,
} from "../drawio-ai-kit/src/layout-engine.mjs";

const d = new Diagram("sequence");

const tree = phantom(
  "root",
  "",
  { dir: "row", gap: 58, align: "center", header: 0, pad: 10 },
  [
    box("operator", "Analyst / Operator", {
      fill: "#DAE8FC",
      stroke: "#6C8EBF",
      bold: true,
    }),
    frame("frontend", "Frontend", { dir: "col", gap: 22 }, [
      box("pipeline_page", "React Pipeline page\nTrigger + job status"),
    ]),
    frame("api", "FastAPI", { dir: "col", gap: 22 }, [
      box("trigger_api", "POST /api/pipeline/trigger"),
      box("jobs_api", "GET /api/pipeline/jobs"),
    ]),
    frame("execution", "Background execution", { dir: "col", gap: 22 }, [
      box("background_task", "FastAPI BackgroundTasks"),
      box("run_crawler", "_run_crawler()\nselected stage or all"),
      box("pipeline_steps", "Crawlers → metrics → features → ML"),
    ]),
    frame("data", "State", { dir: "col", gap: 22 }, [
      icon("postgres", "postgres", "PostgreSQL 16"),
      icon("redis", "redis", "Redis 7"),
    ]),
  ],
);

renderTree(d, tree, [40, 80]);
d.title("Manual pipeline trigger — numbered request sequence");

d.link("operator", "pipeline_page", "1 · choose crawler");
d.link("pipeline_page", "trigger_api", "2 · POST trigger", { flow: true });
d.link("trigger_api", "postgres", "3 · create PipelineJob");
d.link("trigger_api", "background_task", "4 · enqueue task", { flow: true });
d.link("background_task", "run_crawler", "5 · execute");
d.link("run_crawler", "pipeline_steps", "6 · run selected stages", { flow: true });
d.link("pipeline_steps", "postgres", "7 · persist data + finish job");
d.link("pipeline_page", "jobs_api", "8 · poll jobs", { dash: true });
d.link("jobs_api", "postgres", "9 · query status");
d.link("jobs_api", "pipeline_page", "10 · render status", { dash: true });

const result = d.validate();
console.log("sequence:", JSON.stringify({
  ok: result.ok,
  errors: result.errors,
  warnings: result.warnings,
  advice: result.audit.advice,
}));

const outputDir = new URL("../output/", import.meta.url);
mkdirSync(outputDir, { recursive: true });
writeFileSync(
  new URL("02-manual-trigger-sequence.drawio", outputDir),
  d.mxfile("Manual pipeline trigger sequence"),
);
