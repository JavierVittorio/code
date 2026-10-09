"""Render a scorecard dict as Markdown (what a reviewer reads in the PR)."""
from __future__ import annotations


def _p(v) -> str:
    return "-" if v is None else f"{100 * v:.1f}%"


def _n(v) -> str:
    return "-" if v is None else (f"{v:,.0f}" if isinstance(v, (int, float)) and abs(v) >= 100 else str(v))


def render_markdown(card: dict) -> str:
    m, h, ops = card.get("meta", {}), card["headline"], card["ops"]
    L = [f"# Scorecard - {m.get('run_name', '')}", "",
         f"model `{m.get('model')}` | prompt `{m.get('prompt_version')}` | images `{m.get('image_profile')}` | "
         f"config `{m.get('config_fingerprint')}` | git `{m.get('git_sha')}` | dataset `{m.get('dataset_hash')}` "
         f"({m.get('n_docs')} docs, split={m.get('split')})", "",
         "## Headline", "",
         "| metric | value | meaning |", "|---|---|---|",
         f"| field accuracy | **{_p(h['accuracy'])}** | labeled fields whose final answer is right (incl. correct 'absent') |",
         f"| raw accuracy (before abstention) | {_p(h.get('raw_accuracy'))} | extraction quality independent of the abstain threshold |",
         f"| precision of emitted values | **{_p(h['precision'])}** | of values we returned, share correct |",
         f"| hallucination rate | **{_p(h['hallucination_rate'])}** | values returned for fields verified NOT on the page |",
         f"| coverage | {_p(h['coverage'])} | fields not abstained / failed |",
         f"| miss rate | {_p(h['miss_rate'])} | said 'absent' but the field is printed |",
         f"| wrong-value rate | {_p(h['wrong_rate'])} | emitted a value that does not match (near-miss share {_p(h['near_miss_share_of_wrong'])}) |",
         f"| abstention precision | {_p(h['abstention_precision'])} | abstentions that prevented an error |",
         f"| docs with every field correct | {_p(h['doc_all_fields_correct'])} | |", ""]
    rr = card["review_routing"]
    L += ["## Review routing (production view)", "",
          f"- straight-through (auto-approved) docs: **{_p(rr['straight_through_rate'])}**; of those, fully correct: "
          f"**{_p(rr['straight_through_doc_accuracy'])}**",
          f"- docs whose printed numbers don't reconcile (should be flagged): {rr['should_flag_docs']}, caught: "
          f"{_p(rr['should_flag_recall'])}", ""]
    L += ["## Failure taxonomy", "", "| outcome | count |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in card["outcomes"].items()]
    L += ["", "## By field", "",
          "| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |",
          "|---|---|---|---|---|---|---|---|---|"]
    for f, fm in card["by_field"].items():
        oc = ", ".join(f"{k}:{v}" for k, v in fm["outcomes"].items() if k not in ("correct", "correct_absent"))
        L.append(f"| {f} | {fm['n']} | {_p(fm['accuracy'])} | {_p(fm['precision'])} | {_p(fm['hallucination_rate'])} | "
                 f"{_p(fm['miss_rate'])} | {_p(fm['wrong_rate'])} | {_p(fm['abstain_rate'])} | {oc} |")
    li = card["line_items"]
    L += ["", "## Line items", "",
          f"{li['docs']} docs, {li['gt_rows']} GT rows, {li['pred_rows']} predicted. Row P/R/F1 (all labeled cells "
          f"correct): {_p(li['row_precision'])} / {_p(li['row_recall'])} / {_p(li['row_f1'])}. Row count exact: "
          f"{_p(li['row_count_exact_rate'])}. Cell accuracy: "
          + ", ".join(f"{c} {_p(v)}" for c, v in li["cell_accuracy"].items()), ""]
    L += ["## By slice", "", "| slice | fields | accuracy | precision | halluc. | abstain |", "|---|---|---|---|---|---|"]
    for t, fm in card["by_tag"].items():
        L.append(f"| {t} | {fm['n']} | {_p(fm['accuracy'])} | {_p(fm['precision'])} | {_p(fm['hallucination_rate'])} | "
                 f"{_p(fm['abstain_rate'])} |")
    for key, title in (("calibration", "all docs"), ("calibration_test_split", "held-out test split")):
        c = card[key]
        if not c.get("n"):
            continue
        L += ["", f"## Confidence calibration ({title})", "",
              f"n={c['n']} proposed values, base accuracy {_p(c['base_accuracy'])}, ECE **{c['ece']}**, AUROC fused "
              f"**{c['auroc_fused']}** vs model self-confidence {c['auroc_self_conf']}", "",
              "| conf bin | n | mean conf | accuracy |", "|---|---|---|---|"]
        L += [f"| {b['bin']} | {b['n']} | {b['mean_conf']} | {_p(b['accuracy'])} |" for b in c["reliability"]]
        L += ["", "Risk-coverage (answer only the most confident X%):", "", "| coverage | accuracy | conf threshold |",
              "|---|---|---|"]
        L += [f"| {_p(r['coverage'])} | {_p(r['accuracy'])} | {r['threshold']} |" for r in c["risk_coverage"]]
    L += ["", "## Cost & latency", "",
          f"| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | "
          f"in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|",
          f"| {ops['documents']} | {ops['failed_docs']} | {_n(ops['latency_ms_p50'])} ms | {_n(ops['latency_ms_p95'])} ms | "
          f"{ops['llm_calls_per_doc']} | {_p(ops['reask_rate'])} | {_p(ops['json_repair_rate'])} | "
          f"{_n(ops['input_tokens_per_doc'])} | {_n(ops['output_tokens_per_doc'])} | ${ops['cost_usd_total']} | "
          f"${ops['list_cost_usd_per_1k_docs']} | {m.get('docs_per_min', '-')} docs/min |", ""]
    if ops["cache_hit_docs"]:
        L.append(f"_{ops['cache_hit_docs']} docs served from response cache (excluded from latency percentiles)._")
    return "\n".join(L) + "\n"
