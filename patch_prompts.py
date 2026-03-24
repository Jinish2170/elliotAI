import re

def main():
    with open("veritas/config/dark_patterns.py", "r") as f:
        content = f.read()

    # Change confidence to be a placeholder so the LLM has to calculate it instead of copying 0.85
    content = re.sub(r'confidence\\\": 0\.\d+', r'confidence\": 0.0', content)

    # Change the cancel_visible prompt to be context aware
    old_cancel_prompt = '"Is there a clearly visible \'Cancel\', \'Unsubscribe\', or \'Delete Account\' option on this page? "'
    new_cancel_prompt = '"If this is an account settings or subscription page, is there a clearly visible \'Cancel\' option? (If this is just a homepage or info page, assume cancel_visible is true). "'
    content = content.replace(old_cancel_prompt, new_cancel_prompt)

    # Change the price_transparent prompt to be context aware
    old_price_prompt = '"Is the total price clearly visible on this page? Are there any additional fees, charges, "'
    new_price_prompt = '"If this is a product, pricing, or checkout page, is the total price transparent? (If no prices are expected here like a homepage, assume price_transparent is true). "'
    content = content.replace(old_price_prompt, new_price_prompt)

    with open("veritas/config/dark_patterns.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()