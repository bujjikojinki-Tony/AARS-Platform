#!/usr/bin/env python3
"""Sequential trigger evaluation wrapper for sandbox-constrained environments."""

import argparse
import json
from pathlib import Path

from scripts.run_eval import find_project_root, run_single_query
from scripts.utils import parse_skill_md


def main() -> None:
    parser = argparse.ArgumentParser(description="Sequential trigger evaluation wrapper")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p")
    parser.add_argument("--output", required=True, help="Path to write eval results JSON")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)
    name, original_description, _ = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    results = []
    for item in eval_set:
        triggers = []
        for _ in range(args.runs_per_query):
            triggers.append(
                run_single_query(
                    item["query"],
                    name,
                    description,
                    args.timeout,
                    str(project_root),
                    args.model,
                )
            )
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        did_pass = trigger_rate >= args.trigger_threshold if should_trigger else trigger_rate < args.trigger_threshold
        results.append(
            {
                "query": item["query"],
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers),
                "pass": did_pass,
            }
        )

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    output = {
        "skill_name": name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }
    Path(args.output).write_text(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
