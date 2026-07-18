import { mkdirSync, writeFileSync } from "node:fs";
import { Diagram } from "../drawio-ai-kit/src/builder.mjs";
import {
  box,
  endpoint,
  frame,
  icon,
  phantom,
  renderTree,
} from "../drawio-ai-kit/src/layout-engine.mjs";

const d = new Diagram("network");

const external = frame(
  "external",
  "External actors & data providers",
  { dir: "col", gap: 28, fill: "#FFFFFF", stroke: "#5A6B7B" },
  [
    endpoint("browser", "Browser\nAnalyst / researcher"),
    endpoint("providers", "Data providers\nGSO · OECD · company sites · marketplaces"),
  ],
);

const webTier = frame(
  "web_tier",
  "Web tier",
  { dir: "col", gap: 26, fill: "#FFFFFF", stroke: "#6C8EBF" },
  [
    box("frontend", "frontend\nReact + Vite + Recharts\n:5173"),
    box("backend", "backend\nFastAPI + SQLAlchemy\n:8000"),
  ],
);

const workerTier = frame(
  "worker_tier",
  "Worker tier",
  { dir: "col", gap: 26, fill: "#FFFFFF", stroke: "#D79B00" },
  [
    box("scheduler", "worker\nschedule loop · daily 02:00"),
    box("jobs", "Crawlers · cleaning · features · ML"),
  ],
);

const dataTier = frame(
  "data_tier",
  "Data services",
  { dir: "col", gap: 26, fill: "#FFFFFF", stroke: "#9673A6" },
  [
    icon("postgres", "postgres", "PostgreSQL 16\n:5432"),
    icon("redis", "redis", "Redis 7\n:6379"),
    box("volume", "postgres_data\npersistent volume"),
  ],
);

const compose = frame(
  "compose",
  "Docker Compose network",
  { dir: "col", gap: 32, fill: "#F8FAFC", stroke: "#2496ED" },
  [
    phantom(
      "compose_header",
      "",
      { dir: "row", gap: 18, header: 0, pad: 0 },
      [
        icon("docker", "docker", "Docker Compose"),
        box("source_mounts", "Bind mounts\nbackend · crawlers · pipeline · ml · data"),
      ],
    ),
    phantom(
      "tiers",
      "",
      { dir: "row", gap: 46, align: "top", header: 0, pad: 0 },
      [webTier, workerTier, dataTier],
    ),
  ],
);

const tree = phantom(
  "root",
  "",
  { dir: "row", gap: 60, align: "center", header: 0, pad: 10 },
  [external, compose],
);

renderTree(d, tree, [40, 80]);
d.title("Manufacturing Data Economy — Docker Compose network");

d.link("browser", "frontend", "HTTP :5173", { flow: true });
d.link("frontend", "backend", "/api/* :8000", { flow: true });
d.link("providers", "jobs", "HTTPS / SDMX / scrape", { flow: true });
d.link("scheduler", "jobs", "run_all_pipelines()", { flow: true });
d.link("backend", "postgres", "SQL :5432");
d.link("backend", "redis", "redis://:6379", { dash: true });
d.link("jobs", "postgres", "read / write");
d.link("jobs", "redis", "coordination", { dash: true });
d.link("postgres", "volume", "persist");

const result = d.validate();
console.log("network:", JSON.stringify({
  ok: result.ok,
  errors: result.errors,
  warnings: result.warnings,
  advice: result.audit.advice,
}));

const outputDir = new URL("../output/", import.meta.url);
mkdirSync(outputDir, { recursive: true });
writeFileSync(
  new URL("04-docker-compose-network.drawio", outputDir),
  d.mxfile("Docker Compose network"),
);
