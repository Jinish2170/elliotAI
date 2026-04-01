import sys

file_path = "veritas/agents/judge.py"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace ScoringContext creation
old_block = """        ctx = ScoringContext(
            url=evidence.url,
            site_type=site_type,
            site_type_confidence=evidence.site_type_confidence,
        )

        # Fill in visual scores
        if evidence.vision_result:
            vr = evidence.vision_result
            ctx.visual_score = vr.visual_score * 100
            ctx.temporal_score = vr.temporal_score * 100
            ctx.has_dark_patterns = vr.total_patterns_found > 0
            if vr.dark_patterns:
                ctx.dark_pattern_types = tuple(p.pattern_type for p in vr.dark_patterns[:10])
            ctx.script_count = getattr(vr, 'js_analysis', {}).get('script_count', 0)
            ctx.dom_depth = getattr(vr, 'dom_analysis', {}).get('depth', 0)
            ctx.screenshot_count = vr.screenshots_analyzed

        # Fill in structural scores
        if evidence.graph_result:
            gr = evidence.graph_result
            ctx.structural_score = gr.structural_score * 100 if hasattr(gr, 'structural_score') else 65.0
            ctx.graph_score = gr.graph_score * 100
            ctx.has_ssl = gr.has_ssl
            ctx.domain_age_days = gr.domain_age_days if gr.domain_age_days >= 0 else None
            ctx.has_lazy_load = getattr(gr, 'has_lazy_load', False)
            ctx.screenshot_count = min(ctx.screenshot_count, getattr(gr, 'screenshot_count', 1))

        # Fill in scores from SubSignals
        signals = decision.trust_score_result.signals if decision.trust_score_result else {}
        if "meta" in signals:
            ctx.meta_score = signals["meta"].raw_score * 100
        if "security" in signals:
            ctx.security_score = signals["security"].raw_score * 100

        # Fill in security results
        sec = evidence.security_results or {}
        phishing = sec.get("phishing_db") or sec.get("phishing", {})
        ctx.has_phishing_hits = phishing.get("is_phishing", False)
        js = sec.get("js_analysis", {})
        ctx.js_risk_score = js.get("risk_score", 0.0)

        # Check for cross-domain forms
        for scout in evidence.scout_results:
            fv = getattr(scout, 'form_validation', {})
            if fv and fv.get("has_cross_domain", False):
                ctx.has_cross_domain_forms = True
                ctx.form_validation_score = fv.get("score", 50.0)
                break"""

new_block = """        ctx_kwargs = {
            "url": evidence.url,
            "site_type": site_type,
            "site_type_confidence": evidence.site_type_confidence,
        }

        # Fill in visual scores
        if evidence.vision_result:
            vr = evidence.vision_result
            ctx_kwargs["visual_score"] = vr.visual_score * 100
            ctx_kwargs["temporal_score"] = vr.temporal_score * 100
            ctx_kwargs["has_dark_patterns"] = vr.total_patterns_found > 0
            if vr.dark_patterns:
                ctx_kwargs["dark_pattern_types"] = tuple(p.pattern_type for p in vr.dark_patterns[:10])
            ctx_kwargs["script_count"] = getattr(vr, 'js_analysis', {}).get('script_count', 0)
            ctx_kwargs["dom_depth"] = getattr(vr, 'dom_analysis', {}).get('depth', 0)
            ctx_kwargs["screenshot_count"] = vr.screenshots_analyzed

        # Fill in structural scores
        if evidence.graph_result:
            gr = evidence.graph_result
            ctx_kwargs["structural_score"] = getattr(gr, 'structural_score', 0.65) * 100
            ctx_kwargs["graph_score"] = gr.graph_score * 100
            ctx_kwargs["has_ssl"] = gr.has_ssl
            ctx_kwargs["domain_age_days"] = gr.domain_age_days if gr.domain_age_days >= 0 else None
            ctx_kwargs["has_lazy_load"] = getattr(gr, 'has_lazy_load', False)
            if "screenshot_count" in ctx_kwargs:
                ctx_kwargs["screenshot_count"] = min(ctx_kwargs["screenshot_count"], getattr(gr, 'screenshot_count', 1))
            else:
                ctx_kwargs["screenshot_count"] = getattr(gr, 'screenshot_count', 1)

        # Fill in scores from SubSignals
        signals = decision.trust_score_result.signals if decision.trust_score_result else {}
        if "meta" in signals:
            ctx_kwargs["meta_score"] = signals["meta"].raw_score * 100
        if "security" in signals:
            ctx_kwargs["security_score"] = signals["security"].raw_score * 100

        # Fill in security results
        sec = evidence.security_results or {}
        phishing = sec.get("phishing_db") or sec.get("phishing", {})
        ctx_kwargs["has_phishing_hits"] = phishing.get("is_phishing", False)
        js = sec.get("js_analysis", {})
        ctx_kwargs["js_risk_score"] = js.get("risk_score", 0.0)

        # Check for cross-domain forms
        for scout in evidence.scout_results:
            fv = getattr(scout, 'form_validation', {})
            if fv and fv.get("has_cross_domain", False):
                ctx_kwargs["has_cross_domain_forms"] = True
                ctx_kwargs["form_validation_score"] = fv.get("score", 50.0)
                break
                
        ctx = ScoringContext(**ctx_kwargs)"""

text = text.replace(old_block, new_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print("done")
