# Move Prompt Manager from Node 1 to Node 2

## Goal
Migrate the prompt construction logic from Node 1 to Node 2 to centralize generation logic and make Node 1 a pure inference engine.

## Tasks
- [ ] 1. Identify Node 1 Prompt Code -> Verify: List files in `node1-inference/app/prompts`.
- [ ] 2. Create Node 2 Generation Module -> Verify: `node2-main/app/generation/` exists.
- [ ] 3. Port Prompt Files to Node 2 -> Verify: `node2-main/app/generation/prompts/` contains ported files.
- [ ] 4. Refactor Node 2 Service -> Verify: `app.services.generation` uses local prompts.
- [ ] 5. Update Node 1 API -> Verify: `node1-inference` accepts `prompt` string in `/generate`.
- [ ] 6. Delete Node 1 Prompts -> Verify: `node1-inference/app/prompts` is removed.

## Done When
- [ ] Node 2 constructs the full prompt.
- [ ] Node 1 receives the prompt and runs inference.
- [ ] Tests pass in Node 2 for prompt construction.
