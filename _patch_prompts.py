import re

with open('veritas/config/dark_patterns.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: misdirected_click
content = content.replace(
    '"Respond in JSON: {\\"findings\\": [{\\"pair\\": [\\"button1\\", \\"button2\\"], \\"dominant\\": \\"button1\\", "\n                  "\\"size_ratio\\": 2.5, \\"contrast_difference\\": \\"high\\", \\"pattern_type\\": \\"misdirected_click\\", "\n                  "\\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}]}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"misdirected_click\\", \\"evidence\\": \\"button1 is 2.5x larger than button2\\", \\"confidence\\": 0.9}]}. If no such pattern exists, respond with {\\"findings\\": []}."'
)

# Pattern 2: hidden_unsubscribe
content = content.replace(
    '"Respond in JSON: {\\"findings\\": [{\\"element\\": \\"description\\", \\"issue\\": \\"low_contrast|tiny_size|hidden_position\\", "\n                  "\\"estimated_size\\": \\"8px\\", \\"pattern_type\\": \\"hidden_unsubscribe\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}]}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"hidden_unsubscribe\\", \\"evidence\\": \\"Unsubscribe link is 8px and low contrast\\", \\"confidence\\": 0.9}]}. If no such pattern exists, respond with {\\"findings\\": []}."'
)

# Pattern 3: disguised_ads
content = content.replace(
    '"Respond in JSON: {\\"findings\\": [{\\"element\\": \\"description\\", \\"pattern_type\\": \\"disguised_ads\\", "\n                  "\\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}]}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"disguised_ads\\", \\"evidence\\": \\"Ad styled exactly like site navigation\\", \\"confidence\\": 0.9}]}. If no such pattern exists, respond with {\\"findings\\": []}."'
)

# Pattern 4: fake_urgency timers
content = content.replace(
    '"Respond in JSON: {\\"timer_found\\": true/false, \\"timer_value\\": \\"exact text\\", "\n                  "\\"timer_location\\": \\"description of where on page\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"countdown_timer\\", \\"evidence\\": \\"Timer showing 04:59\\", \\"confidence\\": 0.9}]}. If no timer, respond with {\\"findings\\": []}."'
)

# Pattern 5: scarcity_found
content = content.replace(
    '"Respond in JSON: {\\"scarcity_found\\": true/false, \\"scarcity_text\\": \\"exact text\\", "\n                  "\\"scarcity_type\\": \\"stock|viewers|purchases|other\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"scarcity_indicator\\", \\"evidence\\": \\"Only 2 left in stock\\", \\"confidence\\": 0.9}]}. If no scarcity claims, respond with {\\"findings\\": []}."'
)

# Pattern 6: hidden_cancel
content = content.replace(
    '"Respond in JSON: {\\"cancel_visible\\": true/false, \\"cancel_prominence\\": \\"prominent|subtle|hidden\\", "\n                  "\\"estimated_steps\\": 1, \\"pattern_type\\": \\"hidden_cancel|none\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"hidden_cancel\\", \\"evidence\\": \\"Cancel option is obscured or requires multiple complex steps\\", \\"confidence\\": 0.9}]}. If this is just a homepage or if cancel is clearly visible, respond with {\\"findings\\": []}."'
)

# Pattern 7: guilt_language
content = content.replace(
    '"Respond in JSON: {\\"guilt_language_found\\": true/false, \\"phrases\\": [\\"exact phrases found\\"], "\n                  "\\"pattern_type\\": \\"guilt_tripping\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"guilt_tripping\\", \\"evidence\\": \\"Uses phrase: No thanks, I hate saving money\\", \\"confidence\\": 0.9}]}. If no guilt language, respond with {\\"findings\\": []}."'
)

# Pattern 8: pre_selected_found
content = content.replace(
    '"Respond in JSON: {\\"pre_selected_found\\": true/false, \\"items\\": [{\\"description\\": \\"what is pre-selected\\", "\n                  "\\"is_additional_cost\\": true/false}], \\"pattern_type\\": \\"pre_selected_options\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"pre_selected_options\\", \\"evidence\\": \\"Insurance add-on was already checked\\", \\"confidence\\": 0.9}]}. If no pre-selected options, respond with {\\"findings\\": []}."'
)

# Pattern 9: hidden_costs
content = content.replace(
    '"Respond in JSON: {\\"price_transparent\\": true/false, \\"displayed_price\\": \\"$X\\", "\n                  "\\"actual_total\\": \\"$Y or unknown\\", \\"hidden_fees\\": [\\"list of additional charges\\"], "\n                  "\\"pattern_type\\": \\"hidden_costs\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"hidden_costs\\", \\"evidence\\": \\"Displayed $10 but added $5 service fee later\\", \\"confidence\\": 0.9}]}. If pricing is transparent or irrelevant, respond with {\\"findings\\": []}."'
)

# Pattern 10: hidden_subscription
content = content.replace(
    '"Respond in JSON: {\\"free_claim\\": true/false, \\"requires_payment_info\\": true/false, "\n                  "\\"auto_renewal_disclosed\\": true/false, \\"disclosure_prominence\\": \\"prominent|subtle|hidden\\", "\n                  "\\"pattern_type\\": \\"hidden_subscription\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"hidden_subscription\\", \\"evidence\\": \\"Claims free trial but requires CC and hides auto-renewal\\", \\"confidence\\": 0.9}]}. If no hidden subscription tricks, respond with {\\"findings\\": []}."'
)

# Pattern 11: fake_reviews
content = content.replace(
    '"Respond in JSON: {\\"testimonials_found\\": true/false, \\"stock_photos_suspected\\": true/false, "\n                  "\\"uniform_ratings\\": true/false, \\"similar_writing_style\\": true/false, "\n                  "\\"pattern_type\\": \\"fake_reviews\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"fake_reviews\\", \\"evidence\\": \\"All 5-star reviews with obvious stock photos\\", \\"confidence\\": 0.9}]}. If reviews look genuine or are absent, respond with {\\"findings\\": []}."'
)

# Pattern 12: fake_badges
content = content.replace(
    '"Respond in JSON: {\\"badges_found\\": true/false, \\"badges\\": [{\\"name\\": \\"badge name\\", "\n                  "\\"appears_clickable\\": true/false, \\"appears_verifiable\\": true/false}], "\n                  "\\"pattern_type\\": \\"fake_badges\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"fake_badges\\", \\"evidence\\": \\"Norton logo is a static unclickable image\\", \\"confidence\\": 0.9}]}. If badges are verifiable or absent, respond with {\\"findings\\": []}."'
)

# Pattern 13: authority claims
content = content.replace(
    '"Respond in JSON: {\\"authority_claims\\": [{\\"claim\\": \\"text of claim\\", "\n                  "\\"verifiable\\": true/false}], \\"pattern_type\\": \\"unverifiable_authority\\", \\"confidence\\": \\"<0.0-1.0 estimated confidence>\\"}"',
    '"Respond in JSON: {\\"findings\\": [{\\"pattern_type\\": \\"unverifiable_authority\\", \\"evidence\\": \\"Claims 1M+ customers without proof\\", \\"confidence\\": 0.9}]}. If claims are reasonable/verified or absent, respond with {\\"findings\\": []}."'
)

with open('veritas/config/dark_patterns.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Rewrites completed!")
