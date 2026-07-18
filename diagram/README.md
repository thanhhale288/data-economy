# Project diagrams

Four editable draw.io diagrams for the Manufacturing Data Economy Platform.

## Files

- `output/01-data-pipeline.drawio` — end-to-end data pipeline
- `output/02-manual-trigger-sequence.drawio` — manual pipeline trigger sequence
- `output/03-nightly-pipeline-bpmn.drawio` — scheduled pipeline BPMN/swimlane
- `output/04-docker-compose-network.drawio` — Docker Compose runtime network

The source generators are in `build/`. The cloned `drawio-ai-kit` engine is in
`drawio-ai-kit/`.

## Rebuild and validate

```bash
node diagram/build-all.mjs

for file in diagram/output/*.drawio; do
  node diagram/drawio-ai-kit/src/cli.mjs validate "$file"
done
```

Open the `.drawio` files in the draw.io desktop app or
[app.diagrams.net](https://app.diagrams.net/).
