# Making Research Agent Production-Grade — Mentorship Q&A

> A Socratic review of what it takes to move this project from a terminal scaffold to a
> production service. Format: sharp questions first, attempted answers, staff-engineer
> critique, then full answers. Use it to *defend* each decision, not just recall it.

---

## 0. What the system actually is today (the honest read)

It's labeled a "research **agent**," but the code is a **fixed, linear, single-process
workflow with an LLM cherry on top**, driven by a terminal REPL.

- Every tool runs unconditionally on the same input — `for tool in self.tools:` in
  [`orchestrator.py`](../src/research_agent/orchestrator.py) (~line 87). The LLM **never
  decides** which tools to call.
- The LLM runs **once, at the very end**, only to prose-ify the report
  ([`answer_compiler.py`](../src/research_agent/answer_compiler.py) ~line 18).
- [`QueryEnhancer`](../src/research_agent/query_enhancer.py) is a static string template.
- [`Evaluator`](../src/research_agent/evaluation.py) is three `if` statements on word count
  and citation count.
- If **any** tool throws, the whole run dies (`raise` in the orchestrator tool loop).
- State lives in a Python object; `message_index` is hand-incremented in a `while` loop
  ([`main.py`](../src/research_agent/main.py) ~line 90).

None of this is a criticism of a scaffold — it's the baseline we're upgrading from.

---

## Q1 — Agent vs. Workflow: the identity question

**Questions asked**
- What do you gain by letting the LLM choose tools and loop, vs. the current fixed pipeline?
  Name a concrete query where the fixed pipeline gives a *worse* answer.
- The flip side most people miss: what do you *lose* by going agentic?

**My answer (attempt)**
- Agents shine on **dynamic queries** — e.g. two questions in one. A **planner agent** splits
  the query into sub-queries and dispatches them to the vector DB and web tool separately.
