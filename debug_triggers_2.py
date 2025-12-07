from extract_qa_pairs import is_moderator_question_block

# Test the new triggers specifically
test_strings = [
    ">> Wow. Gee, I wish I could just dial me up a billionaire.",
    ">> Right. So she's not talking about Age of Disclosure...",
    ">> You're absolutely right. Uh I his story is important.",
    ">> That's a really interesting question. It's funny.",
]

print("--- DEBUGGING NEW TRIGGERS ---")
for s in test_strings:
    is_q, reason = is_moderator_question_block(s)
    print(f"\nString: {s[:50]}...")
    print(f"Is Question: {is_q}")
    print(f"Reason: {reason}")
