# Rule: Intelligence Tiering (Hybrid Workflow)

This rule defines how the Antigravity Agent Manager (Strategic Mission Control) and Eigent (Execution Engine) collaborate in parallel.

## 🧠 Division of Labor

| Feature | Antigravity (Mission Control) | Eigent (Execution Engine) |
| --- | --- | --- |
| **Model** | Gemini 3 Pro (Native) | **Kimi K2.5** (via Eigent) |
| **Role** | Strategic Planning, UI/UX Review, Browser Tests | Deep Logic, Refactoring, Local Debugging |
| **Backend** | Cloud-based | Hybrid (NVIDIA + Local Ollama) |

## 🛠️ Orchestration Rules

1. **Strategic Consultation (Planning)**:
   - For all structural changes or complex architecture designs, Antigravity **MUST** use the `Eigent.hybrid_reasoning` tool to consult the "Architect" (routed to Kimi K2.5).
   
2. **Technical Execution (Implementation)**:
   - Use Eigent's specialized reasoning for deep code generation or performance optimization.
   - Use native Antigravity tools for project-wide file operations and UI-intensive tasks.

3. **Autonomous Debugging (Testing)**:
   - During the testing phase, call `Eigent.hybrid_reasoning` with `agent_type="debug"`. 
   - This will automatically trigger local **Ollama** models to handle rapid iteration and sanity checks without inflating API costs.

4. **Backgrounding**:
   - Technical refactors initiated via Eigent should run in parallel while Antigravity summarizes findings or updates the project plan.
