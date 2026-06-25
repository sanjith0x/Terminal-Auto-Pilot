import argparse
import sys
from dotenv import load_dotenv
from colorama import Fore, Style, init
from devpilot.agent import DevPilotAgent

def main():
    load_dotenv()
    init(autoreset=True)
    
    # Official Byte Benders Ascii Header
    print(Fore.CYAN + Style.BRIGHT + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(Fore.CYAN + Style.BRIGHT + "  ____  _   _ _____ _____   ____  _____ _   _ ____  _____ ____  ")
    print(Fore.CYAN + Style.BRIGHT + " | __ )| | | |_   _| ____| | __ )| ____| \\ | |  _ \\| ____|  _ \\ ")
    print(Fore.CYAN + Style.BRIGHT + " |  _ \\| | | | | | |  _|   |  _ \\|  _| |  \\| | | | |  _| | |_) |")
    print(Fore.CYAN + Style.BRIGHT + " | |_) | |_| | | | | |___  | |_) | |___| |\\  | |_| | |___|  _ < ")
    print(Fore.CYAN + Style.BRIGHT + " |____/ \\___/  |_| |_____| |____/|_____|_| \\_|____/|_____|_| \\_\\")
    print(Fore.BLUE + Style.BRIGHT + "                    AUTONOMOUS DEVPILOT KERNEL                   ")
    print(Fore.CYAN + Style.BRIGHT + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    parser = argparse.ArgumentParser(description="DevPilot AI - Built by Byte Benders")
    parser.add_argument("prompt", type=str, nargs="+", help="The development workflow objective to execute.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    task = " ".join(args.prompt)
    
    agent = DevPilotAgent()
    agent.execute_workflow(task)

if __name__ == "__main__":
    main()