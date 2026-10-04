# AARS LLM Research Layer v1

The LLM is a research reviewer, not an execution engine.

Boundary:
- reads structured AARS evidence;
- explains supporting/counter evidence, risks and hypotheses;
- cannot place orders, change exposure/leverage, mutate strategy parameters, or bypass PAPER_ONLY;
- output is explicitly RESEARCH_ONLY.

Configure `OPENAI_API_KEY` locally. Default model is `gpt-6-luna`; override with `AARS_LLM_MODEL`.

Example:
```bash
python run_llm_review.py --input evidence.json
```

Do not commit secrets.
