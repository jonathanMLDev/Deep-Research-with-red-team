# Deep Research

Multi-agent research system that runs a **supervisor + research agents**, optional **red-team evaluation**, and post-processing to produce **main**, **cleaned**, **fixed**, and **summary** reports (with usage and pricing in the main report).

## Features

- **Multi-agent research** — Supervisor coordinates research; web search via Tavily
- **Red team evaluation** — Objectivity / bias / source-quality checks when enabled in the workflow
- **Iterative refinement** — Feedback loop to improve the draft report
- **Initial report enrichment** — Start from an existing draft and deepen it
- **Outputs** — Timestamped main report plus `_cleaned.md`, `_fixed.md`, `_summary.md`, and a `.log`
- **Usage & cost** — Token and Tavily usage tracked; pricing section in the main report
- **CLI** — Root script for arbitrary queries or query files

## Requirements

- **Python** 3.11+
- **API keys** (checked at run time): `OPENAI_API_KEY`, `TAVILY_API_KEY`

## Installation

```bash
git clone <repository-url>
cd Deep_Research

# Recommended: install the package (editable) — required for imports
pip install -e .

# Optional: sync deps from lock-style list
pip install -r requirements.txt
```

**Windows:** you can use `install_dependencies.ps1` if you keep a similar setup there.

### Environment

```bash
cp env.example .env
# Edit .env — set at least OPENAI_API_KEY and TAVILY_API_KEY
```

**Optional** (see `env.example` and `src/deep_research/model_config.py`):

| Variable | Purpose |
|----------|---------|
| `USE_OPENROUTER` | `true` to use OpenRouter instead of direct OpenAI |
| `OPENROUTER_API_KEY` | OpenRouter key |
| `OPENROUTER_DEFAULT_MODEL`, `OPENROUTER_LIGHT_MODEL` | Model IDs on OpenRouter |
| `OPENAI_MODEL` | Default OpenAI model (e.g. `gpt-5`, `gpt-4o`) |
| `MAX_TAVILY_SEARCHES` | Cap on Tavily searches per researcher (default `20`) |
| `EVALUATOR_MODEL` | Model label used in pricing paths for the evaluator |

Verify the installed package from the repo root:

```bash
python -c "import deep_research; print('OK')"
```

## Usage

### General CLI (`run_deep_research.py` or `deep-research`)

From the **repository root**, after `pip install -e .`:

```bash
python run_deep_research.py --query "Your research question or brief..."
python run_deep_research.py -q "Short question" -o ./reports/my_run --report-prefix my_topic

# Or use the installed console script:
deep-research --query "Your research question or brief..."

# Query from a file (UTF-8)
python run_deep_research.py --query-file ./prompts/research_brief.md -o ./out

# Optional
python run_deep_research.py -f query.txt --task-name my_job --thread-id my_job --recursion-limit 15
python run_deep_research.py -f query.txt --initial-report-file draft.md --preface-file notes.txt
```

**Flags:** `-q` / `--query`, `-f` / `--query-file`, `-o` / `--output-path` (default `reports/deep_research`), `--report-prefix`, `--task-name`, `--report-title`, `--thread-id`, `--recursion-limit`, `--initial-report-file`, `--preface-file`.

On success, the script prints:

`<main_report_path> - <cleaned_report_path>`  
and a `[summary] ...` line when a summary file is written.

### Predefined tasks (`tasks/`)

Run from repo root (same editable install):

```bash
python -m tasks.investigate_beast2_ci
python -m tasks.investigate_boost_spike
python -m tasks.investigate_cursor_plans
python -m tasks.investigate_mit
python -m tasks.investigate_ragaas
python -m tasks.Investigate_competitors
python -m tasks.collect_cpp_compiler_error_data
```

Each task sets its own query, `output_path`, and `report_prefix` via `execute_main_process`.

### Programmatic use

```python
from deep_research.main_process import execute_main_process

report_path, summary_path = execute_main_process(
    "Your research question here",
    output_path="report_output",
    report_prefix="my_study",
    task_name="custom_task",
    report_title="My Report",
    thread_id="custom_task",
    recursion_limit=15,
)

# Optional: enrich an existing draft
execute_main_process(
    query,
    initial_report=open("draft.md", encoding="utf-8").read(),
    output_path="report_output",
    report_prefix="enriched",
    task_name="enrichment",
)
```

Async API: `run_main_process` in `deep_research.main_process` (same parameters as `execute_main_process`).

## Project layout

```text
Deep_Research/
├── run_deep_research.py      # CLI: arbitrary query / query file (`deep-research` after install)
├── pyproject.toml            # Package metadata & dependencies (deep-research)
├── requirements.txt          # Mirror of main dependencies
├── env.example               # Environment template
├── install_dependencies.ps1  # Optional Windows helper
├── src/
│   └── deep_research/        # Python package `deep_research`
│       ├── main_process.py   # run_main_process / execute_main_process
│       ├── research_agent_full.py
│       ├── research_agent.py
│       ├── multi_agent_supervisor.py
│       ├── red_team_evaluator.py
│       ├── report_productor.py   # cleaned / fixed / summary reports
│       ├── usage_tracker.py
│       ├── pricing_calculator.py
│       ├── model_config.py
│       └── ...
├── tasks/                    # Example / focused research scripts
├── data/                     # Optional inputs for some tasks
├── rules/                    # Project rules / prompts (if used)
└── reports/                  # Typical output root for the CLI
```

Generated artifacts per run (under your `output_path`):  
`*_<timestamp>.md` (main), `*_cleaned.md`, `*_fixed.md`, `*_summary.md`, `*.log`.

## How it works (high level)

1. **Research** — Agents search and synthesize; supervisor merges into a draft.
2. **Evaluation** — Red-team style scoring when the graph produces it.
3. **Refinement** — Iterations to improve quality.
4. **Export** — Main report with usage/pricing; cleaned and recreated variants; short summary.

## License

See [LICENSE](LICENSE).
