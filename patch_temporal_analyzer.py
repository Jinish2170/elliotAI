import re
import sys

def patch_temporal_analyzer():
    with open('veritas/analysis/temporal_analyzer.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The OCR logic for countdowns triggers when ANY pattern "\d{1,2}:\d{2}" is the same across shots...
    # We should only analyze timers if they are ACTUALLY counting down, or if the surround text implies a timer ("sale", "offer", "ends in", "hurry")
    # Actually, a better fix: if seconds_b >= seconds_a, we ONLY flag if we know it's a countdown context.
    # For now, let's just bypass OCR timer "fake_countdown" logic unless there's a strong indication or let's remove it because pixel analysis and VLM do it better anyway.
    
    # Alternatively, ensure the regex requires "00:00:00" explicitly or it doesn't fire.
    
    target = r'(if seconds_b >= seconds_a:\n\s+# Timer went UP or stayed same â€” likely reset\n\s+findings\.append\(TemporalFinding\()'
    replacement = r'if seconds_b > seconds_a:\n                        # Timer went UP -- likely reset\n                        findings.append(TemporalFinding('
    content = re.sub(target, replacement, content, count=1)
    
    # Wait, the above logic says if `seconds_b >= seconds_a` ... if it stayed the SAME, it could just be a static clock or part of an article text.
    # Let's fix that.
    
    # Let's replace the whole block using string replace to be safe.
    old_block = """                    if seconds_b >= seconds_a:
                        # Timer went UP or stayed same â€” likely reset
                        findings.append(TemporalFinding(
                            finding_type="fake_countdown",
                            value_at_t0=ta,
                            value_at_t_delay=tb,
                            delta_seconds=delay_seconds,
                            is_suspicious=True,"""
    new_block = """                    if seconds_b > seconds_a:
                        # Timer went UP â€” likely reset
                        findings.append(TemporalFinding(
                            finding_type="fake_countdown",
                            value_at_t0=ta,
                            value_at_t_delay=tb,
                            delta_seconds=delay_seconds,
                            is_suspicious=True,"""
    content = content.replace(old_block, new_block)

    with open('veritas/analysis/temporal_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(content)

patch_temporal_analyzer()
print("Temporal Analyzer patched.")
