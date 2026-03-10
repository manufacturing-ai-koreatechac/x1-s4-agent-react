"""
signal_tools.py — Track A/B 결과 신호 조회 도구
X1 에이전트가 제조 AI 신호를 Tool로 조회할 수 있도록 구현

신호 소스:
  - Track A-2: 이상탐지(AutoEncoder), RUL(LSTM), 정비스케줄
  - Track B-1: 품질검사(CNN ResNet18)
  - Track B-2: 객체탐지(YOLOv8)
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import numpy as np

# ── 신호 파일 경로 설정 ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNAL_DIRS = [
    # 실제 Track A-2 outputs
    os.path.join(BASE_DIR, '../../track-a2-autoencoder-rul/outputs/signals'),
    # 실제 Track B-1 outputs
    os.path.join(BASE_DIR, '../../track-b1-cnn-transfer/outputs/signals'),
    # 실제 Track B-2 outputs
    os.path.join(BASE_DIR, '../../track-b2-vit-yolov8/outputs/signals'),
    # 로컬 캐시 (시뮬레이션용)
    os.path.join(BASE_DIR, '../outputs/signals'),
]


def _load_signal(filename: str) -> Optional[dict]:
    """여러 경로에서 신호 파일 로드. 없으면 시뮬레이션 반환."""
    for signal_dir in SIGNAL_DIRS:
        path = os.path.join(signal_dir, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


def _simulate_anomaly_signal() -> dict:
    """시뮬레이션 이상탐지 신호 생성"""
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    score = np.random.beta(2, 5) * 1.2  # 0~1.2 범위, 평균 ~0.4
    threshold = 0.75
    return {
        "timestamp": datetime.now().isoformat(),
        "signal_type": "anomaly_detection",
        "source": "track-a2/autoencoder [simulation]",
        "machine_id": "M001",
        "value": {
            "anomaly_score": round(float(score), 3),
            "threshold": threshold,
            "status": "ANOMALY" if score > threshold else "NORMAL",
            "alert_level": "HIGH" if score > 0.9 else ("MEDIUM" if score > threshold else "LOW"),
            "description": "설비 진동 신호 재구성 오차 기반 이상 감지"
        }
    }


def _simulate_rul_signal() -> dict:
    """시뮬레이션 RUL 신호 생성"""
    np.random.seed(int(datetime.now().timestamp()) % 500)
    rul = max(1, np.random.normal(15, 8))
    return {
        "timestamp": datetime.now().isoformat(),
        "signal_type": "rul_prediction",
        "source": "track-a2/lstm [simulation]",
        "machine_id": "M001",
        "value": {
            "rul_days": round(float(rul), 1),
            "confidence": 0.83,
            "maintenance_urgency": "HIGH" if rul < 10 else ("MEDIUM" if rul < 20 else "LOW"),
            "rmse": 3.2,
            "description": "LSTM 기반 설비 잔여수명(RUL) 예측"
        }
    }


def _simulate_maintenance_signal() -> dict:
    np.random.seed(42)
    days = int(np.random.uniform(8, 20))
    return {
        "timestamp": datetime.now().isoformat(),
        "signal_type": "maintenance_schedule",
        "source": "track-a2/maintenance [simulation]",
        "machine_id": "M001",
        "value": {
            "strategy": "PdM",
            "next_maintenance_date": (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d'),
            "days_until_maintenance": days,
            "priority": "HIGH" if days < 10 else "MEDIUM",
            "estimated_cost_saving_pct": 35.0,
            "roi_pct": 250.0,
            "recommended_action": "베어링 교체 + 오일 점검",
        }
    }


def _simulate_defect_signal() -> dict:
    np.random.seed(int(datetime.now().timestamp()) % 200)
    rate = np.random.beta(2, 20)
    count = int(500 * rate)
    return {
        "timestamp": datetime.now().isoformat(),
        "signal_type": "quality_inspection",
        "source": "track-b1/cnn-resnet18 [simulation]",
        "line_id": "LINE-A",
        "value": {
            "defect_rate": round(float(rate), 4),
            "defect_count": count,
            "batch_size": 500,
            "quality_grade": "A" if rate < 0.05 else ("B" if rate < 0.10 else "C"),
            "defect_types": {
                "surface_scratch": int(count * 0.4),
                "dimension_defect": int(count * 0.3),
                "color_defect": int(count * 0.2),
                "other": count - int(count * 0.9)
            },
            "alert": rate > 0.10,
        }
    }


def _simulate_detection_signal() -> dict:
    np.random.seed(int(datetime.now().timestamp()) % 300)
    defects = int(np.random.poisson(5))
    return {
        "timestamp": datetime.now().isoformat(),
        "signal_type": "object_detection",
        "source": "track-b2/yolov8 [simulation]",
        "line_id": "LINE-B",
        "value": {
            "defects_detected": defects,
            "map50": 0.843,
            "map50_95": 0.612,
            "defect_classes": {
                "scratch": max(0, defects - 4),
                "dent": min(2, defects),
                "contamination": min(2, max(0, defects - 2))
            },
            "processing_fps": 45.2,
            "alert": defects > 5,
        }
    }


# ── 공개 Tool 함수 ─────────────────────────────────────────────

def get_anomaly_status(machine_id: str = "M001") -> dict:
    """
    [Tool] Track A-2 이상탐지 결과 조회
    AutoEncoder 기반 설비 진동 신호 이상 여부 반환

    Args:
        machine_id: 설비 ID (기본값: M001)
    Returns:
        dict: {status, anomaly_score, alert_level, timestamp}
    """
    signal = _load_signal('anomaly_signal.json') or _simulate_anomaly_signal()
    v = signal['value']
    return {
        "tool": "get_anomaly_status",
        "machine_id": signal.get('machine_id', machine_id),
        "status": v['status'],
        "anomaly_score": v['anomaly_score'],
        "threshold": v['threshold'],
        "alert_level": v['alert_level'],
        "timestamp": signal['timestamp'],
        "source": signal['source'],
        "summary": f"설비 {machine_id}: {v['status']} (점수 {v['anomaly_score']:.3f}/{v['threshold']:.2f})"
    }


def get_rul_prediction(machine_id: str = "M001") -> dict:
    """
    [Tool] Track A-2 잔여수명(RUL) 예측 결과 조회
    LSTM 기반 설비 잔여수명(일) 반환

    Args:
        machine_id: 설비 ID
    Returns:
        dict: {rul_days, maintenance_urgency, confidence, timestamp}
    """
    signal = _load_signal('rul_signal.json') or _simulate_rul_signal()
    v = signal['value']
    return {
        "tool": "get_rul_prediction",
        "machine_id": signal.get('machine_id', machine_id),
        "rul_days": v['rul_days'],
        "maintenance_urgency": v['maintenance_urgency'],
        "confidence": v['confidence'],
        "timestamp": signal['timestamp'],
        "source": signal['source'],
        "summary": f"설비 {machine_id}: 잔여수명 {v['rul_days']:.1f}일 (긴급도: {v['maintenance_urgency']})"
    }


def get_maintenance_schedule(machine_id: str = "M001") -> dict:
    """
    [Tool] Track A-2 정비 스케줄 조회
    예지보전 기반 다음 정비 일정 및 권장 조치 반환

    Args:
        machine_id: 설비 ID
    Returns:
        dict: {next_date, days_until, priority, recommended_action}
    """
    signal = _load_signal('maintenance_signal.json') or _simulate_maintenance_signal()
    v = signal['value']
    return {
        "tool": "get_maintenance_schedule",
        "machine_id": signal.get('machine_id', machine_id),
        "next_maintenance_date": v['next_maintenance_date'],
        "days_until_maintenance": v['days_until_maintenance'],
        "priority": v['priority'],
        "recommended_action": v['recommended_action'],
        "estimated_cost_saving_pct": v['estimated_cost_saving_pct'],
        "timestamp": signal['timestamp'],
        "summary": f"설비 {machine_id}: {v['days_until_maintenance']}일 후 정비 ({v['priority']}) — {v['recommended_action']}"
    }


def get_defect_rate(line_id: str = "LINE-A") -> dict:
    """
    [Tool] Track B-1 품질검사 결과 조회
    CNN ResNet18 기반 불량률 및 불량 유형 반환

    Args:
        line_id: 생산 라인 ID
    Returns:
        dict: {defect_rate, quality_grade, defect_types, alert}
    """
    signal = _load_signal('defect_signal.json') or _simulate_defect_signal()
    v = signal['value']
    return {
        "tool": "get_defect_rate",
        "line_id": signal.get('line_id', line_id),
        "defect_rate": v['defect_rate'],
        "defect_rate_pct": f"{v['defect_rate']:.1%}",
        "defect_count": v['defect_count'],
        "batch_size": v['batch_size'],
        "quality_grade": v['quality_grade'],
        "defect_types": v['defect_types'],
        "alert": v['alert'],
        "timestamp": signal['timestamp'],
        "source": signal['source'],
        "summary": f"라인 {line_id}: 불량률 {v['defect_rate']:.1%} (등급 {v['quality_grade']})" + (" ⚠️ 조치 필요" if v['alert'] else " ✅ 정상")
    }


def get_detection_results(line_id: str = "LINE-B") -> dict:
    """
    [Tool] Track B-2 YOLOv8 객체탐지 결과 조회
    실시간 불량 탐지 개수 및 종류 반환

    Args:
        line_id: 생산 라인 ID
    Returns:
        dict: {defects_detected, defect_classes, map50, alert}
    """
    signal = _load_signal('detection_signal.json') or _simulate_detection_signal()
    v = signal['value']
    return {
        "tool": "get_detection_results",
        "line_id": signal.get('line_id', line_id),
        "defects_detected": v['defects_detected'],
        "defect_classes": v['defect_classes'],
        "map50": v['map50'],
        "processing_fps": v['processing_fps'],
        "alert": v['alert'],
        "timestamp": signal['timestamp'],
        "source": signal['source'],
        "summary": f"라인 {line_id}: 탐지 불량 {v['defects_detected']}개" + (" ⚠️ 알람" if v['alert'] else " ✅ 정상")
    }


def get_manufacturing_dashboard() -> dict:
    """
    [Tool] 제조 현장 통합 대시보드 — 모든 신호 종합
    Track A/B 전체 결과를 하나의 뷰로 통합

    Returns:
        dict: 설비상태(A) + 품질상태(B) + 종합 권장사항
    """
    anomaly = get_anomaly_status()
    rul = get_rul_prediction()
    maintenance = get_maintenance_schedule()
    defect = get_defect_rate()
    detection = get_detection_results()

    # 종합 위험도 계산
    risk_score = 0
    if anomaly['status'] == 'ANOMALY':
        risk_score += 40
    if rul['maintenance_urgency'] == 'HIGH':
        risk_score += 30
    elif rul['maintenance_urgency'] == 'MEDIUM':
        risk_score += 15
    if defect['alert']:
        risk_score += 20
    if detection['alert']:
        risk_score += 10

    overall_status = "CRITICAL" if risk_score >= 60 else ("WARNING" if risk_score >= 30 else "NORMAL")

    # 권장사항 생성
    recommendations = []
    if anomaly['status'] == 'ANOMALY':
        recommendations.append(f"🔴 설비 M001 이상 감지 — 즉시 점검 필요 (이상점수: {anomaly['anomaly_score']})")
    if rul['maintenance_urgency'] == 'HIGH':
        recommendations.append(f"🔴 잔여수명 {rul['rul_days']}일 — {maintenance['recommended_action']}")
    if defect['alert']:
        recommendations.append(f"🟠 LINE-A 불량률 {defect['defect_rate_pct']} 초과 — 공정 파라미터 점검")
    if detection['alert']:
        recommendations.append(f"🟠 LINE-B 불량 {detection['defects_detected']}개 탐지 — 카메라 검사 강화")
    if not recommendations:
        recommendations.append("✅ 모든 라인 정상 운영 중")

    return {
        "tool": "get_manufacturing_dashboard",
        "timestamp": datetime.now().isoformat(),
        "overall_status": overall_status,
        "risk_score": risk_score,
        "track_a": {
            "anomaly": anomaly['summary'],
            "rul": rul['summary'],
            "maintenance": maintenance['summary']
        },
        "track_b": {
            "defect_rate": defect['summary'],
            "detection": detection['summary']
        },
        "recommendations": recommendations,
        "summary": f"현장 종합: {overall_status} (위험도 {risk_score}/100)"
    }


# ── 직접 실행 테스트 ───────────────────────────────────────────
if __name__ == "__main__":
    print("=== 제조 신호 도구 테스트 ===\n")
    print("1. 이상탐지:", get_anomaly_status()['summary'])
    print("2. RUL 예측:", get_rul_prediction()['summary'])
    print("3. 정비 스케줄:", get_maintenance_schedule()['summary'])
    print("4. 불량률:", get_defect_rate()['summary'])
    print("5. 탐지 결과:", get_detection_results()['summary'])
    print()
    dashboard = get_manufacturing_dashboard()
    print(f"📊 대시보드: {dashboard['summary']}")
    for rec in dashboard['recommendations']:
        print(f"  {rec}")
