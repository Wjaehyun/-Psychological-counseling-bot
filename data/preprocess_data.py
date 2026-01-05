"""
FileName    : preprocess_data.py
Auth        : 이성진
Date        : 2026-01-05
Description : 원본 txt/json 데이터 전처리
Issue/Note  : 비고
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

import os
import glob
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any
from langchain_core.documents import Document
from tqdm import tqdm

# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------

# 상수 정의

TXT_DIR = r"C:\SKN_LSJ\SKN21-3rd-3Team\data\raw\16.심리상담 데이터\3.개방데이터\1.데이터\Training\01.원천데이터"
JSON_DIR = r"C:\SKN_LSJ\SKN21-3rd-3Team\data\raw\16.심리상담 데이터\3.개방데이터\1.데이터\Training\02.라벨링데이터"

# -------------------------------------------------------------
# Main Functions : txt 파싱 → json 파싱 → 통합
# -------------------------------------------------------------

# -------------------------------------------------------------
# STEP 1. txt 파싱 (발화 단위 분리)
# -------------------------------------------------------------

def parse_txt(txt_path):
    """
    텍스트 파일에서 '상담사'와 '내담자'의 대화 분리
    태그가 있는 경우를 대비하여 정규표현식 사용
    """
    paragraphs = []
    
    pattern = r'(?:\\s*)?(상담사|내담자)\s*:\s*(.+)$'

    with open(txt_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line: continue   

            match = re.match(pattern, line)
            if match:
                paragraphs.append({
                    "speaker": match.group(1),
                    "content": match.group(2),
                    "index": idx
                })
    return paragraphs

# -------------------------------------------------------------
# STEP 2. json 파싱 (metadata, label 추출)
# -------------------------------------------------------------

def parse_json(json_path):
    """
    내담자 정보, 요약문, 심리 척도(라벨) 추출
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    #1. 공통 정보 (질환 분류, 나이, 성별, 요약, 질환별 가중치 등)
    info = {
        "id": data['id'],
        "class": data['class'],
        "summary": data['summary'],
        "age": data['age'],
        "gender": data['gender'],
        "severity": {             # severity (중증도) : 질환별 가중치 데이터화
            "depressing": data.get('depression', 0),
            "anxiety": data.get('anxiety', 0),
            "addiction": data.get('addiction', 0)
        }
    }

    #2. 문장별 심리 라벨 (주요 판단 지표, 즉 값이 1인 척도들만 리스트로 추출)
    p_labels = []

    for p in data.get('paragraph', []):
        active = [k for k, v in p.items() if v == 1 and isinstance(v, int)]
        p_labels.append(active)
    
    return info, p_labels

# -------------------------------------------------------------
# STEP 3. 데이터 통합 
# -------------------------------------------------------------

def integrate_data(txt_data, json_info, json_labels):
    """
    파싱 데이터 합쳐서 LangChain Document 객체 생성
    요약본 별도 생성, 헤더 주입, 화자별 분류
    """
    integrated_docs = []

    # Summary Indexing (전체 맥락 파악을 위한 부모 문서)
    summary_doc = Document(
        page_content=f"[상담요약 = {json_info['class']}] {json_info['summary']}",
        metadata = {
            **json_info,
            "type":"summary_parent",
            "severity":str(json_info['severity'])  # 딕셔너리를 문자열화 -> 메타데이터 저장
        }
    )
    integrated_docs.append(summary_doc)

    # 헤더 청킹 & 화자 인식
    for i, p in enumerate(txt_data):
        labels = json_labels[i] if i < len(json_labels) else []

        header = f"[분류: {json_info['class']}][특징: {', '.join(labels[:2] if labels else '일반')}]"

        doc_type = "client_symptom" if p['speaker'] == "내담자" else "counselor_technique"

        doc = Document(
            page_content=header + f"{p['speaker']}: {p['content']}",
            metadata = {
                "source_id": json_info['id'],
                "class": json_info['class'],
                "speaker": p['speaker'],
                "type": doc_type,
                "labels": labels,
                "age": json_info['age'],
                "gender": json_info['gender']
            }
        )
        integrated_docs.append(doc)
    
    return integrated_docs

# -------------------------------------------------------------
# STEP 4. 메인 실행 루프
# -------------------------------------------------------------

def run_preprocessing():
    # 파일 목록 가져오기 및 매칭
    txt_files = sorted(glob.glob(os.path.join(TXT_DIR, "**", "*.txt"), recursive=True))
    json_files = sorted(glob.glob(os.path.join(JSON_DIR, "**", "*.json"), recursive=True))

    # ID 매칭을 위한 딕셔너리 (ID : 경로)
    json_dict = {os.path.basename(f).split('_')[-1].replace('.json', ''): f for f in json_files}

    final_docs = []

    print(f"작업 시작: 총 {len(txt_files)}개의 파일을 처리")

    for txt_path in tqdm(txt_files):
        txt_id = os.path.basename(txt_path).split('_')[-1].replace('.txt', '')

        if txt_id in json_dict:
            try:
                t_data = parse_txt(txt_path)
                j_info, j_labels = parse_json(json_dict[txt_id])
                integrated = integrate_data(t_data, j_info, j_labels)

                final_docs.extend(integrated)
            except Exception as e:
                print(f"\n[오류] ID {txt_id} 처리 중 문제 발생: {e}")
    
    print(f"\n전처리 완료. 생성된 총 문서 조각(Document_ tn: {len(final_docs)})")
    return final_docs

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------

if __name__ == "__main__":
    # 데이터 전처리 실행
    all_docs = run_preprocessing()

    # 결과 확인 (샘플 1개 출력)
    if all_docs:
        print("\n--- 생성 데이터 샘플 ---")
        print(f"내용: {all_docs[1].page_content}")
        print(f"메타데이터: {all_docs[1].metadata}")