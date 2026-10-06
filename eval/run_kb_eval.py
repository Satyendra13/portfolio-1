import json
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.api.app.core.db import Base
from apps.api.app.models.models import Tenant
from apps.api.app.services.tenant_service import TenantService
from apps.api.app.services.kb_ingest import KBIngestService
from apps.api.app.services.kb_search import KBSearchService
from apps.worker.grounding import evaluate_grounded_answer


async def run_kb_eval():
    print("=" * 65)
    print("ASISTLINE AI — MILESTONE M2 KNOWLEDGE BASE EVALUATION SUITE")
    print("=" * 65)

    # 1. Initialize DB & seed data
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        await TenantService.seed_tenants_from_files(session, tenants_dir="data/tenants")
        await KBIngestService.seed_tenant_kbs(session, kb_dir="data/kb")

        with open("eval/kb_eval_set.json", "r", encoding="utf-8") as f:
            eval_data = json.load(f)

        in_kb_set = eval_data.get("in_kb", [])
        out_of_kb_set = eval_data.get("out_of_kb", [])

        # 2. Evaluate In-KB Dataset (30 questions)
        in_kb_passed = 0
        in_kb_total = len(in_kb_set)

        print(f"\nEvaluating In-KB Dataset ({in_kb_total} questions)...")
        for item in in_kb_set:
            tenant_id = item["tenant_id"]
            query = item["query"]
            expected_kw = item["expected_keyword"].lower()

            tenant_cfg = await TenantService.get_tenant_config(session, tenant_id)
            hits = await KBSearchService.hybrid_search(session, tenant_id, query, top_k=3)
            answer_obj = await evaluate_grounded_answer(query, hits, tenant_cfg, "en")

            if answer_obj.is_grounded and len(answer_obj.used_chunk_ids) > 0 and expected_kw in answer_obj.answer.lower():
                in_kb_passed += 1
            else:
                print(f"  [FAIL] Tenant '{tenant_id}': '{query}' -> Expected '{expected_kw}', got: '{answer_obj.answer}'")

        in_kb_acc = (in_kb_passed / in_kb_total) * 100.0

        # 3. Evaluate Out-of-KB Dataset (15 questions)
        out_kb_passed = 0
        out_kb_total = len(out_of_kb_set)

        print(f"\nEvaluating Out-of-KB Dataset ({out_kb_total} questions)...")
        for item in out_of_kb_set:
            tenant_id = item["tenant_id"]
            query = item["query"]

            tenant_cfg = await TenantService.get_tenant_config(session, tenant_id)
            hits = await KBSearchService.hybrid_search(session, tenant_id, query, top_k=3)
            answer_obj = await evaluate_grounded_answer(query, hits, tenant_cfg, "en")

            expected_not_found = tenant_cfg["script"]["not_found"]["en"]
            if not answer_obj.is_grounded and answer_obj.answer == expected_not_found:
                out_kb_passed += 1
            else:
                print(f"  [UNGROUNDED HALLUCINATION DETECTED] Tenant '{tenant_id}': '{query}' -> '{answer_obj.answer}'")

        out_kb_acc = (out_kb_passed / out_kb_total) * 100.0

        # 4. Print Summary Report
        print("\n" + "=" * 65)
        print("EVALUATION RESULTS SUMMARY")
        print("=" * 65)
        print(f"In-KB Retrieval & Answer Accuracy : {in_kb_acc:.1f}% ({in_kb_passed}/{in_kb_total}) [Target: >= 90.0%]")
        print(f"Out-of-KB Refusal Rate (No Hallucination): {out_kb_acc:.1f}% ({out_kb_passed}/{out_kb_total}) [Target: 100.0%]")
        
        in_kb_target = in_kb_acc >= 90.0
        out_kb_target = out_kb_acc == 100.0

        if in_kb_target and out_kb_target:
            print("\n>>> ALL ACCEPTANCE CRITERIA PASSED SUCCESSFULLY! <<<")
        else:
            print("\n>>> EVALUATION DID NOT MEET BENCHMARK TARGETS <<<")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_kb_eval())
