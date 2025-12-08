#!/usr/bin/env python3
"""
Master orchestration script for Q&A extraction pipeline.

Runs the complete workflow:
1. Filter Q&A transcripts
2. Extract Q&A pairs using GPT-4o (batch)
3. Export to CSV
4. Upload to Supabase

This script coordinates all components and provides progress tracking.
"""
import argparse
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import time


class PipelineOrchestrator:
    """Orchestrates the Q&A extraction pipeline."""
    
    def __init__(self, run_config_path: str, global_config_path: str, dry_run: bool = False):
        self.run_config_path = run_config_path
        self.global_config_path = global_config_path
        self.dry_run = dry_run
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
        # Load run configuration (subject-specific)
        with open(run_config_path, 'r') as f:
            self.run_config = json.load(f)
        
        # Load global configuration (API keys, etc.)
        with open(global_config_path, 'r') as f:
            self.global_config = json.load(f)
        
        # Extract subject info
        self.subject_name = self.run_config["subject"]["name"]
        self.subject_id = self.run_config["subject"]["subject_id"]
        
        # Get API key from global config
        self.openai_api_key = (
            self.global_config.get("openai", {}).get("api_key") or 
            self.global_config.get("openai_api_key")
        )
        
        # Paths from run config
        source_cfg = self.run_config["source"]
        output_cfg = self.run_config["output"]
        
        self.transcripts_dir = self.project_root / source_cfg["base_transcripts_dir"]
        self.filtered_dir = self.project_root / output_cfg["filtered_dir"]
        self.outputs_dir = self.project_root / "outputs"
        self.qa_outputs_dir = self.project_root / output_cfg["extractions_dir"]
        self.csv_output = self.outputs_dir / output_cfg["csv_filename"]
        
        # Filter patterns from run config
        self.filter_patterns = self.run_config["filter"]["patterns"]
        self.filter_case_sensitive = self.run_config["filter"]["case_sensitive"]
        
        # Python interpreter (use venv if available)
        venv_python = self.project_root / ".venv" / "bin" / "python"
        self.python = str(venv_python) if venv_python.exists() else "python3"
        
        # Validate requirements
        self._validate()
    
    def _validate(self):
        """Validate configuration and requirements."""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found in global config")
        if not self.subject_id:
            raise ValueError("Subject ID not found in run config")
        if not self.transcripts_dir.exists():
            raise FileNotFoundError(f"Transcripts directory not found: {self.transcripts_dir}")
    
    def _run_command(self, cmd: List[str], description: str) -> Dict[str, Any]:
        """
        Run a shell command and track results.
        
        Args:
            cmd: Command and arguments as list
            description: Human-readable description
            
        Returns:
            Dict with status, output, and timing
        """
        print(f"\n{'='*80}")
        print(f"📍 {description}")
        print(f"{'='*80}")
        print(f"Command: {' '.join(cmd)}\n")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            
            elapsed = time.time() - start_time
            
            # Print output
            if result.stdout:
                print(result.stdout)
            
            print(f"\n✅ Completed in {elapsed:.1f}s")
            
            return {
                "success": True,
                "elapsed": elapsed,
                "output": result.stdout,
                "error": None
            }
            
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            
            print(f"❌ Failed after {elapsed:.1f}s")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            
            return {
                "success": False,
                "elapsed": elapsed,
                "output": e.stdout,
                "error": str(e)
            }
    
    def step1_filter_qa(self) -> Dict[str, Any]:
        """Step 1: Filter Q&A transcripts."""
        cmd = [
            self.python,
            "scripts/filter_qa_transcripts.py",
            "--source", str(self.transcripts_dir),
            "--target", str(self.filtered_dir)
        ]
        
        if self.dry_run:
            cmd.append("--dry-run")
        
        return self._run_command(cmd, "Step 1: Filter Q&A Transcripts")
    
    def step2_extract_qa(self, limit: int = None) -> Dict[str, Any]:
        """
        Step 2: Extract Q&A pairs using GPT-4o (batch).
        
        Args:
            limit: Optional limit on number of files to process
        """
        # Create output directory
        self.qa_outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Get filtered transcripts
        if not self.filtered_dir.exists():
            return {
                "success": False,
                "error": "Filtered directory doesn't exist. Run step 1 first."
            }
        
        transcripts = list(self.filtered_dir.glob("*.txt"))
        
        if limit:
            transcripts = transcripts[:limit]
        
        if not transcripts:
            return {
                "success": False,
                "error": f"No transcripts found in {self.filtered_dir}"
            }
        
        print(f"\n{'='*80}")
        print(f"📍 Step 2: Extract Q&A Pairs (GPT-4o Batch)")
        print(f"{'='*80}")
        print(f"Transcripts to process: {len(transcripts)}")
        if limit:
            print(f"(Limited to first {limit} files)")
        print()
        
        results = []
        total_cost = 0.0
        
        for i, transcript_file in enumerate(transcripts, 1):
            output_file = self.qa_outputs_dir / f"{transcript_file.stem}_qa.json"
            
            cmd = [
                self.python,
                "scripts/extract_qa_gpt4o.py",
                "--transcript", str(transcript_file),
                "--output", str(output_file),
                "--api-key", self.openai_api_key
            ]
            
            print(f"[{i}/{len(transcripts)}] {transcript_file.name}")
            
            if self.dry_run:
                print("   [DRY RUN] Would extract Q&A")
                results.append({"success": True, "file": transcript_file.name})
                continue
            
            # Run extraction
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse cost from output
                if "Cost:" in result.stdout:
                    cost_line = [l for l in result.stdout.split('\n') if "Cost:" in l][0]
                    cost = float(cost_line.split('$')[1].split()[0])
                    total_cost += cost
                
                results.append({
                    "success": True,
                    "file": transcript_file.name,
                    "output": output_file.name
                })
                print(f"   ✓ Extracted")
            else:
                print(f"   ✗ Failed: {result.stderr[:100]}")
                results.append({
                    "success": False,
                    "file": transcript_file.name,
                    "error": result.stderr
                })
        
        successful = sum(1 for r in results if r["success"])
        
        print(f"\n{'='*80}")
        print(f"✅ Extraction Complete")
        print(f"   Processed: {successful}/{len(transcripts)}")
        if not self.dry_run:
            print(f"   Total cost: ${total_cost:.2f}")
        print(f"{'='*80}")
        
        return {
            "success": successful > 0,
            "processed": len(transcripts),
            "successful": successful,
            "total_cost": total_cost,
            "results": results
        }
    
    def step3_export_csv(self) -> Dict[str, Any]:
        """Step 3: Export all JSON to CSV."""
        cmd = [
            self.python,
            "scripts/export_qa_csv.py",
            "--input", str(self.qa_outputs_dir),
            "--output", str(self.csv_output),
            "--subject-id", self.subject_id,
            "--batch"
        ]
        
        return self._run_command(cmd, "Step 3: Export to CSV")
    
    def step4_upload_supabase(self) -> Dict[str, Any]:
        """Step 4: Upload CSV to Supabase."""
        cmd = [
            self.python,
            "scripts/upload_to_supabase.py",
            "--config", self.global_config_path,
            "--input", str(self.csv_output)
        ]
        
        if self.dry_run:
            cmd.append("--dry-run")
        
        return self._run_command(cmd, "Step 4: Upload to Supabase")
    
    def run_full_pipeline(self, extract_limit: int = None) -> Dict[str, Any]:
        """
        Run the complete pipeline.
        
        Args:
            extract_limit: Optional limit on number of files to extract
            
        Returns:
            Summary of all steps
        """
        print("\n" + "="*80)
        print(f"🚀 Q&A EXTRACTION PIPELINE: {self.subject_name}")
        print("="*80)
        print(f"Run Config: {Path(self.run_config_path).name}")
        print(f"Global Config: {Path(self.global_config_path).name}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"Subject ID: {self.subject_id}")
        print(f"Transcripts: {self.transcripts_dir}")
        print(f"Outputs: {self.outputs_dir}")
        print("="*80)
        
        pipeline_start = time.time()
        summary = {}
        
        # Step 1: Filter
        summary["step1_filter"] = self.step1_filter_qa()
        if not summary["step1_filter"]["success"] and not self.dry_run:
            print("\n❌ Pipeline stopped: Step 1 failed")
            return summary
        
        # Step 2: Extract
        summary["step2_extract"] = self.step2_extract_qa(limit=extract_limit)
        if not summary["step2_extract"]["success"] and not self.dry_run:
            print("\n❌ Pipeline stopped: Step 2 failed")
            return summary
        
        # Step 3: Export CSV
        if not self.dry_run:
            summary["step3_csv"] = self.step3_export_csv()
            if not summary["step3_csv"]["success"]:
                print("\n❌ Pipeline stopped: Step 3 failed")
                return summary
        
        # Step 4: Upload
        if not self.dry_run:
            summary["step4_upload"] = self.step4_upload_supabase()
        
        pipeline_elapsed = time.time() - pipeline_start
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 PIPELINE COMPLETE")
        print("="*80)
        print(f"Total time: {pipeline_elapsed/60:.1f} minutes")
        
        if "step2_extract" in summary:
            print(f"Files processed: {summary['step2_extract'].get('processed', 0)}")
            print(f"Successful extractions: {summary['step2_extract'].get('successful', 0)}")
            if not self.dry_run:
                print(f"Total GPT-4o cost: ${summary['step2_extract'].get('total_cost', 0):.2f}")
        
        if not self.dry_run and "step4_upload" in summary:
            print("\n⚠️  Note: SQL generated - execute via MCP in AI assistant")
        
        print("="*80 + "\n")
        
        return summary


def load_run_config(args) -> tuple[str, str]:
    """
    Determine which run config to use based on arguments.
    
    Returns:
        tuple: (run_config_path, global_config_path)
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_runs_dir = project_root / "config_runs"
    
    # Check for named shortcuts (--ross, --lue, etc.)
    run_config_path = None
    
    if args.ross:
        run_config_path = config_runs_dir / "ross_coulthart.json"
    elif args.lue:
        run_config_path = config_runs_dir / "lue_elizondo.json"
    elif args.run_config:
        # Direct path to run config
        run_config_path = Path(args.run_config)
    
    if not run_config_path:
        raise ValueError(
            "No run config specified. Use --ross, --lue, or --run-config <path>"
        )
    
    if not run_config_path.exists():
        raise FileNotFoundError(f"Run config not found: {run_config_path}")
    
    # Global config path (API keys, etc.)
    global_config_path = project_root / args.global_config
    if not global_config_path.exists():
        raise FileNotFoundError(f"Global config not found: {global_config_path}")
    
    return str(run_config_path), str(global_config_path)


def main():
    parser = argparse.ArgumentParser(
        description="Run Q&A extraction pipeline (Filter → Extract → Export → Upload)",
        epilog="Examples:\n"
               "  python run_pipeline.py --ross                    # Process Ross Coulthart Q&As\n"
               "  python run_pipeline.py --ross --limit 2          # Test with 2 files\n"
               "  python run_pipeline.py --ross --dry-run          # Preview without API calls\n"
               "  python run_pipeline.py --run-config custom.json  # Use custom config\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Config selection (mutually exclusive)
    config_group = parser.add_mutually_exclusive_group()
    config_group.add_argument(
        "--ross",
        action="store_true",
        help="Use Ross Coulthart config (config_runs/ross_coulthart.json)"
    )
    config_group.add_argument(
        "--lue",
        action="store_true",
        help="Use Lue Elizondo config (config_runs/lue_elizondo.json)"
    )
    config_group.add_argument(
        "--run-config",
        type=str,
        help="Path to custom run config JSON"
    )
    
    parser.add_argument(
        "--global-config",
        default="scraper_config.json",
        help="Path to global config with API keys (default: scraper_config.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no API calls, no uploads)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of transcripts to process (for testing)"
    )
    parser.add_argument(
        "--step",
        choices=["filter", "extract", "csv", "upload", "all"],
        default="all",
        help="Run specific step only (default: all)"
    )
    
    args = parser.parse_args()
    
    # Show help if no config specified
    if not (args.ross or args.lue or args.run_config):
        parser.print_help()
        print("\n❌ Error: You must specify a run config (--ross, --lue, or --run-config)")
        sys.exit(1)
    
    try:
        # Load configs
        run_config_path, global_config_path = load_run_config(args)
        
        print(f"📋 Using run config: {Path(run_config_path).name}")
        print(f"🔑 Using global config: {global_config_path}\n")
        
        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            run_config_path,
            global_config_path,
            dry_run=args.dry_run
        )
        
        # Run pipeline
        if args.step == "all":
            orchestrator.run_full_pipeline(extract_limit=args.limit)
        elif args.step == "filter":
            orchestrator.step1_filter_qa()
        elif args.step == "extract":
            orchestrator.step2_extract_qa(limit=args.limit)
        elif args.step == "csv":
            orchestrator.step3_export_csv()
        elif args.step == "upload":
            orchestrator.step4_upload_supabase()
            
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
