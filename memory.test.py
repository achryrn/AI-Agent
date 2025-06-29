from memory.vector_memory import VectorMemory

memory = VectorMemory()
memory.save("user", "What is the capital of France?")
memory.save("agent", "The capital is Paris.")
results = memory.recall("city France")
print(results)