- The LLM can **set `top_k` dynamically** based on query and document size (e.g. "top 10
  historic events in India last year" → `top_k` ~10–20).
- **Workflows** are better for **streamlined, single-purpose tasks** — e.g. "upload an image,
  get a cartoon version." One predefined path, so no agency needed.

**Staff-engineer critique — 70%. Right instinct, missed the cost.**
- Query decomposition and dynamic parameterization are legitimate places where an LLM
  decision earns its keep. But the answer only argued the **upside**.
- **What you lose going agentic:** determinism, testability, and a bounded cost/latency
  budget. A fixed pipeline always makes the same N calls — you can reason about its p95 and
  its bill. Once the LLM decides *how many* tools and *how many* loops, cost and latency
  become a **distribution, not a number**, and a bad plan can silently multiply spend.
  Debugging degrades too: "why did it do that?" now has a non-deterministic answer.
- **The missing insight — it's not binary.** "Two questions in one → split → fan out" is
  *not* a full agent. It's a **workflow with one LLM decision point** (a router/decomposer)
  followed by deterministic parallel execution. That's the sweet spot for ~80% of "agents":
  mostly workflow, agency injected *only* at the step that needs open-ended judgment. Reach
  for a full autonomous loop (ReAct, self-directed tool calls until done) only when you
  genuinely can't predict the steps in advance.
- **Challenge:** is an extra LLM round-trip to pick `top_k` ∈ [10,20] worth the latency,
  tokens, and new failure mode? Cheaper: always over-retrieve (top 50) and **rerank** down.
  Over-retrieve + rerank almost always beats "LLM guesses a number." (Revisited in Q6.)

---

## Q2 — The CLI → Service jump: where does state live?

**Questions asked**
- With an HTTP API behind a load balancer (3 replicas), where does conversation state live,
  and how does request #2 for a session find it?
- `FileRepository` writes `.txt` files. What breaks when two requests for the same session
  land on two pods at once?

**My answer (attempt)**
- Scale up → **Postgres** for durable data + a **Redis** caching layer.
- Store the user's past queries/conversation in Redis; the LLM resumes from the context
  window saved as the whole session in Redis.
- Drop `FileRepository` in production; use Postgres instead.

**Staff-engineer critique — 60%. Named the components; dodged the hard part.**
- **Which store is the source of truth?** Redis is a *cache* — it evicts, goes cold, can be
  flushed. If history lives *only* in Redis and a key evicts, the session is lost. The
  invariant: **Postgres = durable truth; Redis = rebuildable hot-path cache** (cache-aside,
  TTL, repopulated from Postgres on miss). If Redis can't be reconstructed from Postgres,
  the design is wrong.
- **The concurrency question was skipped — and it's the whole point.** `message_index += 2`
  in [`main.py`](../src/research_agent/main.py) is fine in a REPL. With two concurrent
  requests for one session on two pods:
  - Who assigns message ordering? Both pods think they're at index 4 → collision / lost msg.
  - `FileRepository` writes the same `.txt` → interleaved/corrupt writes, last-writer-wins.
  - **This is the real CLI→service tax:** ordering and write-safety that a single process
    gave you for free. Fixes: DB-generated sequence for order, a unique constraint to reject
    dupes, per-session serialization or optimistic locking, and **idempotency keys** so a
    client retry doesn't double-append.
- **Context growth:** the LLM client silently truncates to the last 10 turns
  ([`openrouter.py`](../src/research_agent/llm/openrouter.py) ~line 29). At turn 50, turns
  1–40 vanish. Truncate vs. summarize vs. retrieve-relevant-turns is a real design choice,
  not a `[-10:]`.

---

## Q3 — Failure handling: one tool kills everything

**Questions asked**
- Is hard-failing the whole run the right call for a *research* agent? If web search times
  out but vector search succeeded, what should the user get?
- What's your failure policy when the model provider is flaky or rate-limits you?

**My answer (attempt)**
- **Error checking from the planner side:** if it's an input error the agent can fix, retry
  with fixed input.
- If unfixable, **skip that tool and use alternatives** — e.g. web down → use cached past web
  results, or fall to the vector DB.
- **LLM timeout:** don't use a 120s timeout in prod; **divert to another model/provider** not
  currently rate-limited. If everything fails, tell the user the service is unavailable.

**Staff-engineer critique — 75%. Best of the three; strong graceful-degradation instinct.**
- **Don't send an LLM to diagnose a 429.** Putting an LLM call on the failure path adds
  latency and a new failure surface exactly when things are broken. Retryable-vs-not is a
  **deterministic** decision: 429/503/timeout → retry with **exponential backoff + jitter**,
  capped; 400/401 → don't retry. Save the LLM for reasoning, not HTTP triage.
- **Retries need a governor.** Naive retry during an outage = retry storm = self-inflicted
  DDoS on your dependency. That's what a **circuit breaker** is for: after N failures, stop
  calling for a cooldown and fail fast. (Backoff and breakers were both missing.)
- **Stale cache has a truth cost.** Answering "events *last year*" from a stale cache can be
  wrong. If you degrade to cached data, **label freshness** in the answer.
- **Timeouts as a budget:** per-hop timeouts (embed ~2s, web ~5s, LLM ~20s) *and* a total
  request SLA. Fail fast, return partial. On hard failure, return a clean error with
  `Retry-After`; keep session state intact so the user can retry without losing the thread.

---

## Q4 — Quality: how do you know it's *good*? (full answer)

The current evaluator counts words and citations. It **cannot distinguish a correct answer
from a confident hallucination** — the single most important RAG failure mode.

- **Separate two things people conflate:**
  - *Offline eval* (before shipping a change): a **golden dataset** — 50–100 representative
    queries with expected key facts / must-cite sources. This is the CI gate; a change that
    drops the score doesn't merge.
  - *Online monitoring* (in prod, no ground truth): proxy signals — thumbs up/down, did the
    user immediately rephrase (dissatisfaction), citation coverage, LLM-as-judge on a
    *sample* of live traffic.
- **Build the golden set with categories**, and critically include **negative/abstention
  cases** — queries whose answer is *not* in the corpus, where the correct behavior is "I
  don't know," not a fabrication. The word-count evaluator scores a hallucinated 200-word
  answer *higher* than an honest "insufficient evidence." That's backwards.
- **Decompose the score — the debugging superpower.** For RAG, measure separately:
  - **Faithfulness / groundedness:** is every claim supported by a retrieved chunk?
    (catches hallucination)
  - **Context precision / recall:** did retrieval fetch the right chunks? (isolates a
    retrieval bug from a generation bug)
  - **Answer relevance:** does it address the question?

  One number can't tell you whether a bad answer is bad retrieval or bad synthesis.
  RAGAS-style decomposition tells you *which half to fix*.
- **Scoring method + trade-off:** keyword match is cheap and brittle; embedding similarity is
  better but shallow; **LLM-as-judge** is the flexible default — but the judge is itself an
  LLM (cost, bias) and needs its *own* validation against ~20 human labels. Use a **strong**
  judge model even if you serve with a cheap one.
- **Proving model B > A:** hold the golden set fixed, run both at **temperature 0**, compare
  aggregate *and per-category* — watch for B better on average but regressing on abstention.
  On 30 examples a 2-point move is noise; pairwise judge-preference often beats absolute
  scores.
- **Concrete change:** keep the rule-based `Evaluator` as a cheap *online guardrail* if you
  like, but it is **not the quality bar.** Add an offline eval harness (a script +
  `golden.jsonl`) as the real gate.

---

## Q5 — Cost & latency: measure first (full answer)

- **Where the money goes:** embedding is a *one-time, amortized, cached* cost (`VectorCache`
  already helps). The **recurring** cost is chat LLM tokens, dominated by **input tokens**.
  Connection to Q1: running *all* tools every time bloats the report → bloats the prompt →
  bloats cost *and* latency. The fixed pipeline is also a cost bug.
- **Where p95 latency goes:** (1) the final LLM generation dominates (seconds); (2) tools run
  **sequentially** in the orchestrator loop even though they're independent — pure waste;
  (3) cold-start index build.
- **Measure before optimizing:** extend `ExecutionLogger` to record **per-stage duration and
  token count**, then read p50/p95/p99 *per stage* and cost per request. Find the stage that
  *owns* p95 — don't optimize by vibes.
- **Attack order:**
  1. **Parallelize independent tools** (`asyncio.gather` / thread pool). Wall-clock: *sum* →
     *max*. Biggest free win.
  2. **Stream the final response** (the client currently reads the whole body first). Same
     cost, far better *perceived* latency (time-to-first-token).
  3. **Trim context** via a router (only run/include relevant tools) → fewer input tokens.
  4. **Cache**: add answer/semantic caching on top of the existing web + embedding caches.
  5. **Model routing:** cheap/fast model for enhance + eval, strong model only for synthesis.
- **The trade-off triangle:** latency ↔ cost ↔ quality. Streaming buys perceived latency for
  free. Smaller models cut cost/latency but risk quality — which is *why you build Q4's eval
  first*: it's the safety net that lets you make the cheap-model trade without flying blind.

---

## Q6 — Retrieval / RAG (full answer)

- **What restart does:** the ANN structure lives in RAM. Restart → gone; even with
  `VectorCache` on disk you rebuild the index every boot, and **each replica holds a full
  copy** → memory blowup + duplicated work + no shared state. Doesn't scale horizontally.
  **Move to a real vector store** (pgvector for one fewer system, or Qdrant/Weaviate/Milvus)
  with an ANN index (HNSW/IVF).
- **At 10k PDFs:** a brute-force cosine scan is **O(N) per query** — fine at 100 chunks, dead
  at millions. ANN is the trade: exact-but-slow-and-small vs. approximate-but-fast-and-large.
- **Ingestion must become a real pipeline**, decoupled from the query path: parse → chunk →
  embed → **upsert**, run as an async/offline job that is **incremental** (only new/changed
  docs) and **idempotent** (re-ingest doesn't duplicate). Today ingestion is coupled to the
  search tool — a request-path landmine.
- **Fixed chunk + fixed `top_k` failure modes:**
  - Char-based sliding windows split sentences and **shred tables/headers** in PDFs. Use
    **structure-aware chunking**.
  - Fixed `top_k`: too small misses context; too large dilutes with noise and burns tokens.
- **The upgrades (closes the Q1 loop):**
  - **Hybrid search** (dense embeddings + sparse BM25, fused): dense misses exact tokens
    (names, IDs, acronyms), sparse misses paraphrase. Together they cover both.
  - **Rerank**: retrieve top 50 cheaply, cross-encoder rerank to top 5 — *better precision
    than dynamic `top_k` ever would*, which is why the LLM-picks-`top_k` idea loses.
  - **Metadata filtering**: "events in the **last year**" is a *temporal* filter, not a
    similarity problem. Pure vector search returns relevant-but-old chunks. Needs date
    metadata + filtering — a class of query vector search alone can't answer correctly.
  - **Abstention threshold**: if the best retrieval score is below a floor, don't synthesize
    — say "not in corpus" or fall to web. The anti-hallucination lever, measurable by Q4.

---

## The change order (if I owned this)

1. **Stateless service** (FastAPI), source-of-truth Postgres, Redis as cache. Fix message
   ordering + idempotency. *(Q2 — everything else assumes this.)*
2. **Reliability**: parallelize tools, per-hop timeouts + budget, backoff/circuit-breaker,
   provider fallback, partial-result degradation. *(Q3, Q5)*
3. **Eval harness + golden set** *before* touching model/retrieval — so every later change is
   provable. *(Q4)*
4. **Real vector store + hybrid + rerank + metadata + abstention.** *(Q6)*
5. **Add agency surgically** — a decomposition/router step, not a free-running loop. *(Q1)*
6. **Cost/latency**: streaming, model routing, context trimming, caching — now safe because
   eval exists. *(Q5)*
7. **Observability & security**: tracing/token metrics, auth, per-tenant rate limits, PII
   handling.

---

## Known bug found during review

[`README.md`](../README.md) says "Gemini-backed" and tells users to set `GEMINI_API_KEY`, but
the code uses **OpenRouter** and reads `OPEN_ROUTER_API`. Doc drift breaks onboarding on day
one — "product-grade" includes the docs being true.

---

## Open interview question (unanswered — defend this next)

In step 1, if two requests for the same session arrive concurrently, do you **serialize** them
(one waits) or **process both** — and what does that choice do to the user's experience and
your data model? That single decision shapes the whole state design.
