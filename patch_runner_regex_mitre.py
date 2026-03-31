import re
file_path = 'backend/services/audit_runner.py'
content = open(file_path, encoding='utf-8').read()

# Replace MITRE
content = re.sub(
    r'# Emit MITRE TTPs for UI based on risk\s*r_lev = technical.get\("risk_level", "unknown"\).lower\(\).*?elif r_lev == "suspicious":.*?Identity Info"\}\}\)',
    '''# Emit MITRE TTPs for UI based on risk
        has_forms = sum(len(res.get("forms_detected", [])) for res in result.get("scout_results", []) if isinstance(res, dict)) > 0
        r_lev = technical.get("risk_level", "unknown").lower()
        await send({"type": "mitre_technique_mapped", "technique": {"technique_id": "T1590", "tactic": "TA0043", "technique_name": "Gather Victim Network Information"}})
        if has_forms:
            await send({"type": "mitre_technique_mapped", "technique": {"technique_id": "T1589", "tactic": "TA0043", "technique_name": "Gather Victim Identity Info"}})
        if r_lev in ["high_risk", "likely_fraudulent"]:
            await send({"type": "mitre_technique_mapped", "technique": {"technique_id": "T1566", "tactic": "TA0001", "technique_name": "Phishing"}})
            await send({"type": "mitre_technique_mapped", "technique": {"technique_id": "T1114", "tactic": "TA0009", "technique_name": "Email Collection"}})
            await send({"type": "mitre_technique_mapped", "technique": {"technique_id": "T1059", "tactic": "TA0009", "technique_name": "Command and Control"}})
        elif r_lev == "suspicious":
            await send({"type": "mitre_technique_mapped", "technique": {"technique_id": "T1583", "tactic": "TA0043", "technique_name": "Acquire Infrastructure"}})
            await send({"type": "mitre_technique_mapped", "technique": {"technique_id": "T1190", "tactic": "TA0001", "technique_name": "Exploit Public-Facing Application"}})''',
    content, flags=re.DOTALL
)

# Replace CVSS mapping
content = re.sub(
    r'mapped_metrics = \[\{"name": k, "value": str\(v\), "severity": "HIGH"\} for k, v in cvss_metrics.items\(\) if k != "base_score"\]',
    '''def map_sev(val_str):
                return "CRITICAL" if val_str in ("H", "High") else "HIGH" if val_str in ("M", "Medium") else "LOW" if val_str in ("L", "Low", "N", "None") else "MEDIUM"
            mapped_metrics = [{"name": k, "value": str(v), "severity": map_sev(str(v))} for k, v in cvss_metrics.items() if k != "base_score"]''',
    content
)

open(file_path, 'w', encoding='utf-8').write(content)
print("Regex patch applied MITRE/CVSS.")
