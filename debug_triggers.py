from extract_qa_pairs import is_moderator_question_block

test_strings = [
    ">> You're absolutely right. Uh I his story is important. I met Dr. Gregory Rogers very briefly at Contact in the Desert in May this year.",
    ">> Fantastic. Absolutely fantastic. And uh are you going to hit me some questions first or you going to tell me about your holiday?",
    ">> That's what irritates me about this whole subject. Why is it a fun question when, as the age of disclosure demonstrated...",
    ">> Okay. Hi Russ and Megan. Great show. I never miss it and keep up the great work. Question. I know from listening...",
    ">> Actually, I have exchanged messages with Tim Alberino and he is on my list."
]

print("--- DEBUGGING STRINGS ---")
for s in test_strings:
    is_q, reason = is_moderator_question_block(s)
    print(f"\nString: {s[:50]}...")
    print(f"Is Question: {is_q}")
    print(f"Reason: {reason}")
