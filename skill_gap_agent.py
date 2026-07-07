import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

# Load environment variables
load_dotenv(os.path.expanduser("~/.env"))
load_dotenv()

def save_skill_gap_report(report: str) -> str:
    """
    Saves the skill gap analysis report to skill_gap_report.md.
    """
    with open("skill_gap_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    return "Skill gap report successfully saved to skill_gap_report.md."

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        sys.exit(1)
        
    profile_data = {}
    if os.path.exists("student_profile.json"):
        try:
            with open("student_profile.json", "r") as f:
                profile_data = json.load(f)
        except Exception:
            pass

    # Format profile info for the agent
    profile_str = json.dumps(profile_data, indent=2) if profile_data else "None"
    system_instructions = (
        "You are SkillGapAgent, a specialized career coach and placement mentor.\n"
        "Your task is to analyze the student's current technical skills and identify gaps "
        "relative to their target roles and target companies.\n\n"
        f"STUDENT PROFILE:\n{profile_str}\n\n"
        "YOUR WORKFLOW:\n"
        "1. Check the student profile. If branch, target roles, or target companies are missing, ask for them. "
        "Otherwise, greet the student, confirm their targets, and ask them to list their current technical skills (e.g. languages, databases, frameworks, libraries).\n"
        "2. Once they provide their skills, compare them against requirements for their target roles at their target companies. "
        "Use specific, deep company-specific requirements (e.g. for Google, focus on strong DSA depth, memory management, scale; for startups, focus on fast development, full-stack, specific frameworks like React/Node; for finance, focus on low latency, concurrent programming, databases).\n"
        "3. Output a prioritized 'what to learn next' list (top 3-5 specific topics) ranked by importance for their specific target companies. Do NOT give generic advice.\n"
        "4. Call the `save_skill_gap_report` tool to save the Markdown report to skill_gap_report.md.\n"
        "5. Inform the student that the report is saved and conclude the conversation."
    )
    
    config = LocalAgentConfig(
        system_instructions=system_instructions,
        tools=[save_skill_gap_report],
        capabilities=CapabilitiesConfig(enable_subagents=False, enabled_tools=[]),
        api_key=api_key,
        model="gemini-2.5-flash-lite"
    )
    
    print("--- Starting Skill Gap Agent ---")
    async with Agent(config) as agent:
        # Initial greeting
        response = await agent.chat(
            "Hello! I am your Skill Gap Analysis mentor. Let's analyze your technical skills for your target role."
        )
        async for token in response:
            print(token, end="", flush=True)
        print()
        
        while True:
            if os.path.exists("skill_gap_report.md"):
                print("\n--- Skill Gap Analysis complete! Exiting. ---")
                break
                
            try:
                user_input = input("\nYou: ")
            except (KeyboardInterrupt, EOFError):
                break
                
            if not user_input.strip():
                continue
                
            response = await agent.chat(user_input)
            async for token in response:
                print(token, end="", flush=True)
            print()

if __name__ == "__main__":
    asyncio.run(main())
