import { mkdirSync, writeFileSync } from "node:fs";
import { Diagram } from "../drawio-ai-kit/src/builder.mjs";
import { renderTree } from "../drawio-ai-kit/src/layout-engine.mjs";
import {
  end,
  gateway,
  pool,
  serviceTask,
  start,
} from "../drawio-ai-kit/src/bpmn.mjs";

const d = new Diagram("bpmn");

const process = pool(
  "nightly",
  "Daily Manufacturing Data Economy pipeline",
  {
    lanes: [
      "Scheduler / API",
      "Data ingestion",
      "Data processing",
      "ML & persistence",
    ],
    phases: ["Trigger", "Ingest", "Transform", "Train & publish"],
    gap: 42,
  },
  [
    start("start", {
      lane: 0,
      col: 0,
      label: "02:00 schedule\nor manual trigger",
      type: "timer",
    }),
    serviceTask("create_job", {
      lane: 0,
      col: 1,
      label: "Create pipeline_jobs row",
    }),
    serviceTask("crawl", {
      lane: 1,
      col: 2,
      label: "Run GSO · OECD · company · marketplace crawlers",
    }),
    gateway("crawl_ok", {
      lane: 1,
      col: 3,
      label: "Crawl succeeded?",
    }),
    end("failed", {
      lane: 0,
      col: 4,
      label: "Mark job failed",
      type: "error",
    }),
    serviceTask("metrics", {
      lane: 2,
      col: 4,
      label: "Compute digital metrics",
    }),
    serviceTask("features", {
      lane: 2,
      col: 5,
      label: "Engineer lag · rolling · cross features",
    }),
    serviceTask("train", {
      lane: 3,
      col: 6,
      label: "Train ARIMA · XGBoost · LSTM",
    }),
    serviceTask("evaluate", {
      lane: 3,
      col: 7,
      label: "Evaluate MAE · RMSE · MAPE",
    }),
    serviceTask("persist", {
      lane: 3,
      col: 8,
      label: "Persist predictions and metrics",
    }),
    serviceTask("finish_job", {
      lane: 0,
      col: 9,
      label: "Mark job successful",
    }),
    end("complete", {
      lane: 0,
      col: 10,
      label: "Dashboard data ready",
    }),
  ],
);

renderTree(d, process, [40, 80]);
d.title("Nightly pipeline — BPMN swimlane");

d.link("start", "create_job", "", { flow: true, rounded: true });
d.link("create_job", "crawl", "dispatch", { flow: true, rounded: true });
d.link("crawl", "crawl_ok", "", { flow: true, rounded: true });
d.link("crawl_ok", "failed", "no", { rounded: true });
d.link("crawl_ok", "metrics", "yes", { flow: true, rounded: true });
d.link("metrics", "features", "", { flow: true, rounded: true });
d.link("features", "train", "", { flow: true, rounded: true });
d.link("train", "evaluate", "", { flow: true, rounded: true });
d.link("evaluate", "persist", "", { flow: true, rounded: true });
d.link("persist", "finish_job", "", { flow: true, rounded: true });
d.link("finish_job", "complete", "", { flow: true, rounded: true });

const result = d.validate();
console.log("bpmn:", JSON.stringify({
  ok: result.ok,
  errors: result.errors,
  warnings: result.warnings,
  advice: result.audit.advice,
}));

const outputDir = new URL("../output/", import.meta.url);
mkdirSync(outputDir, { recursive: true });
writeFileSync(
  new URL("03-nightly-pipeline-bpmn.drawio", outputDir),
  d.mxfile("Nightly pipeline BPMN"),
);
