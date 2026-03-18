# Research Agent Workflow Documentation

## Overview

The research agent system is a multi-stage pipeline that orchestrates research tasks from initial user input through final report generation. The system uses LangGraph to manage state and coordinate multiple specialized agents.

## Complete Workflow

```
START
  ↓
[1] clarify_with_user (research_agent_scope.py)
  ↓
[2] write_research_brief (research_agent_scope.py)
  ↓
[3] write_draft_report (research_agent_scope.py)
  ↓
[4] supervisor_subgraph (multi_agent_supervisor.py)
  │   ├─ supervisor (decision making)
  │   └─ supervisor_tools (execution)
  │       ├─ think_tool (reflection)
  │       ├─ ConductResearch → researcher_agent (parallel research)
  │       └─ refine_draft_report (report improvement)
  │
  ↓ (loops until ResearchComplete or max_iterations)
[5] main_report_generation (research_agent_full.py)
  ↓
[6] finalize_report (research_agent_full.py)
  │   ├─ Red Team Evaluation
  │   ├─ URL Validation
  │   └─ Report Finalization
  ↓
END
```

## Detailed Stage Breakdown

### Stage 1: User Clarification (`clarify_with_user`)
**File:** `src/research_agent_scope.py`

- **Purpose:** Determines if user request has sufficient information
- **Action:** Routes to research brief generation
- **Output:** Command to proceed to `write_research_brief`

### Stage 2: Research Brief Generation (`write_research_brief`)
**File:** `src/research_agent_scope.py`

- **Purpose:** Transforms user conversation into structured research question
- **Uses:** Structured output model (`ResearchQuestion`)
- **Output:** Detailed research brief with scope and requirements

### Stage 3: Draft Report Generation (`write_draft_report`)
**File:** `src/research_agent_scope.py`

- **Purpose:** Creates initial draft report structure
- **Uses:** Structured output model (`DraftReport`)
- **Output:** Draft report outline

### Stage 4: Multi-Agent Supervisor (`supervisor_subgraph`)
**File:** `src/multi_agent_supervisor.py`

This is the core research execution stage with two main nodes:

#### 4a. Supervisor Node (`supervisor`)
- **Purpose:** Analyzes research brief and decides next actions
- **Decisions:**
  - What research topics need investigation
  - Whether to conduct parallel research
  - When research is complete
- **Tools Available:**
  - `ConductResearch`: Delegate to researcher agents
  - `ResearchComplete`: Signal completion
  - `think_tool`: Reflection and planning
  - `refine_draft_report`: Improve draft report

#### 4b. Supervisor Tools Node (`supervisor_tools`)
- **Purpose:** Executes supervisor's tool calls
- **Actions:**
  - Executes `think_tool` calls synchronously
  - Executes `ConductResearch` calls **in parallel** (up to `max_concurrent_researchers`)
  - Executes `refine_draft_report` calls
- **Loop Control:**
  - Continues until `ResearchComplete` is called
  - Or until `max_researcher_iterations` (15) is reached
  - Or if no tool calls are made

#### 4c. Researcher Agent (`researcher_agent`)
**File:** `src/research_agent.py`

Each `ConductResearch` call spawns a researcher agent that:

1. **LLM Call Node** (`llm_call`):
   - Analyzes research topic
   - Decides to search or provide answer
   - Can call `tavily_search` or `think_tool`

2. **Tool Node** (`tool_node`):
   - Executes `tavily_search` (web search via Tavily API)
   - Executes `think_tool` (reflection)
   - Tracks `tavily_search_count` in state (currently not enforced)

3. **Compress Research Node** (`compress_research`):
   - Synthesizes all research findings
   - Creates compressed summary for supervisor
   - Returns both compressed research and raw notes

**Loop:** `llm_call` → `tool_node` → `llm_call` → ... → `compress_research`

### Stage 5: Main Report Generation (`main_report_generation`)
**File:** `src/research_agent_full.py`

- **Purpose:** Generates final report from all research findings
- **Handles:**
  - Initial report generation (new research)
  - Report enrichment (if initial report provided)
- **Output:** Main report content

### Stage 6: Finalization (`finalize_report`)
**File:** `src/research_agent_full.py`

- **Purpose:** Validates and finalizes the report
- **Steps:**
  1. Red Team Evaluation (bias, source quality, claims)
  2. URL Validation (removes invalid URLs)
  3. Report Fixing (removes content referencing invalid URLs)
  4. Report Recreation (applies recommendations)
- **Output:** Final report, recreated report, red team evaluation

## Tavily Search Integration

### How Tavily is Used

