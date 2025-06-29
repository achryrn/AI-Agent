# interfaces/cli_interface.py

from interfaces.base_interface import Interface


class CLIInterface(Interface):
    def __init__(self, allow_empty=False, exit_commands=None):
        self.allow_empty = allow_empty
        self.exit_commands = exit_commands or ['exit', 'quit', 'q']

    async def input(self) -> str:
        while True:
            try:
                user_input = input(">> ").strip()
                
                # Check for exit commands
                if user_input.lower() in self.exit_commands:
                    raise KeyboardInterrupt
                
                # Handle empty input
                if not user_input:
                    if self.allow_empty:
                        return user_input
                    print("Please enter a valid input (empty messages not allowed)")
                    continue
                
                return user_input
                
            except KeyboardInterrupt:
                print("\nExiting...")
                raise
            except EOFError:
                print("\nExiting...")
                raise KeyboardInterrupt

    async def output(self, message: str):
        print(f"[Agent]: {message}")