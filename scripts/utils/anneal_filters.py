"""
Self-Annealing Q&A Validation System using Claude Haiku.

This script validates extracted Q&A pairs using Claude Haiku API to:
1. Verify question identification accuracy
2. Check answer completeness
3. Validate Q&A pairing correctness
4. Calculate precision, recall, and F1 scores
5. Suggest filter improvements
6. Iterate until 95% accuracy is achieved
"""
import json
import random
import os
import argparse
from typing import List, Dict, Tuple
from anthropic import Anthropic

def load_config(path: str) -> dict:
    """Load configuration from JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def load_qa_dataset(path: str) -> List[Dict]:
    """Load Q&A dataset from JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def validate_qa_pair_with_claude(
    client: Anthropic,
    model: str,
    question: str,
    answer: str,
    source_file: str
) -> Dict:
    """
    Validate a single Q&A pair using Claude Haiku.
    
    Returns:
        {
            "is_valid_question": bool,
            "is_complete_answer": bool,
            "is_correctly_paired": bool,
            "confidence": float,
            "reasoning": str,
            "issues": List[str]
        }
    """
    prompt = f"""You are validating Q&A pairs extracted from YouTube transcripts of Ross Coulthart's Reality Check show.

SOURCE FILE: {source_file}

QUESTION:
{question[:500]}{"..." if len(question) > 500 else ""}

ANSWER:
{answer[:500] if answer else "[EMPTY ANSWER]"}{"..." if len(answer) > 500 else ""}

Please analyze this Q&A pair and respond in JSON format with:
{{
    "is_valid_question": true/false,  // Is this actually a moderator asking a question?
    "is_complete_answer": true/false, // Is the answer complete and relevant?
    "is_correctly_paired": true/false, // Do the Q and A match?
    "confidence": 0.0-1.0,            // Your confidence in this assessment
    "reasoning": "brief explanation",
    "issues": ["list", "of", "problems"] // Empty list if no issues
}}

VALIDATION CRITERIA:
- Valid questions: Start with moderator introducing viewer/email questions (e.g., "Here's a question from...", "Email from...")
- Invalid questions: Ross's responses that start with "That's a good question", "Look,", "Well,", etc.
- Complete answers: Ross's full response to the question, not cut off mid-sentence
- Correct pairing: The answer actually addresses the question asked

Respond ONLY with valid JSON, no other text."""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text.strip()
        
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        print(f"Error validating pair: {e}")
        return {
            "is_valid_question": False,
            "is_complete_answer": False,
            "is_correctly_paired": False,
            "confidence": 0.0,
            "reasoning": f"Validation error: {str(e)}",
            "issues": ["validation_failed"]
        }

def calculate_metrics(validation_results: List[Dict]) -> Dict:
    """
    Calculate precision, recall, and F1 score.
    
    Metrics:
    - Precision: % of extracted pairs that are actually valid
    - Recall: Estimated based on empty answers and issues
    - F1: Harmonic mean of precision and recall
    """
    total = len(validation_results)
    if total == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "accuracy": 0.0}
    
    # Count valid pairs (all three criteria must be true)
    valid_pairs = sum(
        1 for r in validation_results
        if r["is_valid_question"] and r["is_complete_answer"] and r["is_correctly_paired"]
    )
    
    # Precision: % of extracted pairs that are valid
    precision = valid_pairs / total
    
    # Recall estimation: Based on issues found
    # If we have empty answers or pairing issues, recall is lower
    empty_answers = sum(1 for r in validation_results if not r["is_complete_answer"])
    invalid_questions = sum(1 for r in validation_results if not r["is_valid_question"])
    
    # Estimate recall: assume we missed some questions if we have issues
    # This is a heuristic - true recall would require manual annotation
    recall_penalty = (empty_answers + invalid_questions) / total
    estimated_recall = max(0.0, 1.0 - recall_penalty)
    
    # F1 Score
    if precision + estimated_recall > 0:
        f1 = 2 * (precision * estimated_recall) / (precision + estimated_recall)
    else:
        f1 = 0.0
    
    # Overall accuracy (all criteria met)
    accuracy = precision
    
    return {
        "precision": round(precision, 3),
        "recall": round(estimated_recall, 3),
        "f1": round(f1, 3),
        "accuracy": round(accuracy, 3),
        "valid_pairs": valid_pairs,
        "total_pairs": total,
        "empty_answers": empty_answers,
        "invalid_questions": invalid_questions
    }

