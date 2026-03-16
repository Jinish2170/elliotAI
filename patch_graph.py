import re

with open('veritas/agents/graph_investigator.py', 'r') as f:
    text = f.read()

old_block = '''        claims = []
        try:
            response_text = result.get("response", "")
            data = self._extract_json(response_text)
            if data and "entities" in data:
                for entity in data["entities"]:
                    claims.append(
                        EntityClaim(
                            entity_type=entity.get("type", "unknown"),
                            entity_value=entity.get("value", ""),
                            source_page=url,
                            context=entity.get("context", "")
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to extract entities via LLM: {e}")

        return claims'''

new_block = '''        claims = []
        try:
            response_text = result.get("response", "")
            data = self._extract_json(response_text)
            if data and "entities" in data:
                for entity in data["entities"]:
                    claims.append(
                        EntityClaim(
                            entity_type=entity.get("type", "unknown"),
                            entity_value=entity.get("value", ""),
                            source_page=url,
                            context=entity.get("context", "")
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to extract entities via LLM: {e}")

        # Fallback to local regex if LLM yields nothing
        if not claims:
            import re
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text_trimmed)
            for e in set(emails):
                claims.append(EntityClaim(entity_type="email", entity_value=e, source_page=url, context="Extracted via regex"))
            phones = re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text_trimmed)
            for p in set(phones):
                claims.append(EntityClaim(entity_type="phone", entity_value=p, source_page=url, context="Extracted via regex"))
            corps = re.findall(r'[A-Z][a-zA-Z0-9-]*\s+(?:LLC|Inc\.|Ltd\.|Corporation|Corp\.)', text_trimmed)
            for c in set(corps):
                claims.append(EntityClaim(entity_type="company", entity_value=c, source_page=url, context="Extracted via regex"))

        return claims'''

text = text.replace(old_block, new_block)

with open('veritas/agents/graph_investigator.py', 'w') as f:
    f.write(text)

print("Graph fallback patched!")
