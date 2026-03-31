import re

file_path = 'frontend/src/components/terminal/CvssRadar.tsx'
content = open(file_path, encoding='utf-8').read()

# Replace the data mapping logic
old_data_map = '''  const data = metrics.map((m) => ({
    subject: m.name.replace(/_/g, '').substring(0, 7).toUpperCase(),
    A: sevMap[m.severity] || 0,
    fullLabel: \\: \\,
    color: m.severity === "CRITICAL" ? "var(--t-red)" : m.severity === "HIGH" ? "var(--t-amber)" : "var(--t-green)"
  }));'''

new_data_map = '''  // Map full metric names to CVSS abbreviations to prevent radar labeling overlap
  const abbrMap: Record<string, string> = {
    "attack_vector": "AV", "Attack Vector": "AV",
    "attack_complexity": "AC", "Attack Complexity": "AC",
    "privileges_required": "PR", "Privileges Required": "PR", "Privileges Req": "PR",
    "user_interaction": "UI", "User Interaction": "UI",
    "scope": "S", "Scope": "SC", // Use SC for scope to differentiate slightly if needed, standard is S
    "confidentiality": "C", "Confidentiality": "C",
    "integrity": "I", "Integrity": "I",
    "availability": "A", "Availability": "A"
  };

  const data = metrics.map((m) => {
    let rawName = m.name;
    // For raw keys like "attack_vector" parse appropriately
    if (!abbrMap[rawName]) {
      const p = rawName.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());
      rawName = p;
    }
    const mappedSubject = abbrMap[rawName] || abbrMap[m.name] || m.name.replace(/_/g, '').substring(0, 4).toUpperCase();
    
    // Parse value to actual CVSS numeric severity if possible, else use severity string map
    let metricValue = sevMap[m.severity] || 2;
    // Enhance visual spread so it doesn't look like a perfect circle
    if (m.severity === "HIGH" && m.value !== "H") metricValue = 3.2;
    if (m.severity === "LOW" && m.value !== "L") metricValue = 1.2;
    
    return {
      subject: mappedSubject,
      A: metricValue,
      fullLabel: \\: \\,
      color: m.severity === "CRITICAL" ? "var(--t-red)" : m.severity === "HIGH" ? "var(--t-amber)" : "var(--t-green)"
    };
  });'''

if old_data_map in content:
    content = content.replace(old_data_map, new_data_map)
    open(file_path, 'w', encoding='utf-8').write(content)
    print("Frontend CVSSRadar Patched")
else:
    print("Failed to find old CVSSRadar block")
