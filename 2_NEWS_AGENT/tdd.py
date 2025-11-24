"""
TDD 기반 split_message 함수 개발
파이썬 표준 라이브러리만 사용하여 테스트 및 구현
"""


def split_message(text: str, max_length: int) -> list[str]:
    """
    주어진 텍스트를 max_length를 초과하지 않는 여러 문자열로 분할합니다.
    
    - 줄바꿈 문자(\n)를 최우선 기준으로 분할합니다.
    - 줄바꿈이 없는 한 줄이 max_length를 초과하면 강제로 분할합니다.
    
    Args:
        text: 분할할 텍스트
        max_length: 최대 길이
        
    Returns:
        분할된 문자열 리스트
    """
    # 빈 문자열 처리
    if text == "":
        return [""]
    
    result = []
    
    # 1단계: 줄바꿈 문자(\n)를 기준으로 먼저 분할
    lines = text.split('\n')
    
    # 2단계: 각 줄에 대해 처리
    for line in lines:
        # 줄의 길이가 max_length 이하인 경우 그대로 추가
        if len(line) <= max_length:
            result.append(line)
        else:
            # 줄의 길이가 max_length를 초과하는 경우 강제로 분할
            # max_length씩 잘라서 추가
            start = 0
            while start < len(line):
                # 현재 위치부터 max_length만큼 잘라서 추가
                end = start + max_length
                chunk = line[start:end]
                result.append(chunk)
                start = end
    
    return result


# ========== 테스트 함수들 ==========

def test_short_text():
    """기본: max_length보다 짧은 텍스트"""
    text = "안녕하세요"
    max_length = 30
    result = split_message(text, max_length)
    assert result == ["안녕하세요"], f"예상: ['안녕하세요'], 실제: {result}"


def test_exact_length():
    """경계값: max_length와 같은 길이의 텍스트"""
    text = "a" * 30
    max_length = 30
    result = split_message(text, max_length)
    assert result == ["a" * 30], f"예상: ['{'a' * 30}'], 실제: {result}"


def test_newline_split():
    """줄바꿈 기준 분할: 여러 줄의 텍스트가 줄바꿈 기준으로 적절히 묶이는 경우"""
    text = "첫 번째 줄\n두 번째 줄\n세 번째 줄"
    max_length = 30
    result = split_message(text, max_length)
    assert result == ["첫 번째 줄", "두 번째 줄", "세 번째 줄"], f"예상: ['첫 번째 줄', '두 번째 줄', '세 번째 줄'], 실제: {result}"


def test_force_split():
    """강제 분할: 줄바꿈이 없는 긴 텍스트가 강제로 분할되는 경우"""
    text = "a" * 100  # 100개의 'a'
    max_length = 30
    result = split_message(text, max_length)
    expected = ["a" * 30, "a" * 30, "a" * 30, "a" * 10]
    assert result == expected, f"예상: {expected}, 실제: {result}"
    # 각 요소가 max_length를 초과하지 않는지 확인
    for item in result:
        assert len(item) <= max_length, f"항목 '{item}'의 길이가 {max_length}를 초과합니다: {len(item)}"


def test_mixed_split():
    """복합: 일반 줄바꿈과 강제 분할이 섞인 경우"""
    text = "짧은 줄\n" + "b" * 50 + "\n또 다른 짧은 줄"
    max_length = 30
    result = split_message(text, max_length)
    # 첫 번째 줄: "짧은 줄" (5자)
    # 두 번째 줄: "b" * 50을 30자씩 분할 -> ["b"*30, "b"*20]
    # 세 번째 줄: "또 다른 짧은 줄" (9자)
    expected = ["짧은 줄", "b" * 30, "b" * 20, "또 다른 짧은 줄"]
    assert result == expected, f"예상: {expected}, 실제: {result}"
    # 각 요소가 max_length를 초과하지 않는지 확인
    for item in result:
        assert len(item) <= max_length, f"항목 '{item}'의 길이가 {max_length}를 초과합니다: {len(item)}"


def test_empty_string():
    """빈 문자열: 입력이 빈 문자열('')인 경우"""
    text = ""
    max_length = 30
    result = split_message(text, max_length)
    assert result == [""], f"예상: [''], 실제: {result}"


# ========== 테스트 실행 ==========

def run_all_tests():
    """모든 테스트를 실행합니다"""
    tests = [
        test_short_text,
        test_exact_length,
        test_newline_split,
        test_force_split,
        test_mixed_split,
        test_empty_string,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            print(f"✓ {test_func.__name__}: 통과")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: 실패 - {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: 오류 발생 - {e}")
            failed += 1
    
    print(f"\n총 {len(tests)}개 테스트 중 {passed}개 통과, {failed}개 실패")
    
    if failed == 0:
        print("모든 테스트를 통과했습니다!")
        return True
    else:
        print("일부 테스트가 실패했습니다.")
        return False


if __name__ == "__main__":
    run_all_tests()

