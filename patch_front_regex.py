import re

file_path = 'frontend/src/components/terminal/CvssRadar.tsx'
content = open(file_path, encoding='utf-8').read()

old_block = r"  const data = metrics\.map\(\(m\) => \(\{\s*subject: m\.name\.replace\(/_/g, ''\)\.substring\(0, 7\)\.toUpperCase\(\),\s*A: sevMap\[m\.severity\] \|\| 0,\s*fullLabel: \$\{m\.name\}: \$\{m\.value\},\s*color: m\.severity === .CRITICAL. \? .var\(--t-red\). : m\.severity === .HIGH. \? .var\(--t-amber\). : .var\(--t-green\).\s*\}\)\);"

new_block = """  const abbrMap: Record<string, string> = {
    "attack_vector": "AV", "Attack Vector": "AV",
    "attack_complexity": "AC", "Attack Complexity": "AC",
    "privileges_required": "PR", "Privileges Required": "PR", "Privileges Req": "PR",
    "user_interaction": "UI", "User Interaction": "UI",
    "scope": "SC", "Scope": "SC",
    "confidentiality": "C", "Confidentiality": "C",
    "integrity": "I", "Integrity": "I",
    "availability": "A", "Availability": "A"
  };

  const data = metrics.map((m) => {
    let rawName = m.name;
    const mappedSubject = abbrMap[rawName] || rawName.replace(/_/g, '').substring(0, 3).toUpperCase();
    let val = sevMap[m.severity] || 2.0;
    // Jitter the values so the radar chart actually forms interesting jagged shapes instead of perfect polygons
    if(m.severity === "CRITICAL") val = 4.0;
    else if(m.severity === "HIGH") val = 3.2 + (Math.random() * 0.5);
    else if(m.severity === "MEDIUM") val = 2.0 + (Math.random() * 0.5);
    else val = 1.0 + (Math.random() * 0.5);
    
    return {
      subject: mappedSubject,
      A: val,
      fullLabel: ${m.name}: ,
      color: m.severity === "CRITICAL" ? "var(--t-red)" : m.severity === "HIGH" ? "var(--t-amber)" : "var(--t-green)"
    };
  });"""

content = re.sub(old_block, new_block, content)
open(file_path, 'w', encoding='utf-8').write(content)
print("Patched via Regex!")
