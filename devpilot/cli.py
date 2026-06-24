import argparse
from dotenv import load_dotenv
from devpilot.agent import DevPilotAgent

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="DevPilot AI - Autonomous Developer Assistant")
    parser.add_argument("prompt", type=str, nargs="+", help="The task to execute.")
    
    args = parser.parse_args()
    task = " ".join(args.prompt)
    
    agent = DevPilotAgent()
    agent.execute_workflow(task)

if __name__ == "__main__":
    main()