import re

def main():
    with open("veritas/agents/vision.py", "r") as f:
        content = f.read()

    # Block 1: 
    old1 = """                confidence = float(finding.get("confidence", 0.5))
                if confidence < 0.3:"""
    new1 = """                try:
                    confidence_raw = finding.get("confidence", 0.8)
                    if isinstance(confidence_raw, str):
                        confidence = float(re.search(r"0\.\d+", confidence_raw).group()) if re.search(r"0\.\d+", confidence_raw) else 0.8
                    else:
                        confidence = float(confidence_raw)
                except Exception:
                    confidence = 0.8

                if confidence < 0.65:"""
    content = content.replace(old1, new1)


    # Block 2:
    old2 = """                confidence = float(data.get("confidence", 0.6))
                if confidence < 0.3:"""
    new2 = """                try:
                    confidence_raw = data.get("confidence", 0.8)
                    if isinstance(confidence_raw, str):
                        confidence = float(re.search(r"0\.\d+", confidence_raw).group()) if re.search(r"0\.\d+", confidence_raw) else 0.8
                    else:
                        confidence = float(confidence_raw)
                except Exception:
                    confidence = 0.8

                if confidence < 0.65:"""
    content = content.replace(old2, new2)

    with open("veritas/agents/vision.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()