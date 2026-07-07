import asyncio
import os
import json
import sys
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

# Load environment variables from global ~/.env or project-local .env
load_dotenv(os.path.expanduser("~/.env"))
load_dotenv()

def save_student_profile(
    branch: str,
    year: str,
    target_job_roles: list[str],
    target_companies: list[str],
    weakness: str
) -> str:
    """
    Saves the collected student profile details to student_profile.json.

    Args:
        branch: The student's engineering/study branch (e.g. Computer Science).
        year: The academic year (e.g. 3rd year).
        target_job_roles: A list of target job roles the student is aiming for.
        target_companies: A list of companies the student is targeting.
        weakness: What the student feels weak at (e.g. "I freeze during interviews").
    """
    profile = {
        "branch": branch,
        "year": year,
        "target_job_roles": target_job_roles,
        "target_companies": target_companies,
        "weakness": weakness
    }
    with open("student_profile.json", "w") as f:
        json.dump(profile, f, indent=4)
    return "Profile saved successfully."

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please configure it in C:\\Users\\mansi\\.env or in a local .env file.", file=sys.stderr)
        sys.exit(1)

    system_instructions = (
        "You are ProfileAgent, a helpful AI placement mentor.\n"
        "Your sole task is to gather these five student profile details one by one:\n"
        "1. Branch of study\n"
        "2. Year of study\n"
        "3. Target job roles\n"
        "4. Target companies\n"
        "5. What they feel weak at (e.g. 'I freeze during interviews')\n\n"
        "Do NOT ask multiple questions at once. Ask them one by one. "
        "Acknowledge the student's input briefly and immediately ask the next question.\n"
        "Once you have gathered all five details, call the `save_student_profile` tool "
        "to save their answers to student_profile.json. "
        "After saving, inform the student that their profile has been saved successfully and end the conversation."
    )

    config = LocalAgentConfig(
        system_instructions=system_instructions,
        tools=[save_student_profile],
        capabilities=CapabilitiesConfig(),
        api_key=api_key
    )

    async with Agent(config) as agent:
        print("\n--- Starting Profile Agent ---")
        response = await agent.chat("Hello! Let's start building your placement profile. Please ask me the first question.")
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
        print()

        while True:
            # Check if student_profile.json exists (meaning the tool was called and executed)
            if os.path.exists("student_profile.json"):
                print("\n--- Profile successfully created and saved! Exiting. ---")
                break

            try:
                user_input = input("\nYou: ")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break

            if not user_input.strip():
                continue

            response = await agent.chat(user_input)
            print("\nProfileAgent: ", end="")
            async for token in response:
                sys.stdout.write(token)
                sys.stdout.flush()
            print()

if __name__ == "__main__":
    asyncio.run(main())
