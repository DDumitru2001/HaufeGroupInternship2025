from gpt4all import GPT4All
import os

model = GPT4All("CodeLlama-7B.Q5_K_S.gguf", model_path="./models")

def review_code(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        code_content = f.read()

    prompt = f"""
        You are an expert web dev developer.
        Please review the following code and provide:
        1. Potential bugs or errors
        2. Suggestions for improvements and refactoring
        3. Recommendations for readability, style, and performance

        Code:
        {code_content}
        """

    with model.chat_session():
        response = model.generate(prompt, max_tokens=300)
        print("\n=== Code Review ===\n")
        print(response)
        print("\n==================\n")

review_code("code_to_review/example.py")
