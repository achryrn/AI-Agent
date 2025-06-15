from core.agent import Agent

def main():
    print("Starting LLaMA3 AI Assistant (type 'exit' to quit)\n")
    agent = Agent()
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        response = agent.handle_input(user_input)
        print(f"Assistant: {response}\n")

if __name__ == "__main__":
    main()
