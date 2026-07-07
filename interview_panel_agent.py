import asyncio
import os
import sys
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

# Load environment variables (like GEMINI_API_KEY) from global ~/.env or project .env
load_dotenv(os.path.expanduser("~/.env"))
load_dotenv()

def save_interview_report(report: str) -> str:
    """
    Saves the full interview report (transcript, panel debrief, verdict, coach notes) to interview_report.md.
    If the report contains harsh language above a threshold (2 or more instances of "weak", "poor", "failed", "not ready"),
    it prompts the developer for approval.

    Args:
        report: The detailed interview report in markdown format.
    """
    harsh_words = ["weak", "poor", "failed", "not ready"]
    harsh_count = sum(report.lower().count(w) for w in harsh_words)

    if harsh_count >= 2:
        print("\n[HUMAN REVIEW NEEDED] This feedback seems harsh. Approve showing this to the student? (yes/no)")
        choice = input().strip().lower()

        # Log decision to human_review_log.txt
        with open("human_review_log.txt", "a", encoding="utf-8") as f:
            f.write(f"Decision: {'approved' if choice == 'yes' else 'revised'}\n")
            f.write(f"Harsh Count: {harsh_count}\n")
            f.write(f"Report Excerpt:\n{report[:300]}...\n")
            f.write(f"{'-'*40}\n")

        if choice == 'yes':
            with open("interview_report.md", "w", encoding="utf-8") as f:
                f.write(report)
            return "Interview report successfully saved to interview_report.md."
        else:
            return (
                "Feedback rejected by developer due to harsh language. Please rewrite the feedback, "
                "especially the 'Coach Notes' or 'Final Verdict' sections, to soften the language and make "
                "it more constructive, encouraging, and supportive (avoiding words like 'weak', 'poor', 'failed', 'not ready')."
            )
    else:
        with open("interview_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        return "Interview report successfully saved to interview_report.md."

def log_guardrail_violation(inappropriate_question: str, reason: str) -> str:
    """
    Logs any generated question that violates safety guardrails (bias, discrimination, inappropriate topics)
    to guardrail_log.txt.

    Args:
        inappropriate_question: The draft question that was flagged and skipped.
        reason: The reason why the question is inappropriate or biased.
    """
    with open("guardrail_log.txt", "a", encoding="utf-8") as f:
        f.write(f"Flagged Question: '{inappropriate_question}'\nReason: {reason}\n{'-'*40}\n")
    return "Guardrail violation logged to guardrail_log.txt."

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please configure it in C:\\Users\\mansi\\.env or in a local .env file.", file=sys.stderr)
        sys.exit(1)

    system_instructions = (
        "You are InterviewPanelAgent, simulating a panel of three interviewers:\n"
        "1. Hiring Manager - focus on behavioral/ownership questions (1-2 questions).\n"
        "2. Peer Engineer - focus on technical questions relevant to the target role (1-2 questions), and push back with a skeptical follow-up on the candidate's initial answer.\n"
        "3. Exec - focus on company alignment and motivational questions (e.g. why this company/role).\n\n"
        "YOUR WORKFLOW:\n"
        "1. Start by asking the student for their target role and target company.\n"
        "2. Once provided, start the interview. Introduce each interviewer before they ask their question.\n"
        "3. The Hiring Manager asks behavioral questions first.\n"
        "4. Then, the Peer Engineer asks a technical question. Once the candidate answers, the Peer Engineer MUST push back skeptically (e.g. asking about trade-offs, edge cases, or questioning the tech choice) before asking their next question.\n"
        "5. The Exec finishes the interview with a 'why this company/role' question.\n\n"
        "SAFETY GUARDRAIL:\n"
        "Before asking any question, perform a safety check. If the question involves personal, biased, or inappropriate subjects "
        "(e.g., age, marital/family status, gender, religion, politics, or disability), you MUST immediately call the `log_guardrail_violation` tool, "
        "skip that question, and formulate a fair professional alternative instead.\n\n"
        "AFTER THE INTERVIEW:\n"
        "Once all questions are answered, compile a detailed report including:\n"
        "- Full Interview Transcript\n"
        "- Panel Debrief: A dialogue-based debate between Hiring Manager, Peer Engineer, and Exec evaluating the candidate (what each liked and doubted).\n"
        "- Final Verdict: Select from (Strong Hire / Hire / No Hire / Strong No Hire) with explanation.\n"
        "- Coach Notes: 2-3 specific, actionable tips for improvement.\n\n"
        "Finally, call the `save_interview_report` tool to save the report to interview_report.md, summarize the outcome to the candidate, and exit."
    )

    config = LocalAgentConfig(
        system_instructions=system_instructions,
        tools=[save_interview_report, log_guardrail_violation],
        capabilities=CapabilitiesConfig(enable_subagents=False, enabled_tools=[]),
        api_key=api_key,
        model="gemini-2.5-flash-lite"
    )

    async with Agent(config) as agent:
        print("\n--- Starting Interview Panel Agent ---")
        response = await agent.chat(
            "Hello! Let's conduct your mock panel interview. To help us customize the panel questions, "
            "what is your target job role and target company?"
        )
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
        print()

        while True:
            if os.path.exists("interview_report.md"):
                print("\n--- Interview complete and report saved! Exiting. ---")
                break

            try:
                user_input = input("\nYou: ")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break

            if not user_input.strip():
                continue

            response = await agent.chat(user_input)
            print()
            async for token in response:
                sys.stdout.write(token)
                sys.stdout.flush()
            print()

if __name__ == "__main__":
    asyncio.run(main())
