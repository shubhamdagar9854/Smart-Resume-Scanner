import ollama_service

result = ollama_service.create_resume_summary('Test resume text with 5 years experience in Java and Spring Boot')
print('Generated summary:')
print(result)
