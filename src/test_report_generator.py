#!/usr/bin/env python3
"""
Test Report Generator for Creative Automation Pipeline.
Generates timestamped .md reports for test executions.
"""

import os
import sys
import subprocess
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import timestamp utilities
try:
    from timestamp_utils import get_timestamp, get_timestamped_filename
except ImportError:
    # Fallback for direct execution
    from .timestamp_utils import get_timestamp, get_timestamped_filename


class TestReportGenerator:
    """
    Generates markdown test reports from test executions.
    """
    
    def __init__(self, test_reports_dir: str = "../test_reports"):
        """
        Initialize test report generator.
        
        Args:
            test_reports_dir: Directory to store test reports
        """
        self.test_reports_dir = os.path.abspath(test_reports_dir)
        os.makedirs(self.test_reports_dir, exist_ok=True)
        
        # Test status tracking
        self.test_results = {
            "checks": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "start_time": None,
            "end_time": None
        }
    
    def start_test(self, test_name: str, test_suite: str = "automated"):
        """
        Start a new test run.
        
        Args:
            test_name: Name of the test
            test_suite: Test suite identifier
        """
        self.test_name = test_name
        self.test_suite = test_suite
        self.test_results = {
            "checks": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "start_time": datetime.now(),
            "end_time": None,
            "test_output": "",
            "environment": self._get_environment_info()
        }
    
    def add_check(self, description: str, passed: bool, details: str = ""):
        """
        Add a check result to the test.
        
        Args:
            description: Check description
            passed: True if check passed, False if failed
            details: Additional details about the check
        """
        check = {
            "description": description,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["checks"].append(check)
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
    
    def add_warning(self, description: str, details: str = ""):
        """
        Add a warning (non-critical failure) to the test.
        
        Args:
            description: Warning description
            details: Additional details
        """
        check = {
            "description": description,
            "passed": False,
            "details": details,
            "is_warning": True,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["checks"].append(check)
        self.test_results["warnings"] += 1
    
    def capture_output(self, output: str):
        """
        Capture test output for inclusion in report.
        
        Args:
            output: Test output text
        """
        self.test_results["test_output"] = output
    
    def end_test(self):
        """End the current test run."""
        self.test_results["end_time"] = datetime.now()
    
    def generate_report(self) -> str:
        """
        Generate markdown report from test results.
        
        Returns:
            Path to generated report file
        """
        # Calculate duration
        start_time = self.test_results["start_time"]
        end_time = self.test_results["end_time"] or datetime.now()
        duration = end_time - start_time
        
        # Generate report filename
        safe_test_name = self.test_name.lower().replace(" ", "_")
        filename = get_timestamped_filename(
            f"test_report_{safe_test_name}",
            "md",
            True,
            "file"
        )
        report_path = os.path.join(self.test_reports_dir, filename)
        
        # Prepare template variables
        total_checks = len(self.test_results["checks"])
        passed_count = self.test_results["passed"]
        failed_count = self.test_results["failed"]
        warning_count = self.test_results["warnings"]
        
        success_rate = 0
        if total_checks > 0:
            success_rate = int((passed_count / total_checks) * 100)
        
        # Determine overall status
        if failed_count == 0 and warning_count == 0:
            status = "✅ PASSED"
            status_icon = "✅"
        elif failed_count == 0 and warning_count > 0:
            status = "⚠️  PASSED WITH WARNINGS"
            status_icon = "⚠️"
        else:
            status = "❌ FAILED"
            status_icon = "❌"
        
        # Generate check results table
        check_table = "| Check | Status | Details |\n"
        check_table += "|-------|--------|---------|\n"
        
        for check in self.test_results["checks"]:
            check_desc = check["description"]
            check_status = "✅ PASS" if check.get("passed") else ("⚠️  WARNING" if check.get("is_warning") else "❌ FAIL")
            check_details = check.get("details", "")
            
            # Truncate long details
            if len(check_details) > 100:
                check_details = check_details[:97] + "..."
            
            check_table += f"| {check_desc} | {check_status} | {check_details} |\n"
        
        # Generate issues list
        issues = []
        for check in self.test_results["checks"]:
            if not check.get("passed") and not check.get("is_warning"):
                issues.append(f"- ❌ {check['description']}: {check.get('details', 'No details')}")
            elif check.get("is_warning"):
                issues.append(f"- ⚠️  {check['description']}: {check.get('details', 'No details')}")
        
        issues_list = "\n".join(issues) if issues else "No critical issues found."
        
        # Generate output files list (if any)
        output_files = []
        for item in os.listdir(self.test_reports_dir):
            if item.endswith(".json") or item.endswith(".log"):
                output_files.append(f"- {item}")
        
        output_files_list = "\n".join(output_files) if output_files else "No output files generated."
        
        # Read template
        template_path = os.path.join(self.test_reports_dir, "TEST_REPORT_TEMPLATE.md")
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            template = self._get_default_template()
        
        # Replace template variables
        report_content = template.replace("{TEST_NAME}", self.test_name)
        report_content = report_content.replace("{TEST_SUITE}", self.test_suite)
        report_content = report_content.replace("{TIMESTAMP_HUMAN}", get_timestamp("human", True))
        report_content = report_content.replace("{STATUS_ICON}", status_icon)
        report_content = report_content.replace("{STATUS}", status)
        report_content = report_content.replace("{DURATION}", str(duration))
        report_content = report_content.replace("{TOTAL_CHECKS}", str(total_checks))
        report_content = report_content.replace("{PASSED_COUNT}", str(passed_count))
        report_content = report_content.replace("{FAILED_COUNT}", str(failed_count))
        report_content = report_content.replace("{SUCCESS_RATE}", str(success_rate))
        report_content = report_content.replace("{CHECK_RESULTS_TABLE}", check_table)
        report_content = report_content.replace("{TEST_OUTPUT}", self.test_results.get("test_output", ""))
        report_content = report_content.replace("{SYSTEM_INFO}", self.test_results["environment"]["system"])
        report_content = report_content.replace("{PYTHON_VERSION}", self.test_results["environment"]["python_version"])
        report_content = report_content.replace("{SCRIPT_DIR}", self.test_results["environment"]["script_dir"])
        report_content = report_content.replace("{WORKING_DIR}", self.test_results["environment"]["working_dir"])
        report_content = report_content.replace("{OUTPUT_FILES_LIST}", output_files_list)
        report_content = report_content.replace("{ISSUES_LIST}", issues_list)
        
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Save results as JSON for programmatic access
        json_path = report_path.replace(".md", ".json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "test_name": self.test_name,
                "test_suite": self.test_suite,
                "timestamp": get_timestamp("human", True),
                "duration_seconds": duration.total_seconds(),
                "results": self.test_results,
                "report_path": report_path
            }, f, indent=2, default=str)
        
        return report_path
    
    def _get_environment_info(self) -> Dict:
        """Get environment information for the report."""
        import platform
        
        return {
            "system": platform.system(),
            "system_version": platform.version(),
            "python_version": sys.version.split()[0],
            "script_dir": os.path.dirname(os.path.abspath(__file__)),
            "working_dir": os.getcwd(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_default_template(self) -> str:
        """Get default report template."""
        return """# Test Report: {TEST_NAME}

**Generated:** {TIMESTAMP_HUMAN}  
**Test Suite:** {TEST_SUITE}  
**Status:** {STATUS_ICON} {STATUS}

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| **Test Duration** | {DURATION} |
| **Total Checks** | {TOTAL_CHECKS} |
| **Passed** | {PASSED_COUNT} |
| **Failed** | {FAILED_COUNT} |
| **Success Rate** | {SUCCESS_RATE}% |

## 🧪 Test Results

{CHECK_RESULTS_TABLE}

## 📝 Detailed Logs

```bash
{TEST_OUTPUT}
```

## 🔍 Environment Information

- **System:** {SYSTEM_INFO}
- **Python Version:** {PYTHON_VERSION}
- **Script Directory:** {SCRIPT_DIR}
- **Working Directory:** {WORKING_DIR}

## 📁 Output Files

{OUTPUT_FILES_LIST}

## 🚨 Issues & Recommendations

{ISSUES_LIST}

---

*Report generated by Creative Automation Pipeline Test Suite*  
*Version: 2.0 (Timestamp Standardization)*"""
    
    def run_test_command(self, command: str, test_name: str = None) -> Tuple[bool, str]:
        """
        Run a shell command and generate a test report.
        
        Args:
            command: Shell command to execute
            test_name: Name for the test (defaults to command)
            
        Returns:
            Tuple of (success, report_path)
        """
        if test_name is None:
            test_name = command.split()[0] if command.split() else "unknown_test"
        
        self.start_test(test_name, "shell_command")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = time.time()
            duration = end_time - start_time
            
            # Capture output
            output = f"Command: {command}\n"
            output += f"Exit Code: {result.returncode}\n"
            output += f"Duration: {duration:.2f}s\n\n"
            output += "=== STDOUT ===\n"
            output += result.stdout + "\n"
            output += "=== STDERR ===\n"
            output += result.stderr
            
            self.capture_output(output)
            
            # Add checks based on exit code
            if result.returncode == 0:
                self.add_check("Command executed successfully", True, f"Exit code: {result.returncode}")
                # Parse output for additional checks
                self._parse_output_for_checks(result.stdout)
            else:
                self.add_check("Command execution failed", False, f"Exit code: {result.returncode}")
                self.add_check("Error output captured", True, f"See stderr in logs")
            
            self.end_test()
            report_path = self.generate_report()
            
            return (result.returncode == 0, report_path)
            
        except subprocess.TimeoutExpired:
            self.add_check("Command execution timed out", False, "Timeout after 300 seconds")
            self.capture_output(f"Command timed out: {command}")
            self.end_test()
            report_path = self.generate_report()
            return (False, report_path)
        
        except Exception as e:
            self.add_check("Command execution failed with exception", False, str(e))
            self.capture_output(f"Exception running command: {command}\nError: {e}")
            self.end_test()
            report_path = self.generate_report()
            return (False, report_path)
    
    def _parse_output_for_checks(self, output: str):
        """
        Parse command output to extract check results.
        Looks for common patterns like ✅, ❌, ✓, ✗, PASS, FAIL, etc.
        """
        lines = output.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Look for success indicators
            if '✅' in line or '✓' in line or 'pass' in line_lower or 'success' in line_lower:
                if 'test' in line_lower or 'check' in line_lower:
                    self.add_check(f"Output check: {line.strip()[:50]}", True)
            
            # Look for failure indicators
            elif '❌' in line or '✗' in line or 'fail' in line_lower or 'error' in line_lower:
                if 'test' in line_lower or 'check' in line_lower:
                    self.add_check(f"Output check: {line.strip()[:50]}", False)


def generate_test_report_from_command(command: str, test_name: str = None) -> Tuple[bool, str]:
    """
    Convenience function to run a command and generate a test report.
    
    Args:
        command: Shell command to execute
        test_name: Name for the test
        
    Returns:
        Tuple of (success, report_path)
    """
    generator = TestReportGenerator()
    return generator.run_test_command(command, test_name)


def main():
    """Test the test report generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Report Generator")
    parser.add_argument("--command", help="Command to test and generate report for")
    parser.add_argument("--test-name", help="Name for the test")
    parser.add_argument("--list-reports", action="store_true", help="List existing test reports")
    
    args = parser.parse_args()
    
    generator = TestReportGenerator()
    
    if args.list_reports:
        reports_dir = generator.test_reports_dir
        print(f"Test reports in: {reports_dir}")
        
        for filename in sorted(os.listdir(reports_dir)):
            if filename.endswith(".md"):
                report_path = os.path.join(reports_dir, filename)
                with open(report_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                print(f"  {filename}: {first_line}")
    
    elif args.command:
        print(f"Running command: {args.command}")
        success, report_path = generator.run_test_command(args.command, args.test_name)
        
        if success:
            print(f"✅ Test completed successfully")
        else:
            print(f"❌ Test failed")
        
        print(f"Report generated: {report_path}")
        
        # Show summary
        json_path = report_path.replace(".md", ".json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"\nSummary:")
                print(f"  Test: {data['test_name']}")
                print(f"  Duration: {data['duration_seconds']:.2f}s")
                print(f"  Checks: {len(data['results']['checks'])}")
                print(f"  Passed: {data['results']['passed']}")
                print(f"  Failed: {data['results']['failed']}")
    
    else:
        # Run a simple test
        print("Running sample test...")
        generator.start_test("Sample Test", "demonstration")
        
        generator.add_check("Python version check", True, f"Python {sys.version.split()[0]}")
        generator.add_check("Import test: timestamp_utils", True, "Module imported successfully")
        generator.add_check("Report directory exists", os.path.exists(generator.test_reports_dir), 
                          f"Directory: {generator.test_reports_dir}")
        
        # Simulate a warning
        generator.add_warning("Sample warning", "This is a demonstration warning")
        
        generator.capture_output("Sample test output\nLine 1\nLine 2\n✅ All checks passed")
        generator.end_test()
        
        report_path = generator.generate_report()
        print(f"✅ Sample test report generated: {report_path}")


if __name__ == "__main__":
    main()