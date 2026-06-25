import json
import os
import time
from google import genai
from google.genai import types
from colorama import Fore, Style, init
from tenacity import retry, stop_after_attempt, wait_exponential
from devpilot.tools import run_command, read_file, write_file

# Initialize terminal color mapping
init(autoreset=True)

SYSTEM_INSTRUCTION = """
You are DevPilot AI, an autonomous software engineering assistant engineered for team Byte Benders.
Your goal is to complete complex developer workflows by investigating, executing, and verifying tasks.

You must ALWAYS respond with a SINGLE valid JSON object representing your next move. 
Do not wrap it in markdown blockquotes or triple backticks.
The JSON must strictly follow this structure:
{
    "status": "Planning" | "Executing Commands" | "Fixing Errors",
    "thought": "Explain your reasoning and what you are about to do.",
    "action": "run_command" | "read_file" | "write_file" | "finish",
    "action_input": "The command, filepath, or text array configuration"
}

Allowed actions:
- run_command: Executes a terminal command (e.g., action_input: "npm install")
- read_file: Reads a file to debug (e.g., action_input: "./package.json")
- write_file: Writes code to a file. action_input MUST be an array: [filepath, file_content].
- finish: Marks the task as complete and replies to the user.

Special Execution Instructions:
1. Automated Dependency Scanning & Repair: If a project environment fails to build or run:
   - Proactively inspect files like package.json, requirements.txt, or go.mod.
   - Match missing package runtime logs against appropriate installer paths.
   - Issue correct command sequences (e.g., "npm install", "pip install -r requirements.txt").
2. Maintain JSON Integrity: Only emit the exact valid JSON format.
"""

SUGGESTIONS_PROMPT_TEMPLATE = """
You are a principal software architect at Byte Benders reviewing a task.
Task: "{task}"

Analyze the scope and provide premium, structured architectural recommendations.
You must return a SINGLE valid JSON object matching this exact structure without markdown formatting:
{{
    "structure": "Definition of the ideal file and directory layout",
    "approaches": ["Alternative strategic route 1", "Alternative strategic route 2"],
    "scalability": "Specific performance optimization advice",
    "security": "Critical isolation rules or sanitization strategies",
    "requirements": ["Often overlooked library 1", "Often overlooked core configuration 2"],
    "extensions": ["Elegant future extension 1", "Elegant future extension 2"]
}}
"""

class DevPilotAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(Fore.RED + Style.BRIGHT + "[ERROR] GEMINI_API_KEY not found in environment.")
            exit(1)
            
        self.client = genai.Client(api_key=api_key)
        self.chat = self.client.chats.create(
            model='gemini-2.5-flash-lite',
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1,  
                response_mime_type="application/json"  
            )
        )
        
        self.steps_executed = 0
        self.bugs_fixed = 0
        self.process_log = []

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def _send_message_with_retry(self, current_input):
        return self.chat.send_message(current_input)

    def _generate_architectural_suggestions(self, task: str):
        print(Fore.CYAN + "\n[SYSTEM] Compiling Byte Benders architectural review...")
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=SUGGESTIONS_PROMPT_TEMPLATE.format(task=task),
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            sug = json.loads(raw_text)
            
            # Premium Box-Style UI Output
            print(Fore.BLUE + Style.BRIGHT + "\n╔" + "═"*78 + "╗")
            print(Fore.BLUE + Style.BRIGHT + "║" + Fore.WHITE + "                 BYTE BENDERS ARCHITECTURAL BLUEPRINT REVIEW                  " + Fore.BLUE + "║")
            print(Fore.BLUE + Style.BRIGHT + "╠" + "═"*78 + "╣")
            
            print(Fore.BLUE + "║ " + Fore.CYAN + Style.BRIGHT + "PROJECT TARGET STRUCTURE")
            print(Fore.BLUE + "║ " + Fore.WHITE + f"  {sug.get('structure', 'N/A')}")
            print(Fore.BLUE + "║")
            
            print(Fore.BLUE + "║ " + Fore.CYAN + Style.BRIGHT + "STRATEGIC ALTERNATIVE APPROACHES")
            for item in sug.get('approaches', []):
                print(Fore.BLUE + "║ " + Fore.WHITE + f"  > {item}")
            print(Fore.BLUE + "║")
                
            print(Fore.BLUE + "║ " + Fore.CYAN + Style.BRIGHT + "SCALABILITY AND RUNTIME")
            print(Fore.BLUE + "║ " + Fore.WHITE + f"  {sug.get('scalability', 'N/A')}")
            print(Fore.BLUE + "║")
            
            print(Fore.BLUE + "║ " + Fore.CYAN + Style.BRIGHT + "SECURITY SANITIZATION")
            print(Fore.BLUE + "║ " + Fore.WHITE + f"  {sug.get('security', 'N/A')}")
            print(Fore.BLUE + "║")
            
            print(Fore.BLUE + "║ " + Fore.CYAN + Style.BRIGHT + "CRITICAL REQUIREMENTS")
            for item in sug.get('requirements', []):
                print(Fore.BLUE + "║ " + Fore.WHITE + f"  > {item}")
            print(Fore.BLUE + "║")
                
            print(Fore.BLUE + "║ " + Fore.CYAN + Style.BRIGHT + "FUTURE EXTENSIONS")
            for item in sug.get('extensions', []):
                print(Fore.BLUE + "║ " + Fore.WHITE + f"  > {item}")
                
            print(Fore.BLUE + Style.BRIGHT + "╚" + "═"*78 + "╝\n")
            
        except Exception as e:
            print(Fore.RED + f"[SYSTEM WARNING] Recommendations rendering skipped: {e}\n")

    def _print_status_banner(self, status: str):
        print(Fore.MAGENTA + Style.BRIGHT + "\n" + "─"*70)
        print(Fore.MAGENTA + Style.BRIGHT + f"[STAGE ACTIVATED] Current Phase: {status.upper()}")
        print(Fore.MAGENTA + Style.BRIGHT + "─"*70)

    def _print_report(self):
        print(Fore.GREEN + Style.BRIGHT + "\n╔" + "═"*68 + "╗")
        print(Fore.GREEN + Style.BRIGHT + "║                  BYTE BENDERS EXECUTION SUMMARY                  ║")
        print(Fore.GREEN + Style.BRIGHT + "╠" + "═"*68 + "╣")
        print(Fore.GREEN + "║" + Fore.WHITE + f"  Total Pipeline Operations Executed : {self.steps_executed:<30}" + Fore.GREEN + "║")
        print(Fore.GREEN + "║" + Fore.WHITE + f"  Identified Runtime Bugs Fixed      : {self.bugs_fixed:<30}" + Fore.GREEN + "║")
        print(Fore.GREEN + Style.BRIGHT + "╠" + "═"*68 + "╣")
        print(Fore.GREEN + "║" + Fore.CYAN + "  Engine Process Log Ledger:                                       " + Fore.GREEN + "║")
        for idx, log in enumerate(self.process_log, 1):
            log_str = f"  [{idx}] {log}"[:65]
            print(Fore.GREEN + "║" + Fore.LIGHTBLACK_EX + f"{log_str:<68}" + Fore.GREEN + "║")
        print(Fore.GREEN + Style.BRIGHT + "╚" + "═"*68 + "╝\n")

    def execute_workflow(self, task: str):
        user_choice = input(Fore.WHITE + Style.BRIGHT + "Would you like AI Project Suggestions before starting? (y/n): ").strip().lower()
        if user_choice == 'y':
            self._generate_architectural_suggestions(task)
            self.process_log.append("Generated structured architectural blueprint.")
        else:
            print(Fore.LIGHTBLACK_EX + "[SYSTEM] Review bypassed. Directing execution to automation kernel.\n")

        print(Fore.CYAN + Style.BRIGHT + "[SYSTEM] DevPilot Kernel Active. Processing directives...")
        
        current_input = task
        last_status = None
        
        while True:
            try:
                response = self._send_message_with_retry(current_input)
                raw_text = response.text.strip()
                
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:-3].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:-3].strip()
                    
                data = json.loads(raw_text)
                status = data.get("status", "Executing Commands")
                thought = data.get("thought", "")
                action = data.get("action", "")
                action_input = data.get("action_input", "")
                
                self.steps_executed += 1
                
                if status != last_status:
                    self._print_status_banner(status)
                    last_status = status
                
                if status == "Fixing Errors" and ("Error Code" in current_input or "Stderr" in current_input):
                    self.bugs_fixed += 1

                print(Fore.LIGHTCYAN_EX + f"[THOUGHT] {thought}")
                
                if action == "finish":
                    print(Fore.GREEN + Style.BRIGHT + f"\n[SUCCESS] Pipeline Complete. Output: {action_input}\n")
                    self.process_log.append("Task metrics successfully complete.")
                    self._print_report()
                    break
                    
                elif action == "run_command":
                    print(Fore.YELLOW + f"[ACTION] Dispatching Script -> `{action_input}`")
                    self.process_log.append(f"Executed shell script: `{action_input}`")
                    
                    confirm = input(Fore.WHITE + "Allow terminal execution? [y/N]: ").strip().lower()
                    if confirm == 'y':
                        result = run_command(action_input)
                        current_input = f"Command output:\n{result}"
                    else:
                        current_input = "User explicitly denied execution privileges for this command."
                        print(Fore.RED + "[SYSTEM] Command skipped by user.")
                        
                elif action == "read_file":
                    print(Fore.YELLOW + f"[ACTION] Reading Target -> `{action_input}`")
                    self.process_log.append(f"Read system file: `{action_input}`")
                    result = read_file(action_input)
                    current_input = f"File content:\n{result}"
                    
                elif action == "write_file":
                    filepath, content = action_input[0], action_input[1]
                    print(Fore.YELLOW + f"[ACTION] Writing Disk Adjustments -> `{filepath}`")
                    self.process_log.append(f"Wrote to target file: `{filepath}`")
                    
                    confirm = input(Fore.WHITE + "Allow system file modifications? [y/N]: ").strip().lower()
                    if confirm == 'y':
                        result = write_file(filepath, content)
                        current_input = f"Write result:\n{result}"
                    else:
                        current_input = "User denied file modification permission."
                        print(Fore.RED + "[SYSTEM] File write rejected.")
                else:
                    current_input = "Error: Unknown action. Proceed with valid operations."
                    
            except json.JSONDecodeError:
                current_input = "JSON parsing failed. Ensure structural keys remain intact."
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + f"[CRITICAL RUNTIME CRASH] {e}")
                break