1. **Tool Definition:** `tavily_search` tool in `src/utils.py`
2. **Called By:** Researcher agents during `tool_node` execution
3. **Search Function:** `tavily_search_multiple()` in `src/utils.py`
4. **Tracking:** `tavily_search_count` in `ResearcherState` (tracked and enforced)

### Search Limit Configuration

**✅ IMPLEMENTED:** The Tavily search limit is now **enforced in code**!

1. **Code Enforcement:**
   - Location: `src/research_agent.py`, `tool_node()` function
   - Limit: **10 Tavily searches** (default, configurable via environment variable)
   - Enforcement: Searches beyond the limit are skipped with a warning message
   - Status: ✅ **Fully implemented**

2. **Configuration:**
   - Environment Variable: `MAX_TAVILY_SEARCHES` (default: 10)
   - Location: `src/research_agent.py`, line 29
   - Can be set in `.env` file: `MAX_TAVILY_SEARCHES=10`

3. **Prompt Integration:**
   - Location: `src/prompts.py`, `research_agent_prompt`
   - Uses `{max_searches}` placeholder that matches code limit
   - Updated to use configurable limit instead of hardcoded "10"

4. **State Tracking:**
   - Location: `src/state_research.py`, line 31
   - Field: `tavily_search_count: int`
   - Status: Tracked and used for limit enforcement

5. **Results Per Search:**
   - Location: `src/utils.py`, line 57
   - Parameter: `max_results: int = 3` (default 3 results per search)
   - This controls **results per query**, not total searches

## How to Control Tavily Search Count Limit

### ✅ Implementation Complete

The Tavily search limit is now **fully implemented** with code enforcement. Here's how to configure it:

### Method 1: Environment Variable (Recommended)

1. **Set in `.env` file:**
```bash
MAX_TAVILY_SEARCHES=10
```

2. **Default value:** If not set, defaults to 10 searches per researcher agent

3. **How it works:**
   - The limit is read at module load time in `src/research_agent.py`
   - Each researcher agent has its own independent limit
   - When limit is reached, subsequent `tavily_search` calls are skipped
   - A warning message is returned to the agent explaining the limit was reached

### Method 2: Change Default in Code

Edit `src/research_agent.py`, line 29:
```python
MAX_TAVILY_SEARCHES = int(os.getenv("MAX_TAVILY_SEARCHES", "10"))  # Change "10" to desired default
```

### How Enforcement Works

1. **Before each search:** `tool_node()` checks if `tavily_search_count >= MAX_TAVILY_SEARCHES`
2. **If limit reached:**
   - Search is skipped (not executed)
   - Warning message is returned to the agent
   - Counter is NOT incremented (stays at limit)
   - Log entry is created for monitoring
3. **If under limit:**
   - Search executes normally
   - Counter is incremented
   - Results are returned to the agent

### Example Behavior

- **Limit = 10, Agent makes 12 search calls:**
  - First 10 searches: ✅ Executed normally
  - 11th search: ⚠️ Skipped with warning message
  - 12th search: ⚠️ Skipped with warning message
  - Agent receives warning and should proceed with available information

## Current Implementation Status

1. **✅ Code Enforcement:** Search limit is enforced in `tool_node()`
2. **✅ Per-Agent Limit:** Each researcher agent has its own independent limit
3. **✅ Early Prevention:** Searches beyond limit are prevented before execution
4. **✅ Active Tracking:** `tavily_search_count` is tracked and used for enforcement
5. **✅ Logging:** Limit reached events are logged for monitoring
6. **✅ Configurable:** Limit can be set via environment variable

## Recommendations

1. **Implement Code Enforcement:** Add limit checking in `tool_node` (Option 1)
2. **Make Configurable:** Use environment variables or config file (Options 3-4)
3. **Update Prompts:** Keep prompt limit in sync with code limit
4. **Add Logging:** Log when limit is reached for monitoring
5. **Per-Agent Limits:** Consider limiting searches per researcher agent, not globally

## Related Configuration

- **Max Researcher Iterations:** `max_researcher_iterations = 15` in `multi_agent_supervisor.py`
- **Max Concurrent Researchers:** `max_concurrent_researchers = 3` in `multi_agent_supervisor.py`
- **Max Results Per Search:** `max_results: int = 3` in `utils.py` (default)

## Files Involved

- `src/research_agent_full.py` - Main workflow orchestration
- `src/research_agent_scope.py` - Scoping and brief generation
- `src/multi_agent_supervisor.py` - Supervisor coordination
- `src/research_agent.py` - Individual researcher agents
- `src/utils.py` - Tavily search implementation
- `src/prompts.py` - Prompt templates with search limits
- `src/state_research.py` - State definitions including `tavily_search_count`
