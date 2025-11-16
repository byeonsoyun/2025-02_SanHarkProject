import requests
import json
import os

class OllamaClient:
    def __init__(self, base_url=None, model="llama3.2"):
        # Use environment variable or default to localhost
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model
        self.is_remote = not self.base_url.startswith('http://localhost')
    
    def generate_response(self, prompt, context=""):
        """Generate response using Ollama (optimized for local performance)"""
        
        # Aggressive optimization for local M3 MacBook
        if self.is_remote:
            # Remote GPU server - can handle more
            max_prompt_length = 3000
            timeout = 60
            num_predict = 500
        else:
            # Local M3 - very conservative settings
            max_prompt_length = 800  # Much shorter
            timeout = 30  # Shorter timeout
            num_predict = 200  # Shorter responses
        
        # Aggressively limit prompt length for local
        if len(prompt) > max_prompt_length:
            # Keep only the most important parts
            lines = prompt.split('\n')
            important_lines = []
            current_length = 0
            
            for line in lines:
                if current_length + len(line) > max_prompt_length:
                    break
                important_lines.append(line)
                current_length += len(line)
            
            prompt = '\n'.join(important_lines) + "\n\n답변:"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower for consistency
                        "num_predict": num_predict,
                        "num_ctx": 1024,  # Smaller context window
                        "top_k": 20,      # Reduced for speed
                        "top_p": 0.8      # Reduced for speed
                    }
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"LLM 오류: {response.status_code}"
                
        except requests.exceptions.Timeout:
            server_type = "원격 GPU 서버" if self.is_remote else "로컬 서버"
            return f"{server_type} 응답 시간 초과. 더 간단한 질문을 해주세요."
        except requests.exceptions.ConnectionError:
            server_type = "원격 GPU 서버" if self.is_remote else "로컬 Ollama 서버"
            return f"{server_type} 연결 실패. 서버 상태를 확인해주세요."
        except Exception as e:
            return f"오류: {str(e)}"