def analyze_failure_patterns(validation_results: List[Dict], qa_data: List[Dict]) -> Dict:
    """
    Analyze common failure patterns to suggest filter improvements.
    """
    issues_summary = {}
    false_positives = []  # Questions that aren't actually questions
    false_negatives = []  # Missed questions (indicated by empty answers)
    
    for i, result in enumerate(validation_results):
        qa_pair = qa_data[i]
        
        # Collect all issues
        for issue in result.get("issues", []):
            issues_summary[issue] = issues_summary.get(issue, 0) + 1
        
        # False positives: extracted as question but isn't
        if not result["is_valid_question"]:
            false_positives.append({
                "question": qa_pair["question"][:100],
                "reasoning": result["reasoning"]
            })
        
        # False negatives: empty or incomplete answers
        if not result["is_complete_answer"] and qa_pair["answer"]:
            false_negatives.append({
                "question": qa_pair["question"][:100],
                "answer": qa_pair["answer"][:100],
                "reasoning": result["reasoning"]
            })
    
    return {
        "issues_summary": issues_summary,
        "false_positives": false_positives[:5],  # Top 5 examples
        "false_negatives": false_negatives[:5],
        "total_false_positives": len(false_positives),
        "total_false_negatives": len(false_negatives)
    }

def suggest_filter_improvements(failure_patterns: Dict) -> List[str]:
    """
    Generate actionable filter improvement suggestions based on failure patterns.
    """
    suggestions = []
    
    fp_count = failure_patterns["total_false_positives"]
    fn_count = failure_patterns["total_false_negatives"]
    
    if fp_count > 0:
        suggestions.append(
            f"⚠️ Found {fp_count} false positives (non-questions marked as questions). "
            "Review negative patterns (Ross's answer starts) in extract_qa_pairs.py"
        )
        
        # Analyze false positive examples
        for fp in failure_patterns["false_positives"][:3]:
            suggestions.append(f"  Example FP: '{fp['question']}' - {fp['reasoning']}")
    
    if fn_count > 0:
        suggestions.append(
            f"⚠️ Found {fn_count} incomplete/missing answers. "
            "Review answer extraction logic to capture full responses."
        )
        
        for fn in failure_patterns["false_negatives"][:3]:
            suggestions.append(f"  Example FN: '{fn['question']}' - {fn['reasoning']}")
    
    if not suggestions:
        suggestions.append("✅ No major issues detected. Filters appear to be working well!")
    
    return suggestions

