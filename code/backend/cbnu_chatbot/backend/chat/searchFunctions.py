import ast
import sys

# 별건 아니고 파이썬 파일 내 함수나 클래스 같은 부분들을 찾아내는 코드임, 기능이랑은 관련 없는데 개발 단계에서는 디버깅하기 좋아서 그냥 남겨둠 ㅎㅎ
# 명령줄 인수로 파일 이름을 받습니다.
if len(sys.argv) < 2:
    print("사용법: python extract_names.py <분석할_파이썬_파일명>")
    sys.exit(1)

filename = sys.argv[1]

try:
    with open(filename, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read())
except FileNotFoundError:
    print(f"오류: 파일 '{filename}'을(를) 찾을 수 없습니다.")
    sys.exit(1)
except Exception as e:
    print(f"파일을 파싱하는 중 오류 발생: {e}")
    sys.exit(1)


print(f"--- '{filename}'의 클래스 및 함수 이름 ---")
for node in ast.walk(tree):
    # 함수 정의 (def)
    if isinstance(node, ast.FunctionDef):
        # 클래스 내부에 정의된 메서드(node.name)는 추출되지만,
        # 일반 함수도 추출됩니다.
        print(f"Function/Method: {node.name}")
    # 클래스 정의 (class)
    elif isinstance(node, ast.ClassDef):
        print(f"Class: {node.name}")