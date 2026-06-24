import json
import os
import time
from google import genai
from google.genai import types
from colorama import Fore, Style, init
from tenacity import retry, stop_after_attempt, wait_exponential
from devpilot.tools import run_command, read_file, write_file

# Initialize terminal colors
init(autoreset=True)

SYSTEM_INSTRUCTION = """
You are DevPilot AI, an autonomous software development assistant.
Your goal is to complete complex developer workflows by investigating, executing, and verifying tasks.

You must ALWAYS respond with a SINGLE valid JSON object representing your next move. 
Do not wrap it in markdown blockquotes or triple backticks.
The JSON must strictly follow this structure:
{
    "thought": "Explain your reasoning and what you are about to do.",
    "action": "run_command", 
    "action_input": "The command, filepath, or text"
}

Allowed actions:
- run_command: Executes a terminal command (e.g., action_input: "npm install")
- read_file: Reads a file to debug (e.g., action_input: "./package.json")
- write_file: Writes code to a file. (e.g., action_input: ["./app.js", "console.log('hi');"])
- finish: Marks the task as complete and replies to the user (e.g., action_input: "The project is ready.")

Rules:
1. Think step-by-step. If a command fails, read the logs, fix the file, and try again.
2. For `write_file`, action_input MUST be an array: [filepath, file_content].
"""

class DevPilotAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(Fore.RED + "Error: GEMINI_API_KEY not found in environment.")
            exit(1)
            
        self.client = genai.Client(api_key=api_key)
        
        # Locked to the lightning fast 2.5 Flash-Lite variant
        self.chat = self.client.chats.create(
            model='gemini-2.5-flash-lite',
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1,  
                response_mime_type="application/json"  
            )
        )

    # Automatically back off and retry if the API hits a spike in demand
    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _send_message_with_retry(self, current_input):
        return self.chat.send_message(current_input)

    def execute_workflow(self, task: str):
        print(Fore.CYAN + f"\n🚀 DevPilot Engine Active for task: {task}\n")
        
        current_input = task
        
        while True:
            try:
                response = self._send_message_with_retry(current_input)
                raw_text = response.text.strip()
                
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:-3].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:-3].strip()
                    
                data = json.loads(raw_text)
                thought = data.get("thought", "")
                action = data.get("action", "")
                action_input = data.get("action_input", "")
                
                print(Fore.MAGENTA + f"🧠 Thought: {thought}")
                
                if action == "finish":
                    print(Fore.GREEN + Style.BRIGHT + f"\n✅ DevPilot: {action_input}\n")
                    break
                    
                elif action == "run_command":
                    print(Fore.YELLOW + f"⚡ Action: Run Command -> `{action_input}`")
                    confirm = input(Fore.WHITE + "Allow execution? [y/N]: ").strip().lower()
                    if confirm == 'y':
                        result = run_command(action_input)
                        current_input = f"Command output:\n{result}"
                        print(Fore.LIGHTBLACK_EX + "Logs analyzed.")
                    else:
                        current_input = "User denied permission to run command. Ask what to do next."
                        
                elif action == "read_file":
                    print(Fore.YELLOW + f"📄 Action: Read File -> `{action_input}`")
                    result = read_file(action_input)
                    current_input = f"File content:\n{result}"
                    
                elif action == "write_file":
                    filepath, content = action_input[0], action_input[1]
                    print(Fore.YELLOW + f"📝 Action: Write File -> `{filepath}`")
                    confirm = input(Fore.WHITE + "Allow file write? [y/N]: ").strip().lower()
                    if confirm == 'y':
                        result = write_file(filepath, content)
                        current_input = f"Write result:\n{result}"
                    else:
                        current_input = "User denied permission to write to file."
                else:
                    current_input = "Error: Unknown action. Stick to allowed actions."
                    
            except json.JSONDecodeError:
                current_input = "Your last response was not valid JSON. Please output strictly valid JSON."
            except Exception as e:
                print(Fore.RED + f"API Error: {e}")
                break