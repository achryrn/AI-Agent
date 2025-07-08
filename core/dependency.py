from reasoning.llm_model_wrapper import LLMModelWrapper

llm = LLMModelWrapper(
    model="llama3",
    base_url="http://localhost:11434/api/generate"
)
