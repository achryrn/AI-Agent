from core.dependency import llm  # or wherever your LLM is

prompt = "Hello! What is the color of grass?"
result = llm.generate(prompt)  # if sync
print(result)