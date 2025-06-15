# tools/smart_web_agent/__init__.py

from tools.research.researcher import Researcher
from .researcher import Researcher
import asyncio

def run(command: str, model):
    researcher = Researcher(command, model)
    asyncio.run(researcher.research(command))
    return "[Research completed]"