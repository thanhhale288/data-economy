import { mkdirSync, writeFileSync } from "node:fs";
import { Diagram } from "../drawio-ai-kit/src/builder.mjs";
import {
  band,
  box,
  endpoint,
  icon,
  phantom,
  renderTree,
  stage,
} from "../drawio-ai-kit/src/layout-engine.mjs";

const d = new Diagram("pipeline");

const sources = stage("sources", 0, "1 · Data Sources", [
  box("gso", "GSO\nIIP · Shipment · Inventory"),
  box("oecd", "OECD SDMX\nMEI IP · BCI · INDIGO"),
  box("companies", "10 listed companies\nMetadata · BCTC · websites"),
  box("marketplaces", "Marketplaces\nShopee · TikTok · Lazada"),
]);

const ingestion = stage("ingestion", 1, "2 · Ingestion", [
  box("gso_crawler", "GSO crawler\nSDMX / PX-Web"),
  box("oecd_crawler", "OECD SDMX client"),
  box("company_crawler", "Company crawler\nHTTP · PDF extraction"),
  box("marketplace_crawler", "Marketplace crawler\nShop matcher ≥ 0.65"),
]);

const processing = stage("processing", 2, "3 · Clean & Engineer", [
  box("cleaning", "Cleaning\nmissing values · IQR outliers"),
  box("metrics", "Digital metrics\nOnline revenue · Digital VA · VDEI"),
  box("features", "Feature engineering\nlags · rolling · digital · financial"),
]);

const modeling = stage("modeling", 3, "4 · Forecast & Evaluate", [
  box("arima", "ARIMA(1,1,1)\nStatistical baseline"),
  icon("xgboost", "xgboost", "XGBoost"),
  icon("lstm", "pytorch", "PyTorch LSTM"),
  box("evaluation", "MAE · RMSE · MAPE"),
]);

const serving = stage("serving", 4, "5 · Store & Serve", [
  icon("postgres", "postgres", "PostgreSQL 16"),
  box("fastapi", "FastAPI\n/api/*"),
  box("react", "React + Recharts\nDashboard · Companies · ML Lab"),
]);

const controls = band("controls", "Cross-cutting controls", [
  box("mapping", "VSIC 10–33 ↔ ISIC Section C"),
  box("provenance", "Source provenance\nNo invented fallback values"),
  box("jobs", "pipeline_jobs\nstatus · records · errors"),
]);

const platform = phantom("platform", "", { dir: "col", gap: 34, header: 0 }, [
  phantom(
    "main_flow",
    "",
    { dir: "row", gap: 46, align: "top", header: 0, pad: 8 },
    [sources, ingestion, processing, modeling, serving],
  ),
  controls,
]);

const tree = phantom(
  "root",
  "",
  { dir: "row", gap: 46, align: "center", header: 0, pad: 10 },
  [
    endpoint("trigger", "TRIGGERS\n\nDaily 02:00\nor manual API"),
    platform,
    endpoint("users", "CONSUMERS\n\nResearchers\nanalysts · dashboard"),
  ],
);

renderTree(d, tree, [40, 80]);
d.title("Manufacturing Data Economy — end-to-end data pipeline");

d.link("trigger", "gso", "start", { flow: true });
d.link("gso", "gso_crawler", "SDMX", { flow: true });
d.link("oecd", "oecd_crawler", "SDMX", { flow: true });
d.link("companies", "company_crawler", "crawl", { flow: true });
d.link("marketplaces", "marketplace_crawler", "scrape", { flow: true });
d.link("gso_crawler", "cleaning", "", { flow: true });
d.link("oecd_crawler", "cleaning", "");
d.link("company_crawler", "metrics", "");
d.link("marketplace_crawler", "metrics", "");
d.link("cleaning", "features", "", { flow: true });
d.link("metrics", "features", "");
d.link("features", "arima", "");
d.link("features", "xgboost", "");
d.link("features", "lstm", "");
d.link("arima", "evaluation", "");
d.link("xgboost", "evaluation", "");
d.link("lstm", "evaluation", "");
d.link("evaluation", "postgres", "predictions", { flow: true });
d.link("postgres", "fastapi", "SQLAlchemy", { flow: true });
d.link("fastapi", "react", "JSON", { flow: true });
d.link("react", "users", "insights", { flow: true });

const result = d.validate();
console.log("pipeline:", JSON.stringify({
  ok: result.ok,
  errors: result.errors,
  warnings: result.warnings,
  advice: result.audit.advice,
}));

const outputDir = new URL("../output/", import.meta.url);
mkdirSync(outputDir, { recursive: true });
writeFileSync(
  new URL("01-data-pipeline.drawio", outputDir),
  d.mxfile("End-to-end data pipeline"),
);
