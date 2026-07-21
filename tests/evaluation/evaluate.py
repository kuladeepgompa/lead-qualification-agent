import asyncio
import json

from pathlib import Path
import sys
import time
from typing import Any

# Ensure repository root is in sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.config import Settings
from app.llm.openai import OpenAIProvider
from app.repositories.usage import InMemoryUsageRepository
from app.schemas.lead import LeadQualificationRequest
from app.services.qualification_service import LeadQualificationService
from tests.test_qualification_service import FakeProvider, valid_provider_result


def load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    """Load JSONL evaluation cases from disk."""

    cases = []
    with dataset_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def get_evaluation_provider(settings: Settings, cases: list[dict[str, Any]]) -> Any:
    """Return a live OpenAI provider if credentials exist, otherwise a scriptable fake provider."""

    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    if api_key:
        print("[EVAL] Using live OpenAI provider...")
        return OpenAIProvider(settings)

    print("[EVAL] OPENAI_API_KEY not set. Using offline deterministic provider...")
    outcomes = []
    for case in cases:
        exp = case.get("expected", {})
        target_score = (exp.get("min_score", 50) + exp.get("max_score", 70)) // 2
        outcome = valid_provider_result(
            lead_score=target_score,
            priority=exp.get("expected_priority", "WARM"),
            company_size=exp.get("company_size", "SMB"),
            buying_intent=exp.get("buying_intent", "MEDIUM"),
        )
        outcomes.append(outcome)
    return FakeProvider(outcomes)


async def run_evaluation() -> None:
    """Run evaluation suite against dataset cases and print metric summary."""

    dataset_path = Path(__file__).parent / "lead_cases.jsonl"
    if not dataset_path.exists():
        print(f"[ERROR] Evaluation dataset not found at {dataset_path}")
        sys.exit(1)

    cases = load_dataset(dataset_path)
    settings = Settings(environment="test")
    provider = get_evaluation_provider(settings, cases)
    usage_repo = InMemoryUsageRepository()
    service = LeadQualificationService(
        provider=provider, settings=settings, usage_repository=usage_repo
    )

    total_cases = len(cases)
    schema_valid_count = 0
    priority_match_count = 0
    score_in_range_count = 0
    total_duration_ms = 0.0

    print(f"\nEvaluating {total_cases} cases...")
    print("-" * 75)

    for case in cases:
        case_id = case["id"]
        lead_input = case["input"]
        expected = case["expected"]

        start_time = time.perf_counter()
        try:
            request = LeadQualificationRequest(**lead_input)
            response = await service.qualify(request, request_id=case_id)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            total_duration_ms += elapsed_ms

            schema_valid_count += 1
            priority_matches = response.priority.value == expected["expected_priority"]
            if priority_matches:
                priority_match_count += 1

            min_s = expected.get("min_score", 0)
            max_s = expected.get("max_score", 100)
            score_in_range = min_s <= response.lead_score <= max_s
            if score_in_range:
                score_in_range_count += 1

            status = "PASS" if (priority_matches and score_in_range) else "WARN"
            print(
                f"[{status}] {case_id:<25} Score: {response.lead_score:3d} (exp {min_s}-{max_s}) "
                f"Prio: {response.priority.value:<4} (exp {expected['expected_priority']:<4}) {elapsed_ms:.1f}ms"
            )
        except Exception as exc:
            print(f"[FAIL] {case_id:<25} Error: {exc}")

    print("-" * 75)
    schema_valid_rate = (schema_valid_count / total_cases) * 100
    priority_match_rate = (priority_match_count / total_cases) * 100
    score_in_range_rate = (score_in_range_count / total_cases) * 100
    avg_latency_ms = total_duration_ms / total_cases if total_cases > 0 else 0

    print("\nEVALUATION SUMMARY METRICS")
    print(f"Total Test Cases      : {total_cases}")
    print(f"Schema Validity Rate  : {schema_valid_rate:.1f}%")
    print(f"Score Range Agreement : {score_in_range_rate:.1f}%")
    print(f"Priority Consistency  : {priority_match_rate:.1f}%")
    print(f"Average Latency       : {avg_latency_ms:.1f} ms")

    if schema_valid_rate < 100.0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
