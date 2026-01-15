import ollama
import traceback

print("Testing ollama connection...")
try:
    # Test basic ollama connection
    response = ollama.generate(model='llama3.2:latest', prompt='Hello, how are you?')
    print("✅ Ollama connection successful!")
    print(f"Response: {response['response']}")
except Exception as e:
    print(f"❌ Ollama connection failed: {e}")
    print(traceback.format_exc())

print("\nTesting summary generation...")
try:
    from ollama_service import create_resume_summary
    result = create_resume_summary('Test resume text with 5 years experience in Java and Spring Boot')
    print(f"Generated summary: {result}")
except Exception as e:
    print(f"❌ Summary generation failed: {e}")
    print(traceback.format_exc())
