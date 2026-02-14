"""Diagnose: replicate exactly what the Streamlit subprocess does."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

veritas_root = Path(r"c:\jinish\elliotAI\veritas")
python_exe = sys.executable
url = "https://example.com"
tier = "quick_scan"

# Mimic the UI's temp file
tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, dir=str(veritas_root / "data" / "cache"))
tmp_path = tmp.name
tmp.close()

cmd = [python_exe, "-m", "veritas", url, "--tier", tier, "--output", tmp_path]
cwd = str(veritas_root.parent)

print(f"python_exe: {python_exe}")
print(f"cwd:        {cwd}")
print(f"cmd:        {' '.join(cmd)}")
print(f"tmp_path:   {tmp_path}")
print(f"---")

try:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=600,
        encoding="utf-8",
        errors="replace",
    )
    print(f"returncode: {proc.returncode}")
    print(f"stdout lines: {len((proc.stdout or '').splitlines())}")
    
    # Show last 20 lines of stdout
    for line in (proc.stdout or "").splitlines()[-20:]:
        if len(line) < 500:
            print(f"  stdout: {line}")
    
    if proc.stderr:
        print(f"stderr lines: {len(proc.stderr.splitlines())}")
        for line in proc.stderr.splitlines()[-10:]:
            if len(line) < 500:
                print(f"  stderr: {line}")
    
    # Check result file
    result_path = Path(tmp_path)
    if result_path.exists():
        sz = result_path.stat().st_size
        print(f"\nResult file: {tmp_path} ({sz} bytes)")
        if sz > 10:
            data = json.loads(result_path.read_text(encoding="utf-8"))
            print(f"  status: {data.get('status')}")
            print(f"  judge_decision present: {'judge_decision' in data}")
            jd = data.get("judge_decision", {})
            tr = jd.get("trust_score_result", {})
            print(f"  trust score: {tr.get('final_score')}")
            print(f"  risk level: {tr.get('risk_level')}")
            print(f"  narrative length: {len(jd.get('narrative', ''))}")
            print(f"  findings: {len(data.get('vision_result', {}).get('findings', []))}")
            print("  SUCCESS - subprocess produced valid output")
        else:
            print(f"  File too small ({sz} bytes) - audit may have failed")
    else:
        print(f"\nResult file NOT FOUND: {tmp_path}")
        
except subprocess.TimeoutExpired:
    print("TIMEOUT after 600s")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
finally:
    try:
        Path(tmp_path).unlink(missing_ok=True)
    except:
        pass
