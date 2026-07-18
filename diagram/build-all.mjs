const diagrams = [
  "./build/build_pipeline.mjs",
  "./build/build_sequence.mjs",
  "./build/build_bpmn.mjs",
  "./build/build_network.mjs",
];

for (const diagram of diagrams) {
  await import(diagram);
}
