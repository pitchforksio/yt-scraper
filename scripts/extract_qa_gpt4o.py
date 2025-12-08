#!/usr/bin/env python3
"""
Extract Q&A pairs using GPT-4o on full transcript (no chunking).
"""
import json
import time
from openai import OpenAI
from pathlib import Path
from typing import List, Dict, Any

def extract_with_gpt4o(transcript_path: str, api_key: str) -> Dict[str, Any]:
    """Extract Q&A pairs using GPT-4o on the entire transcript."""
    
    # Read transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    # Number lines
    lines = transcript_text.split('\n')
    numbered_lines = [f"L{i:04d}: {line}" for i, line in enumerate(lines)]
    transcript_numbered = '\n'.join(numbered_lines)
    
    prompt = f"""Extract ALL question-answer pairs from this Ross Coulthart Q&A transcript.

SPEAKER IDENTIFICATION:
- Lines starting with ">>" indicate a speaker change
- Moderator (Megan) introduces viewer questions and reads emails
- Ross Coulthart provides the answers
- A QUESTION starts when moderator says: "question from...", "email from...", "asks...", etc.
- An ANSWER is Ross's complete response until the NEXT question begins

EXTRACTION RULES:
1. Extract COMPLETE Q&A pairs only - don't fragment a single exchange
2. NO DUPLICATES - each Q&A pair should appear only once
3. Question range should include the FULL viewer question (not just moderator intro)
4. Answer range should include Ross's COMPLETE response (until next question starts)
5. Return line numbers as INTEGERS ONLY (not L0001, just 1)
6. Question MUST come BEFORE answer (q_end < a_start)

WHAT TO SKIP:
- Conversational greetings ("Hello, how are you?")
- Brief clarifications or interruptions
- Closing remarks

Here is the transcript with line numbers:

{transcript_numbered}

CRITICAL: If a viewer asks MULTIPLE questions in one message, split them into SEPARATE Q&A pairs.

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "pairs": [
    {{
      "q_lines": [questionStartLine, questionEndLine],
      "a_lines": [answerStartLine, answerEndLine],
      "concise_question": "Viewer: [concise rephrasing of the question]",
      "concise_answer": "Ross: [concise rephrasing of the answer]",
      "confidence": 0.9
    }}
  ]
}}

IMPORTANT FORMAT RULES:
- concise_question: Start with "Viewer:" then rephrase the question concisely (not a summary)
- concise_answer: Start with "Ross:" then rephrase the answer concisely (not a summary)
- Keep the speaker's voice and key details
- If one viewer message has 2 questions, create 2 separate pairs with corresponding answer portions

Example:
{{
  "pairs": [
    {{
      "q_lines": [59, 65],
      "a_lines": [72, 100],
      "concise_question": "Viewer: Why is there a delay in the film release?",
      "concise_answer": "Ross: The delays were due to securing interviews and updates from whistleblowers.",
      "confidence": 0.9
    }},
    {{
      "q_lines": [66, 71],
      "a_lines": [101, 149],
      "concise_question": "Viewer: Does the film discuss cover-ups of harm caused by the phenomena?",
      "concise_answer": "Ross: Yes, the film addresses the lengths some have gone to cover up cases where humans were harmed.",
      "confidence": 0.9
    }}
  ]
}}

Set confidence 0.9 for clear Q&A pairs, 0.7 for uncertain ones."""
    
    client = OpenAI(api_key=api_key)
    
    start_time = time.time()
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an extraction engine. Extract Q&A pairs and return only JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    processing_time = time.time() - start_time
    
    # Parse response
    result_text = response.choices[0].message.content
    result = json.loads(result_text)
    
    # Add metadata
    tokens_used = response.usage.total_tokens
    
    return {
        "pairs": result.get("pairs", []),
        "metadata": {
            "model": "gpt-4o",
            "total_pairs": len(result.get("pairs", [])),
            "total_tokens": tokens_used,
            "processing_time": processing_time,
            "cost_estimate": tokens_used * 0.000005  # $5 per 1M tokens (rough estimate)
        }
    }

def reconstruct_text(lines: List[str], start: int, end: int) -> str:
    """Reconstruct text from line range."""
    return ' '.join(lines[start:end+1])

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--transcript', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--api-key', required=True)
    args = parser.parse_args()
    
    print(f"📄 Processing: {args.transcript}")
    print(f"🤖 Model: gpt-4o (full transcript)")
    print("=" * 80)
    
    # Extract
    result = extract_with_gpt4o(args.transcript, args.api_key)
    
    # Read original lines for text reconstruction
    with open(args.transcript, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
    
    # Reconstruct full Q&A pairs
    final_pairs = []
    for pair in result["pairs"]:
        if pair.get("q_lines") and pair.get("a_lines"):
            q_start, q_end = pair["q_lines"]
            a_start, a_end = pair["a_lines"]
            
            question = reconstruct_text(lines, q_start, q_end)
            answer = reconstruct_text(lines, a_start, a_end)
            
            final_pairs.append({
                "question": question,
                "answer": answer,
                "concise_question": pair.get("concise_question", ""),
                "concise_answer": pair.get("concise_answer", ""),
                "q_lines": pair["q_lines"],
                "a_lines": pair["a_lines"],
                "confidence": pair.get("confidence", 0.9),
                "source": "gpt4o_full"
            })
    
    # Save
    output_data = {
        "pairs": final_pairs,
        "metadata": result["metadata"]
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Extracted {len(final_pairs)} pairs")
    print(f"💰 Cost: ${result['metadata']['cost_estimate']:.4f}")
    print(f"⏱️  Time: {result['metadata']['processing_time']:.1f}s")
    print(f"💾 Saved to: {args.output}")

if __name__ == "__main__":
    main()