def main():
    parser = argparse.ArgumentParser(description="Self-Annealing Q&A Validation with Claude Haiku")
    parser.add_argument("--config", default="scraper_config.json", help="Config file path")
    parser.add_argument("--qa_file", default="qa_dataset.json", help="Q&A dataset file")
    parser.add_argument("--sample_size", type=int, help="Override sample size from config")
    parser.add_argument("--full", action="store_true", help="Validate entire dataset (ignore sample_size)")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    annealing_config = config.get("annealing", {})
    
    api_key = annealing_config.get("claude_api_key")
    if not api_key or api_key == "YOUR_API_KEY":
        print("❌ Error: Claude API key not configured in scraper_config.json")
        return
    
    model = annealing_config.get("model", "claude-3-haiku-20240307")
    sample_size = args.sample_size or annealing_config.get("sample_size", 50)
    target_accuracy = annealing_config.get("target_accuracy", 0.95)
    
    # Load Q&A dataset
    if not os.path.exists(args.qa_file):
        print(f"❌ Error: Q&A dataset not found at {args.qa_file}")
        return
    
    qa_data = load_qa_dataset(args.qa_file)
    print(f"📊 Loaded {len(qa_data)} Q&A pairs from {args.qa_file}")
    
    # Sample or use full dataset
    if args.full:
        sample = qa_data
        print(f"🔍 Validating FULL dataset ({len(sample)} pairs)")
    else:
        sample_size = min(sample_size, len(qa_data))
        sample = random.sample(qa_data, sample_size)
        print(f"🔍 Validating random sample of {sample_size} pairs")
    
    # Initialize Claude client
    client = Anthropic(api_key=api_key)
    
    # Validate each pair
    print(f"\n🤖 Using Claude model: {model}")
    print("=" * 80)
    
    validation_results = []
    for i, qa_pair in enumerate(sample, 1):
        print(f"[{i}/{len(sample)}] Validating pair from {qa_pair['source_file']}...", end=" ")
        
        result = validate_qa_pair_with_claude(
            client=client,
            model=model,
            question=qa_pair["question"],
            answer=qa_pair["answer"],
            source_file=qa_pair["source_file"]
        )
        
        validation_results.append(result)
        
        # Show result
        status = "✅" if all([
            result["is_valid_question"],
            result["is_complete_answer"],
            result["is_correctly_paired"]
        ]) else "❌"
        print(f"{status} (confidence: {result['confidence']:.2f})")
    
    print("=" * 80)
    
    # Calculate metrics
    metrics = calculate_metrics(validation_results)
    
    print("\n📈 VALIDATION METRICS:")
    print(f"  Accuracy:  {metrics['accuracy']:.1%} ({metrics['valid_pairs']}/{metrics['total_pairs']} pairs)")
    print(f"  Precision: {metrics['precision']:.1%}")
    print(f"  Recall:    {metrics['recall']:.1%} (estimated)")
    print(f"  F1 Score:  {metrics['f1']:.1%}")
    print(f"\n  Issues:")
    print(f"    - Empty/incomplete answers: {metrics['empty_answers']}")
    print(f"    - Invalid questions: {metrics['invalid_questions']}")
    
    # Analyze failure patterns
    failure_patterns = analyze_failure_patterns(validation_results, sample)
    
    print("\n🔍 FAILURE PATTERN ANALYSIS:")
    print(f"  False Positives: {failure_patterns['total_false_positives']}")
    print(f"  False Negatives: {failure_patterns['total_false_negatives']}")
    
    if failure_patterns["issues_summary"]:
        print(f"\n  Common Issues:")
        for issue, count in sorted(failure_patterns["issues_summary"].items(), key=lambda x: -x[1]):
            print(f"    - {issue}: {count}")
    
    # Generate improvement suggestions
    suggestions = suggest_filter_improvements(failure_patterns)
    
    print("\n💡 IMPROVEMENT SUGGESTIONS:")
    for suggestion in suggestions:
        print(f"  {suggestion}")
    
    # Check if target accuracy achieved
    print("\n" + "=" * 80)
    if metrics['accuracy'] >= target_accuracy:
        print(f"🎉 SUCCESS! Achieved {metrics['accuracy']:.1%} accuracy (target: {target_accuracy:.1%})")
        print("✅ Filters are performing well. No iteration needed.")
    else:
        gap = target_accuracy - metrics['accuracy']
        print(f"⚠️  Current accuracy: {metrics['accuracy']:.1%} (target: {target_accuracy:.1%})")
        print(f"📊 Gap to target: {gap:.1%}")
        print("\n🔄 NEXT STEPS:")
        print("  1. Review the improvement suggestions above")
        print("  2. Update filter patterns in extract_qa_pairs.py")
        print("  3. Re-run extraction: python extract_qa_pairs.py")
        print("  4. Re-run validation: python anneal_filters.py")
        print("  5. Repeat until target accuracy achieved")
    
    # Save detailed results
    output_file = "validation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "metrics": metrics,
            "failure_patterns": failure_patterns,
            "suggestions": suggestions,
            "validation_results": validation_results[:10]  # Save first 10 for review
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
