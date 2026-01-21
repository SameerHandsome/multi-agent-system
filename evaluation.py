"""
Evaluation Script for Multi-Agent System
Metrics: Task Success Rate, Tool Recall, Instruction Following
"""

import json
from typing import List, Dict
from multi_agent_system import run_agent_system
from datetime import datetime


class AgentEvaluator:
    """Evaluates multi-agent system performance"""
    
    def __init__(self):
        self.results = []
        
    def evaluate_task_success_rate(self, test_cases: List[Dict]) -> float:
        """
        Evaluate Task Success Rate
        Measures how many tasks complete without errors
        """
        print("\n" + "="*60)
        print("📊 EVALUATING TASK SUCCESS RATE")
        print("="*60)
        
        successful_tasks = 0
        total_tasks = len(test_cases)
        
        for idx, test_case in enumerate(test_cases):
            print(f"\n[{idx+1}/{total_tasks}] Testing: {test_case['query'][:50]}...")
            
            try:
                result = run_agent_system(test_case['query'])
                final_output = json.loads(result.get("final_output", "{}"))
                
                # Check if task completed successfully
                has_output = bool(final_output.get("researcher_output") or final_output.get("coder_output"))
                quality_score = final_output.get("quality_score", 0.0)
                
                if has_output and quality_score > 0.5:
                    successful_tasks += 1
                    status = "✅ SUCCESS"
                else:
                    status = "❌ FAILED"
                
                self.results.append({
                    "test_case": test_case['query'],
                    "success": has_output and quality_score > 0.5,
                    "quality_score": quality_score,
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"   {status} - Quality Score: {quality_score:.2f}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                self.results.append({
                    "test_case": test_case['query'],
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        success_rate = (successful_tasks / total_tasks) * 100
        print(f"\n📈 Task Success Rate: {success_rate:.2f}% ({successful_tasks}/{total_tasks})")
        return success_rate
    
    def evaluate_tool_recall(self, test_cases: List[Dict]) -> float:
        """
        Evaluate Tool Recall
        Measures if correct tools are called for appropriate tasks
        """
        print("\n" + "="*60)
        print("🔧 EVALUATING TOOL RECALL")
        print("="*60)
        
        correct_tool_usage = 0
        total_tool_tests = len(test_cases)
        
        for idx, test_case in enumerate(test_cases):
            print(f"\n[{idx+1}/{total_tool_tests}] Testing: {test_case['query'][:50]}...")
            expected_tools = test_case.get('expected_tools', [])
            
            try:
                result = run_agent_system(test_case['query'])
                final_output = json.loads(result.get("final_output", "{}"))
                
                # Check which agents were used
                used_researcher = bool(final_output.get("researcher_output"))
                used_coder = bool(final_output.get("coder_output"))
                
                # Map agents to tools
                tools_used = []
                if used_researcher:
                    tools_used.append("researcher")
                if used_coder:
                    tools_used.append("coder")
                
                # Check if expected tools were used
                tools_match = all(tool in tools_used for tool in expected_tools)
                
                if tools_match:
                    correct_tool_usage += 1
                    print(f"   ✅ Correct tools used: {tools_used}")
                else:
                    print(f"   ❌ Expected {expected_tools}, got {tools_used}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        tool_recall = (correct_tool_usage / total_tool_tests) * 100
        print(f"\n📈 Tool Recall: {tool_recall:.2f}% ({correct_tool_usage}/{total_tool_tests})")
        return tool_recall
    
    def evaluate_instruction_following(self, test_cases: List[Dict]) -> float:
        """
        Evaluate Instruction Following
        Measures if outputs match expected format and requirements
        """
        print("\n" + "="*60)
        print("📝 EVALUATING INSTRUCTION FOLLOWING")
        print("="*60)
        
        correct_instructions = 0
        total_instruction_tests = len(test_cases)
        
        for idx, test_case in enumerate(test_cases):
            print(f"\n[{idx+1}/{total_instruction_tests}] Testing: {test_case['query'][:50]}...")
            requirements = test_case.get('requirements', [])
            
            try:
                result = run_agent_system(test_case['query'])
                final_output = json.loads(result.get("final_output", "{}"))
                
                # Check requirements
                requirements_met = 0
                total_requirements = len(requirements)
                
                for req in requirements:
                    if req == "has_plan":
                        if final_output.get("plan", {}).get("tasks"):
                            requirements_met += 1
                            print(f"   ✅ Has plan")
                        else:
                            print(f"   ❌ Missing plan")
                    
                    elif req == "has_research":
                        if final_output.get("researcher_output"):
                            requirements_met += 1
                            print(f"   ✅ Has research output")
                        else:
                            print(f"   ❌ Missing research")
                    
                    elif req == "has_code":
                        output = final_output.get("coder_output", "")
                        if "```" in output or "def " in output or "class " in output:
                            requirements_met += 1
                            print(f"   ✅ Has code")
                        else:
                            print(f"   ❌ Missing code")
                    
                    elif req == "quality_score":
                        score = final_output.get("quality_score", 0.0)
                        if score >= 0.6:
                            requirements_met += 1
                            print(f"   ✅ Quality score: {score:.2f}")
                        else:
                            print(f"   ❌ Low quality score: {score:.2f}")
                
                if total_requirements > 0 and requirements_met == total_requirements:
                    correct_instructions += 1
                    print(f"   ✅ All requirements met ({requirements_met}/{total_requirements})")
                else:
                    print(f"   ❌ Requirements met: {requirements_met}/{total_requirements}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        instruction_rate = (correct_instructions / total_instruction_tests) * 100
        print(f"\n📈 Instruction Following: {instruction_rate:.2f}% ({correct_instructions}/{total_instruction_tests})")
        return instruction_rate
    
    def save_results(self, filename: str = "evaluation_results.json"):
        """Save evaluation results to file"""
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results
            }, f, indent=2)
        print(f"\n💾 Results saved to {filename}")


def run_evaluation():
    """Run full evaluation suite"""
    
    evaluator = AgentEvaluator()
    
    # Test cases for Task Success Rate
    success_test_cases = [
        {"query": "What is the capital of France?"},
        {"query": "Write a Python function to calculate factorial"},
        {"query": "Research latest AI developments"},
        {"query": "Create a simple calculator in Python"},
        {"query": "Explain quantum computing"}
    ]
    
    # Test cases for Tool Recall
    tool_recall_cases = [
        {
            "query": "Research the latest developments in AI",
            "expected_tools": ["researcher"]
        },
        {
            "query": "Write a Python script to sort a list",
            "expected_tools": ["coder"]
        },
        {
            "query": "Research AI agents and write a Python example",
            "expected_tools": ["researcher", "coder"]
        },
        {
            "query": "What is machine learning?",
            "expected_tools": ["researcher"]
        },
        {
            "query": "Create a function to reverse a string",
            "expected_tools": ["coder"]
        }
    ]
    
    # Test cases for Instruction Following
    instruction_cases = [
        {
            "query": "Research AI and write code example",
            "requirements": ["has_plan", "has_research", "has_code", "quality_score"]
        },
        {
            "query": "Explain neural networks",
            "requirements": ["has_plan", "has_research", "quality_score"]
        },
        {
            "query": "Write a Python class for a stack",
            "requirements": ["has_plan", "has_code", "quality_score"]
        }
    ]
    
    print("\n" + "="*60)
    print("🚀 STARTING MULTI-AGENT EVALUATION")
    print("="*60)
    
    # Run evaluations
    task_success_rate = evaluator.evaluate_task_success_rate(success_test_cases)
    tool_recall = evaluator.evaluate_tool_recall(tool_recall_cases)
    instruction_following = evaluator.evaluate_instruction_following(instruction_cases)
    
    # Final Summary
    print("\n" + "="*60)
    print("📊 FINAL EVALUATION SUMMARY")
    print("="*60)
    print(f"Task Success Rate:      {task_success_rate:.2f}%")
    print(f"Tool Recall:            {tool_recall:.2f}%")
    print(f"Instruction Following:  {instruction_following:.2f}%")
    print(f"Overall Score:          {(task_success_rate + tool_recall + instruction_following) / 3:.2f}%")
    print("="*60)
    
    # Save results
    evaluator.save_results()
    
    return {
        "task_success_rate": task_success_rate,
        "tool_recall": tool_recall,
        "instruction_following": instruction_following,
        "overall_score": (task_success_rate + tool_recall + instruction_following) / 3
    }


if __name__ == "__main__":
    run_evaluation()