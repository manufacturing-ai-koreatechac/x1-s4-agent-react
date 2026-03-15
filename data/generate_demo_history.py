"""
generate_demo_history.py — 30일치 제조 신호 이력 데이터 생성 (시연용)

매 4시간마다 1개 레코드 = 30일 × 6개 = 180개 per 신호

생성 파일 (data/history/ 디렉토리):
  - anomaly_history.jsonl     : M001 이상점수 이력 (서서히 악화 + 간헐적 급등)
  - rul_history.jsonl         : M001 RUL 이력 (60일 → 8일로 감소)
  - maintenance_history.jsonl : M001 정비 이벤트 이력
  - defect_history.jsonl      : LINE-A 불량률 이력 (월요일 스파이크 패턴)
  - detection_history.jsonl   : LINE-B 객체탐지 이력
"""

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

# ── 경로 설정 ──────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(SCRIPT_DIR, 'history')


def ensure_dirs():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def write_jsonl(path: str, records: list):
    with open(path, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return len(records)


# ── 1. 이상탐지 이력 ───────────────────────────────────────────

def gen_anomaly_history(machine_id: str = "M001", days: int = 30) -> list:
    """
    서서히 악화하는 이상점수 패턴:
    - 15일 전 점검 후: 0.25-0.35 (안정)
    - 10일 전부터: 서서히 0.4-0.55로 증가
    - 최근 5일: 0.55-0.75
    - 최근 3일: 0.65-0.88 (경보 발생)
    - 간헐적 스파이크: 5일마다 한 번씩
    """
    np.random.seed(42)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    total = days * 6  # 매 4시간 = 하루 6개
    threshold = 0.75
    records = []

    for i in range(total):
        ts = now - timedelta(hours=(total - i) * 4)
        progress = i / total  # 0.0 → 1.0

        # 기본 트렌드: 0.25 → 0.75
        base = 0.25 + progress * 0.50

        # 15일 전(i=90) 점검: 점수 리셋
        if i < 90:
            # 점검 직후: 더 안정적
            base = 0.20 + progress * 0.30
        else:
            # 점검 이후: 재악화
            post_check_progress = (i - 90) / (total - 90)
            base = 0.25 + post_check_progress * 0.55

        # 노이즈
        noise = np.random.normal(0, 0.04)

        # 주기적 스파이크 (약 5일 = 30 레코드마다)
        if i % 30 == 0 and i > 30:
            spike = np.random.uniform(0.10, 0.22)
        else:
            spike = 0.0

        value = float(np.clip(base + noise + spike, 0.05, 0.99))
        status = "ANOMALY" if value > threshold else "NORMAL"
        alert_level = "HIGH" if value > 0.90 else ("MEDIUM" if value > threshold else "LOW")

        records.append({
            "ts": ts.isoformat(),
            "machine_id": machine_id,
            "signal_type": "anomaly",
            "value": round(value, 4),
            "status": status,
            "metadata": {
                "threshold": threshold,
                "alert_level": alert_level
            }
        })

    return records


# ── 2. RUL 이력 ────────────────────────────────────────────────

def gen_rul_history(machine_id: str = "M001", days: int = 30) -> list:
    """
    RUL 감소 패턴:
    - 30일 전: ~60일
    - 현재: ~8일
    - 감소 속도는 후반부로 갈수록 빨라짐 (비선형)
    """
    np.random.seed(123)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    total = days * 6
    start_rul = 60.0
    end_rul = 8.0
    records = []

    for i in range(total):
        ts = now - timedelta(hours=(total - i) * 4)
        progress = i / total

        # 비선형 감소 (후반 가속)
        rul = start_rul - (start_rul - end_rul) * (progress ** 1.3)

        # 노이즈 (측정 불확실성)
        noise = np.random.normal(0, 1.2)
        value = float(max(1.0, rul + noise))

        confidence = float(np.clip(
            0.85 - progress * 0.10 + np.random.normal(0, 0.03),
            0.60, 0.95
        ))

        urgency = "HIGH" if value < 10 else ("MEDIUM" if value < 20 else "LOW")

        records.append({
            "ts": ts.isoformat(),
            "machine_id": machine_id,
            "signal_type": "rul",
            "value": round(value, 1),
            "status": urgency,
            "metadata": {
                "confidence": round(confidence, 3),
                "rmse": 3.2
            }
        })

    return records


# ── 3. 정비 이벤트 이력 ────────────────────────────────────────

def gen_maintenance_history(machine_id: str = "M001") -> list:
    """
    실제 정비 이벤트 2건:
    - 45일 전: 정기 예방정비 (오일 교체 + 필터 청소)
    - 15일 전: 임시 점검 (베어링 점검 + 오일 보충, 베어링 교체 보류)
    """
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    events = [
        {
            "days_ago": 45,
            "action": "오일 교체 + 필터 청소 + 전체 점검",
            "result": "정상 복구. 이상점수 0.22로 감소.",
            "cost": 350000,
            "type": "planned"
        },
        {
            "days_ago": 15,
            "action": "베어링 점검 + 오일 보충 (베어링 교체 보류)",
            "result": "부분 개선. 베어링 마모 진행 중, 교체 필요 예상.",
            "cost": 120000,
            "type": "inspection"
        },
    ]

    records = []
    for ev in events:
        ts = now - timedelta(days=ev["days_ago"])
        records.append({
            "ts": ts.isoformat(),
            "machine_id": machine_id,
            "signal_type": "maintenance",
            "value": 1.0,
            "status": "COMPLETED",
            "metadata": {
                "action": ev["action"],
                "result": ev["result"],
                "cost": ev["cost"],
                "type": ev["type"]
            }
        })

    return records


# ── 4. 불량률 이력 ─────────────────────────────────────────────

def gen_defect_history(line_id: str = "LINE-A", days: int = 30) -> list:
    """
    불량률 패턴:
    - 평일: 2-3% (정상 운영)
    - 월요일 오전: 4-6% 스파이크 (주말 공정 재기동 영향)
    - 가끔 비계획 스파이크 (재료 로트 불량 등)
    """
    np.random.seed(77)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    total = days * 6
    records = []

    for i in range(total):
        ts = now - timedelta(hours=(total - i) * 4)
        weekday = ts.weekday()  # 0=월요일, 6=일요일
        hour = ts.hour

        # 기본 불량률
        if weekday == 0 and hour < 12:
            # 월요일 오전: 스파이크 (주말 재기동)
            base_rate = np.random.beta(6, 60)  # ~9% 중심
        elif weekday >= 5:
            # 주말: 소규모 생산 or 점검
            base_rate = np.random.beta(2, 50)  # ~4% 중심
        else:
            # 평일 일반
            base_rate = np.random.beta(2, 80)  # ~2.4% 중심

        # 비계획 스파이크 (약 10일에 1번)
        if i % 60 == 0 and i > 0:
            base_rate += np.random.uniform(0.02, 0.04)

        value = float(np.clip(base_rate, 0.005, 0.15))
        count = int(500 * value)
        grade = "A" if value < 0.03 else ("B" if value < 0.06 else "C")
        alert = value > 0.06

        records.append({
            "ts": ts.isoformat(),
            "machine_id": line_id,
            "signal_type": "defect",
            "value": round(value, 5),
            "status": "ALERT" if alert else "NORMAL",
            "metadata": {
                "count": count,
                "batch_size": 500,
                "grade": grade,
                "defect_types": {
                    "surface_scratch": int(count * 0.40),
                    "dimension_defect": int(count * 0.30),
                    "color_defect": int(count * 0.20),
                    "other": max(0, count - int(count * 0.90))
                }
            }
        })

    return records


# ── 5. 객체탐지 이력 ───────────────────────────────────────────

def gen_detection_history(line_id: str = "LINE-B", days: int = 30) -> list:
    """
    YOLOv8 탐지 결과:
    - 평균 4개/배치
    - 가끔 급증 (6개 이상 = 알람)
    """
    np.random.seed(55)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    total = days * 6
    records = []

    for i in range(total):
        ts = now - timedelta(hours=(total - i) * 4)

        # 포아송 분포 (평균 4)
        defects = int(np.random.poisson(3.8))

        # 간헐적 급증 (7일마다)
        if i % 42 == 0 and i > 0:
            defects += int(np.random.uniform(3, 8))

        alert = defects > 5

        records.append({
            "ts": ts.isoformat(),
            "machine_id": line_id,
            "signal_type": "detection",
            "value": float(defects),
            "status": "ALERT" if alert else "NORMAL",
            "metadata": {
                "fps": 45.2,
                "map50": 0.843,
                "map50_95": 0.612,
                "defect_classes": {
                    "scratch": max(0, defects - 4),
                    "dent": min(2, defects),
                    "contamination": min(2, max(0, defects - 2))
                }
            }
        })

    return records


# ── 메인 실행 ──────────────────────────────────────────────────

def main():
    ensure_dirs()
    print("=" * 55)
    print("제조 신호 이력 데이터 생성 (30일치)")
    print("=" * 55)

    # 1. 이상탐지 이력
    records = gen_anomaly_history("M001", days=30)
    path = os.path.join(HISTORY_DIR, 'anomaly_history.jsonl')
    n = write_jsonl(path, records)
    anomaly_vals = [r['value'] for r in records]
    anomaly_alerts = sum(1 for r in records if r['status'] == 'ANOMALY')
    print(f"\n[anomaly_history.jsonl]")
    print(f"  레코드 수: {n}개")
    print(f"  값 범위: {min(anomaly_vals):.3f} ~ {max(anomaly_vals):.3f}")
    print(f"  평균값: {sum(anomaly_vals)/len(anomaly_vals):.3f}")
    print(f"  ANOMALY 경보: {anomaly_alerts}회")
    print(f"  첫 레코드: {records[0]['ts'][:10]} 값={records[0]['value']:.3f}")
    print(f"  마지막 레코드: {records[-1]['ts'][:10]} 값={records[-1]['value']:.3f}")

    # 2. RUL 이력
    records = gen_rul_history("M001", days=30)
    path = os.path.join(HISTORY_DIR, 'rul_history.jsonl')
    n = write_jsonl(path, records)
    rul_vals = [r['value'] for r in records]
    print(f"\n[rul_history.jsonl]")
    print(f"  레코드 수: {n}개")
    print(f"  RUL 범위: {min(rul_vals):.1f} ~ {max(rul_vals):.1f}일")
    print(f"  첫 기록: {records[0]['ts'][:10]} RUL={records[0]['value']:.1f}일")
    print(f"  마지막: {records[-1]['ts'][:10]} RUL={records[-1]['value']:.1f}일")

    # 3. 정비 이벤트
    records = gen_maintenance_history("M001")
    path = os.path.join(HISTORY_DIR, 'maintenance_history.jsonl')
    n = write_jsonl(path, records)
    print(f"\n[maintenance_history.jsonl]")
    print(f"  레코드 수: {n}개")
    for r in records:
        print(f"  {r['ts'][:10]}: {r['metadata']['action'][:40]}...")

    # 4. 불량률 이력
    records = gen_defect_history("LINE-A", days=30)
    path = os.path.join(HISTORY_DIR, 'defect_history.jsonl')
    n = write_jsonl(path, records)
    defect_vals = [r['value'] * 100 for r in records]
    defect_alerts = sum(1 for r in records if r['status'] == 'ALERT')
    print(f"\n[defect_history.jsonl]")
    print(f"  레코드 수: {n}개")
    print(f"  불량률 범위: {min(defect_vals):.2f}% ~ {max(defect_vals):.2f}%")
    print(f"  평균 불량률: {sum(defect_vals)/len(defect_vals):.2f}%")
    print(f"  ALERT 횟수: {defect_alerts}회")

    # 5. 객체탐지 이력
    records = gen_detection_history("LINE-B", days=30)
    path = os.path.join(HISTORY_DIR, 'detection_history.jsonl')
    n = write_jsonl(path, records)
    det_vals = [r['value'] for r in records]
    det_alerts = sum(1 for r in records if r['status'] == 'ALERT')
    print(f"\n[detection_history.jsonl]")
    print(f"  레코드 수: {n}개")
    print(f"  탐지 불량 범위: {int(min(det_vals))} ~ {int(max(det_vals))}개")
    print(f"  평균: {sum(det_vals)/len(det_vals):.1f}개/배치")
    print(f"  ALERT 횟수: {det_alerts}회")

    print(f"\n생성 완료: {HISTORY_DIR}")
    print("=" * 55)


if __name__ == "__main__":
    main()
