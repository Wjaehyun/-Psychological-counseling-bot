# 데이터 전처리 및 청킹 가이드

## 목표
원본 txt/json 파일을 파싱하여 DB에 저장 가능한 형태로 변환

---

## 전체 Flow

```
[입력] txt + json 파일
        ↓
[STEP 1] txt 파싱 (청킹) → 발화 단위 분리
[STEP 2] json 파싱 → 메타데이터 + 라벨 추출
        ↓
[STEP 3] 데이터 통합
        ↓
[출력] DB 저장용 데이터
```

---

## STEP 1: txt 파싱 (청킹)

### 입력
```
상담사 : 안녕하세요. 오늘 기분은 어떠세요?
내담자 : 요즘 너무 힘들어요.
상담사 : 그렇군요. 언제부터 그런 느낌이 드셨나요?
```

### 파싱 패턴
```python
pattern = r'^(상담사|내담자)\s*:\s*(.+)$'
```

### 출력
```python
paragraphs = [
    {"speaker": "상담사", "content": "안녕하세요. 오늘 기분은 어떠세요?", "index": 0},
    {"speaker": "내담자", "content": "요즘 너무 힘들어요.", "index": 1},
    {"speaker": "상담사", "content": "그렇군요. 언제부터...", "index": 2}
]
```

---

## STEP 2: json 파싱

### 입력
```json
{
    "id": "D012",
    "age": 31,
    "gender": "남",
    "depression": 2,
    "anxiety": 0,
    "class": "DEPRESSION",
    "summary": "주요 증상: ...",
    "paragraph": [
        {"paragraph_speaker": "상담사", "depressive_mood": 0, ...},
        {"paragraph_speaker": "내담자", "depressive_mood": 1, ...}
    ]
}
```

### 출력
```python
metadata = {
    "id": "D012",
    "age": 31,
    "gender": "남",
    "depression": 2,
    "anxiety": 0,
    "class": "DEPRESSION",
    "summary": "주요 증상: ..."
}

labels = [
    {"depressive_mood": 0, "suicidal": 0, ...},  # index 0
    {"depressive_mood": 1, "suicidal": 0, ...}   # index 1
]
```

---

## STEP 3: 데이터 통합 (DB 저장 형태)

### counseling_data (상담 세션)
```python
{
    "source_id": "D012",           # metadata['id']
    "category": "DEPRESSION",       # metadata['class']
    "severity": 2,                  # depression+anxiety+addiction
    "summary": "주요 증상: ...",    # metadata['summary']
    "raw_metadata": {...}           # 전체 metadata
}
```

### counseling_paragraphs (발화 단위)
```python
[
    {
        "paragraph_index": 0,
        "speaker": "상담사",
        "content": "안녕하세요...",
        "labels": {"depressive_mood": 0, ...}
    },
    {
        "paragraph_index": 1,
        "speaker": "내담자", 
        "content": "요즘 너무 힘들어요.",
        "labels": {"depressive_mood": 1, ...}
    }
]
```

---

## 파일 경로

| 구분 | 경로 패턴 |
|------|----------|
| 원천 txt | `01.원천데이터/TS_{카테고리}_{회기}/resource_*.txt` |
| 라벨 json | `02.라벨링데이터/TL_{카테고리}_{회기}/label_*.json` |

---

## 카테고리 매핑

| 폴더명 | 코드 |
|--------|------|
| 001. 우울증 | DEPRESSION |
| 002. 불안장애 | ANXIETY |
| 003. 중독 | ADDICTION |
| 004. 일반군 | NORMAL |

---

## 참고

- 데이터 구조 상세: [DATA_ANALYSIS.md](./DATA_ANALYSIS.md)
- DB 스키마: [DATABASE_DESIGN.md](./DATABASE_DESIGN.md)
