"""
analytics_tools.py — 제조 AI 이력 분석 + 통계 + 리포트 + 의사결정 도구

signal_tools.py가 '현재 상태'를 반환한다면,
analytics_tools.py는 '이력 + 통계 + 미래 예측 + 의사결정 근거'를 제공합니다.

함수 목록:
  1. get_signal_history       — JSONL에서 마지막 N개 레코드 로드
  2. get_signal_statistics    — 지정 기간 통계 (mean, std, trend 등)
  3. get_trend_analysis       — 일별 집계 + 트렌드 + 24h 예측
  4. compare_machines         — 여러 설비 동일 메트릭 비교 랭킹
  5. get_maintenance_decision — 이상탐지+RUL+정비이력 종합 의사결정
  6. generate_equipment_health_report — 설비 건강도 마크다운 보고서
  7. generate_quality_report  — 품질 마크다운 보고서
  8. generate_factory_weekly_summary  — 전체 공장 주간 요약
  9. search_maintenance_log   — 유지보수 로그 키워드 검색
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

# ── 경로 설정 ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(BASE_DIR, '../data/history')
DATA_DIR = os.path.join(BASE_DIR, '../data')


def _ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _history_path(signal_type: str) -> str:
    return os.path.join(HISTORY_DIR, f'{signal_type}_history.jsonl')


def _load_jsonl(path: str) -> list:
    """JSONL 파일 전체 로드. 없으면 빈 리스트 반환."""
    if not os.path.exists(path):
        return []
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def _try_generate_demo_history():
    """demo history가 없을 때 generate_demo_history.py 자동 실행."""
    anomaly_path = _history_path('anomaly')
    if os.path.exists(anomaly_path):
        return
    gen_script = os.path.join(DATA_DIR, 'generate_demo_history.py')
    if os.path.exists(gen_script):
        try:
            subprocess.run([sys.executable, gen_script], check=True, capture_output=True)
        except Exception:
            pass


def _simulate_history(machine_id: str, signal_type: str, n: int = 720) -> list:
    """
    JSONL 파일이 없을 때 사용할 시뮬레이션 이력 생성.
    30일치, 매 4시간 간격 = 30 * 6 = 180개 레코드.
    """
    now = datetime.now()
    records = []
    np.random.seed(42)

    if signal_type == 'anomaly':
        # 서서히 악화하는 패턴: 0.3 → 0.6, 최근 3일 0.6-0.85
        for i in range(n):
            ts = now - timedelta(hours=(n - i) * 4)
            progress = i / n  # 0→1
            base = 0.25 + progress * 0.45
            noise = np.random.normal(0, 0.05)
            # 주기적 스파이크 (약 5일마다)
            if i % 30 == 0:
                noise += np.random.uniform(0.1, 0.25)
            value = float(np.clip(base + noise, 0.1, 1.0))
            threshold = 0.75
            status = "ANOMALY" if value > threshold else "NORMAL"
            records.append({
                "ts": ts.isoformat(),
                "machine_id": machine_id,
                "signal_type": "anomaly",
                "value": round(value, 4),
                "status": status,
                "metadata": {"threshold": threshold}
            })

    elif signal_type == 'rul':
        # 60일 → 8일 감소 패턴
        start_rul = 60.0
        end_rul = 8.0
        for i in range(n):
            ts = now - timedelta(hours=(n - i) * 4)
            progress = i / n
            rul = start_rul - (start_rul - end_rul) * progress
            noise = np.random.normal(0, 1.5)
            value = float(max(1.0, rul + noise))
            confidence = float(np.clip(0.75 + np.random.normal(0, 0.05), 0.6, 0.95))
            records.append({
                "ts": ts.isoformat(),
                "machine_id": machine_id,
                "signal_type": "rul",
                "value": round(value, 1),
                "status": "HIGH" if value < 10 else ("MEDIUM" if value < 20 else "LOW"),
                "metadata": {"confidence": round(confidence, 3)}
            })

    elif signal_type == 'maintenance':
        # 15일 전, 45일 전 두 건의 정비 이벤트
        events = [
            {"days_ago": 45, "action": "오일 교체 + 필터 청소", "result": "정상 복구"},
            {"days_ago": 15, "action": "베어링 점검 + 오일 보충", "result": "부분 개선 (베어링 교체 보류)"},
        ]
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
                    "cost": 500000 if ev["days_ago"] == 15 else 300000
                }
            })

    elif signal_type == 'defect':
        # 주중 2-3%, 월요일 스파이크 4-6%
        for i in range(n):
            ts = now - timedelta(hours=(n - i) * 4)
            weekday = ts.weekday()  # 0=월요일
            if weekday == 0:
                # 월요일 스파이크
                rate = float(np.clip(np.random.beta(5, 50) + 0.02, 0.01, 0.12))
            else:
                rate = float(np.clip(np.random.beta(3, 80), 0.005, 0.06))
            count = int(500 * rate)
            grade = "A" if rate < 0.03 else ("B" if rate < 0.06 else "C")
            records.append({
                "ts": ts.isoformat(),
                "machine_id": machine_id,
                "signal_type": "defect",
                "value": round(rate, 5),
                "status": "ALERT" if rate > 0.06 else "NORMAL",
                "metadata": {"count": count, "batch_size": 500, "grade": grade}
            })

    elif signal_type == 'detection':
        for i in range(n):
            ts = now - timedelta(hours=(n - i) * 4)
            defects = int(np.random.poisson(4))
            records.append({
                "ts": ts.isoformat(),
                "machine_id": machine_id,
                "signal_type": "detection",
                "value": float(defects),
                "status": "ALERT" if defects > 5 else "NORMAL",
                "metadata": {"fps": 45.2, "map50": 0.843}
            })

    return records


# ── 1. 이력 조회 ───────────────────────────────────────────────

def get_signal_history(machine_id: str, signal_type: str, last_n: int = 48) -> dict:
    """
    [Tool] JSONL 이력 파일에서 마지막 N개 레코드 반환.

    Args:
        machine_id: 설비 ID (예: 'M001') 또는 라인 ID (예: 'LINE-A')
        signal_type: 'anomaly' | 'rul' | 'maintenance' | 'defect' | 'detection'
        last_n: 반환할 레코드 수 (기본값 48 = 최근 8일, 매 4h 기준)

    Returns:
        dict: {"records": [...], "count": N, "period": "..."}
    """
    _ensure_history_dir()
    _try_generate_demo_history()

    path = _history_path(signal_type)
    records = _load_jsonl(path)

    # machine_id 필터
    records = [r for r in records if r.get('machine_id') == machine_id]

    # JSONL이 없으면 시뮬레이션
    if not records:
        records = _simulate_history(machine_id, signal_type, n=180)

    # 타임스탬프 기준 정렬 후 마지막 N개
    records.sort(key=lambda r: r.get('ts', ''))
    records = records[-last_n:]

    period = "N/A"
    if records:
        t_start = records[0].get('ts', '')[:10]
        t_end = records[-1].get('ts', '')[:10]
        period = f"{t_start} ~ {t_end}"

    return {
        "tool": "get_signal_history",
        "machine_id": machine_id,
        "signal_type": signal_type,
        "records": records,
        "count": len(records),
        "period": period,
        "summary": f"{machine_id} {signal_type} 이력 {len(records)}건 ({period})"
    }


# ── 2. 통계 분석 ───────────────────────────────────────────────

def get_signal_statistics(
    machine_id: str,
    signal_type: str = 'anomaly',
    period_hours: int = 168
) -> dict:
    """
    [Tool] 지정 기간 내 신호 통계 계산.

    Args:
        machine_id: 설비 ID
        signal_type: 신호 종류
        period_hours: 분석 기간 (기본 168h = 7일)

    Returns:
        dict: {"statistics": {...}, "period_hours": N, "sample_count": N, "summary": "..."}
    """
    cutoff = datetime.now() - timedelta(hours=period_hours)

    history = get_signal_history(machine_id, signal_type, last_n=9999)
    records = history['records']

    # 기간 필터
    filtered = []
    for r in records:
        try:
            ts = datetime.fromisoformat(r['ts'])
            if ts >= cutoff:
                filtered.append(r)
        except (ValueError, KeyError):
            pass

    if not filtered:
        # 데이터가 없으면 전체 사용
        filtered = records

    values = np.array([r['value'] for r in filtered], dtype=float)
    statuses = [r.get('status', '') for r in filtered]

    # 경보 상태 집계
    alert_statuses = {'ANOMALY', 'ALERT', 'HIGH', 'CRITICAL'}
    alert_count = sum(1 for s in statuses if s in alert_statuses)
    anomaly_rate = alert_count / len(statuses) if statuses else 0.0

    # 백분위수
    p50 = float(np.percentile(values, 50))
    p95 = float(np.percentile(values, 95))

    # 선형 회귀 트렌드 (시간 인덱스 기준)
    x = np.arange(len(values))
    if len(values) >= 2:
        coeffs = np.polyfit(x, values, 1)
        slope = float(coeffs[0])
    else:
        slope = 0.0

    if slope > 0.001:
        trend_direction = 'degrading'
    elif slope < -0.001:
        trend_direction = 'improving'
    else:
        trend_direction = 'stable'

    # 마지막 경보 시각
    last_alert_ts = None
    for r in reversed(filtered):
        if r.get('status', '') in alert_statuses:
            last_alert_ts = r['ts']
            break

    stats = {
        "mean": round(float(np.mean(values)), 4),
        "std": round(float(np.std(values)), 4),
        "min": round(float(np.min(values)), 4),
        "max": round(float(np.max(values)), 4),
        "p50": round(p50, 4),
        "p95": round(p95, 4),
        "anomaly_rate": round(anomaly_rate, 4),
        "trend_slope": round(slope, 6),
        "trend_direction": trend_direction,
        "alert_count": alert_count,
        "last_alert_ts": last_alert_ts,
    }

    summary = (
        f"{machine_id} {signal_type} {period_hours}h 통계: "
        f"평균 {stats['mean']:.3f}, 최대 {stats['max']:.3f}, "
        f"경보 {alert_count}회, 추세 {trend_direction}"
    )

    return {
        "tool": "get_signal_statistics",
        "machine_id": machine_id,
        "signal_type": signal_type,
        "period_hours": period_hours,
        "sample_count": len(filtered),
        "statistics": stats,
        "summary": summary
    }


# ── 3. 트렌드 분석 ─────────────────────────────────────────────

def get_trend_analysis(
    machine_id: str,
    metric: str = 'anomaly_score',
    period_days: int = 7
) -> dict:
    """
    [Tool] 일별 평균 집계 후 트렌드 분석 + 24h 예측.

    Args:
        machine_id: 설비 ID
        metric: 분석 메트릭 (anomaly_score | rul_days | defect_rate)
        period_days: 분석 기간 (기본 7일)

    Returns:
        dict: {"daily_values": [...], "trend": {...}, "forecast": {...}}
    """
    # metric → signal_type 매핑
    metric_to_signal = {
        'anomaly_score': 'anomaly',
        'rul_days': 'rul',
        'defect_rate': 'defect',
        'defect_count': 'detection',
    }
    signal_type = metric_to_signal.get(metric, 'anomaly')

    cutoff = datetime.now() - timedelta(days=period_days)
    history = get_signal_history(machine_id, signal_type, last_n=9999)
    records = history['records']

    # 일별 버킷 집계
    daily_buckets: dict = {}
    for r in records:
        try:
            ts = datetime.fromisoformat(r['ts'])
            if ts < cutoff:
                continue
            day = ts.strftime('%Y-%m-%d')
            if day not in daily_buckets:
                daily_buckets[day] = []
            daily_buckets[day].append(r)
        except (ValueError, KeyError):
            pass

    alert_statuses = {'ANOMALY', 'ALERT', 'HIGH', 'CRITICAL'}
    daily_values = []
    for day in sorted(daily_buckets.keys()):
        recs = daily_buckets[day]
        vals = [r['value'] for r in recs]
        alert_c = sum(1 for r in recs if r.get('status', '') in alert_statuses)
        daily_values.append({
            "date": day,
            "mean": round(float(np.mean(vals)), 4),
            "max": round(float(np.max(vals)), 4),
            "min": round(float(np.min(vals)), 4),
            "alert_count": alert_c,
        })

    # 트렌드 계산
    if len(daily_values) >= 2:
        y = np.array([d['mean'] for d in daily_values])
        x = np.arange(len(y))
        coeffs = np.polyfit(x, y, 1)
        slope = float(coeffs[0])
        first_val = y[0]
        last_val = y[-1]
        change_pct = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0.0

        # 24h 예측 (외삽)
        forecast_val = float(np.polyval(coeffs, len(y)))

        if slope > 0.005:
            risk_trajectory = 'escalating'
        elif slope < -0.005:
            risk_trajectory = 'recovering'
        else:
            risk_trajectory = 'stable'

        trend = {
            "slope": round(slope, 6),
            "change_pct": round(change_pct, 2),
            "risk_trajectory": risk_trajectory,
            "period_start": daily_values[0]['date'],
            "period_end": daily_values[-1]['date'],
        }
        forecast = {
            "forecast_24h": round(forecast_val, 4),
            "forecast_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "confidence": "medium",
        }
    else:
        trend = {"slope": 0, "change_pct": 0, "risk_trajectory": "stable"}
        forecast = {"forecast_24h": None, "forecast_date": None, "confidence": "low"}

    summary = (
        f"{machine_id} {metric} {period_days}일 트렌드: "
        f"{trend.get('risk_trajectory', 'stable')}, "
        f"변화율 {trend.get('change_pct', 0):+.1f}%, "
        f"내일 예측 {forecast.get('forecast_24h', 'N/A')}"
    )

    return {
        "tool": "get_trend_analysis",
        "machine_id": machine_id,
        "metric": metric,
        "period_days": period_days,
        "daily_values": daily_values,
        "trend": trend,
        "forecast": forecast,
        "summary": summary
    }


# ── 4. 설비 비교 ───────────────────────────────────────────────

def compare_machines(
    machine_ids: list,
    metric: str = 'anomaly_score',
    period_hours: int = 24
) -> dict:
    """
    [Tool] 여러 설비의 동일 메트릭 비교.

    Args:
        machine_ids: 설비 ID 목록 (예: ['M001', 'M002', 'M003'])
        metric: 비교 메트릭
        period_hours: 비교 기간 (기본 24h)

    Returns:
        dict: {"ranking": [...], "worst": ..., "best": ...}
    """
    metric_to_signal = {
        'anomaly_score': 'anomaly',
        'rul_days': 'rul',
        'defect_rate': 'defect',
    }
    signal_type = metric_to_signal.get(metric, 'anomaly')

    results = []
    for mid in machine_ids:
        stats = get_signal_statistics(mid, signal_type, period_hours=period_hours)
        s = stats['statistics']
        # 위험 정도: 평균값 기준 (anomaly/defect는 높을수록 위험, rul은 낮을수록 위험)
        if signal_type == 'rul':
            risk_val = -s['mean']  # rul 낮을수록 위험
        else:
            risk_val = s['mean']

        results.append({
            "machine_id": mid,
            "mean": s['mean'],
            "max": s['max'],
            "alert_count": s['alert_count'],
            "trend_direction": s['trend_direction'],
            "_risk_val": risk_val,
        })

    # 위험 순으로 정렬 (내림차순)
    results.sort(key=lambda r: r['_risk_val'], reverse=True)

    ranking = []
    for i, r in enumerate(results):
        status = "CRITICAL" if r['mean'] > 0.75 else ("WARNING" if r['mean'] > 0.5 else "NORMAL")
        if signal_type == 'rul':
            status = "CRITICAL" if r['mean'] < 10 else ("WARNING" if r['mean'] < 20 else "NORMAL")
        ranking.append({
            "rank": i + 1,
            "machine_id": r['machine_id'],
            "mean": r['mean'],
            "max": r['max'],
            "alert_count": r['alert_count'],
            "trend_direction": r['trend_direction'],
            "status": status,
        })
        # 내부용 임시 키 제거
        r.pop('_risk_val', None)

    worst = ranking[0]['machine_id'] if ranking else None
    best = ranking[-1]['machine_id'] if ranking else None

    return {
        "tool": "compare_machines",
        "metric": metric,
        "period_hours": period_hours,
        "ranking": ranking,
        "worst": worst,
        "best": best,
        "summary": f"설비 비교 ({metric}, {period_hours}h): 최위험={worst}, 최양호={best}"
    }


# ── 5. 의사결정 ────────────────────────────────────────────────

def get_maintenance_decision(machine_id: str) -> dict:
    """
    [Tool] 이상탐지 + RUL + 정비이력을 종합한 의사결정.

    Args:
        machine_id: 설비 ID

    Returns:
        dict: {decision, urgency_score, reasoning, cost_analysis,
               recommended_date, action_items, risk_if_ignored}
    """
    # 현재 상태 수집
    anomaly_stats = get_signal_statistics(machine_id, 'anomaly', period_hours=72)
    rul_stats = get_signal_statistics(machine_id, 'rul', period_hours=72)
    maint_history = get_signal_history(machine_id, 'maintenance', last_n=10)
    trend = get_trend_analysis(machine_id, 'anomaly_score', period_days=7)

    a_stat = anomaly_stats['statistics']
    r_stat = rul_stats['statistics']
    trend_info = trend['trend']

    # 의사결정 점수 (0-100)
    urgency_score = 0
    reasoning = []

    # 이상점수 평가 (최대 40점)
    anomaly_mean = a_stat['mean']
    anomaly_max = a_stat['max']
    if anomaly_max > 0.90:
        urgency_score += 40
        reasoning.append(f"이상점수 최대값 {anomaly_max:.2f}가 임계값 0.75 크게 초과 (위험)")
    elif anomaly_max > 0.75:
        urgency_score += 25
        reasoning.append(f"이상점수 최대값 {anomaly_max:.2f}가 임계값 0.75 초과")
    elif anomaly_mean > 0.60:
        urgency_score += 15
        reasoning.append(f"이상점수 평균 {anomaly_mean:.2f}이 경계값 0.60 초과 (주의)")

    # RUL 평가 (최대 35점)
    rul_mean = r_stat['mean']
    if rul_mean < 7:
        urgency_score += 35
        reasoning.append(f"잔여수명 {rul_mean:.1f}일 — 7일 이내 고장 예상")
    elif rul_mean < 14:
        urgency_score += 20
        reasoning.append(f"잔여수명 {rul_mean:.1f}일 — 2주 이내 정비 필요")
    elif rul_mean < 30:
        urgency_score += 10
        reasoning.append(f"잔여수명 {rul_mean:.1f}일 — 30일 이내 예방정비 권장")

    # 경보 빈도 (최대 15점)
    alert_count = a_stat['alert_count']
    if alert_count >= 5:
        urgency_score += 15
        reasoning.append(f"최근 72h 경보 {alert_count}회 — 반복 이상")
    elif alert_count >= 2:
        urgency_score += 8
        reasoning.append(f"최근 72h 경보 {alert_count}회")

    # 트렌드 (최대 10점)
    if trend_info.get('risk_trajectory') == 'escalating':
        urgency_score += 10
        reasoning.append(f"이상 트렌드 악화 중 (7일 변화율 {trend_info.get('change_pct', 0):+.1f}%)")

    # 마지막 정비 경과 (최대 5점)
    maint_records = maint_history['records']
    if maint_records:
        last_maint_ts = max(r['ts'] for r in maint_records)
        try:
            last_maint_dt = datetime.fromisoformat(last_maint_ts)
            days_since = (datetime.now() - last_maint_dt).days
            if days_since > 30:
                urgency_score += 5
                reasoning.append(f"마지막 정비 {days_since}일 경과")
        except ValueError:
            pass

    urgency_score = min(100, urgency_score)

    # 의사결정
    if urgency_score >= 70:
        decision = "즉시정비(긴급)"
        days_offset = 1
    elif urgency_score >= 40:
        decision = "7일이내 계획정비"
        days_offset = 7
    elif urgency_score >= 20:
        decision = "30일이내 예방정비"
        days_offset = 30
    else:
        decision = "지속모니터링"
        days_offset = None

    recommended_date = (
        (datetime.now() + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        if days_offset is not None else None
    )

    # 비용 분석
    emergency_cost = 2_000_000
    planned_cost = 800_000
    saving = emergency_cost - planned_cost

    cost_analysis = {
        "emergency_cost": emergency_cost,
        "planned_cost": planned_cost,
        "saving_by_planning": saving,
    }

    # 권장 조치
    action_items = []
    if anomaly_max > 0.75:
        action_items.append("베어링 마모 상태 정밀 점검")
    if rul_mean < 20:
        action_items.append("베어링 교체 (예방 교체)")
    action_items.extend([
        "오일 상태 점검 및 필요시 교체",
        "진동 센서 재캘리브레이션",
        "냉각 시스템 청소",
    ])

    # 방치 시 리스크
    est_days_to_failure = max(1, int(rul_mean))
    risk_if_ignored = (
        f"예상 고장까지 약 {est_days_to_failure}일, "
        f"예상 긴급 수리비 {emergency_cost:,}원 (계획 정비 대비 {saving:,}원 초과)"
    )

    if not reasoning:
        reasoning.append("모든 지표 정상 범위 — 정기 모니터링 유지")

    return {
        "tool": "get_maintenance_decision",
        "machine_id": machine_id,
        "decision": decision,
        "urgency_score": urgency_score,
        "reasoning": reasoning,
        "cost_analysis": cost_analysis,
        "recommended_date": recommended_date,
        "action_items": action_items,
        "risk_if_ignored": risk_if_ignored,
        "summary": f"{machine_id} 의사결정: {decision} (긴급도 {urgency_score}/100)"
    }


# ── 6. 설비 건강도 보고서 ─────────────────────────────────────

def generate_equipment_health_report(machine_id: str, period_days: int = 7) -> str:
    """
    [Tool] 마크다운 형식 설비 건강도 보고서 생성.

    Args:
        machine_id: 설비 ID
        period_days: 보고 기간 (기본 7일)

    Returns:
        str: 마크다운 보고서
    """
    now = datetime.now()
    start_dt = now - timedelta(days=period_days)
    start_str = start_dt.strftime('%Y-%m-%d')
    end_str = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d %H:%M')

    # 데이터 수집
    a_stats = get_signal_statistics(machine_id, 'anomaly', period_hours=period_days * 24)
    r_stats = get_signal_statistics(machine_id, 'rul', period_hours=period_days * 24)
    trend = get_trend_analysis(machine_id, 'anomaly_score', period_days=period_days)
    decision = get_maintenance_decision(machine_id)

    a_s = a_stats['statistics']
    r_s = r_stats['statistics']
    d_info = trend['daily_values']
    t_info = trend['trend']
    dec = decision

    # 현재 상태 (최근 1개)
    recent_history = get_signal_history(machine_id, 'anomaly', last_n=1)
    current_score = (
        recent_history['records'][-1]['value']
        if recent_history['records'] else a_s['mean']
    )
    current_status = "ANOMALY" if current_score > 0.75 else "NORMAL"

    recent_rul = get_signal_history(machine_id, 'rul', last_n=1)
    current_rul = (
        recent_rul['records'][-1]['value']
        if recent_rul['records'] else r_s['mean']
    )

    # 이상탐지 일별 테이블
    anomaly_table_rows = ""
    if d_info:
        for day_data in d_info:
            status_mark = "⚠️" if day_data['alert_count'] > 0 else "✅"
            anomaly_table_rows += (
                f"| {day_data['date']} "
                f"| {day_data['max']:.3f} "
                f"| {day_data['alert_count']} "
                f"| {status_mark} |\n"
            )
    else:
        anomaly_table_rows = "| (데이터 없음) | - | - | - |\n"

    # RUL 일별 테이블
    rul_trend = get_trend_analysis(machine_id, 'rul_days', period_days=period_days)
    rul_table_rows = ""
    for day_data in rul_trend['daily_values']:
        conf_str = "83%"
        rul_table_rows += (
            f"| {day_data['date']} "
            f"| {day_data['mean']:.1f} "
            f"| {conf_str} |\n"
        )
    if not rul_table_rows:
        rul_table_rows = "| (데이터 없음) | - | - |\n"

    # 비용 분석
    ca = dec['cost_analysis']
    decision_urgency_bar = "█" * (dec['urgency_score'] // 10) + "░" * (10 - dec['urgency_score'] // 10)

    # 근거 목록
    reasoning_md = "\n".join(f"- {r}" for r in dec['reasoning'])
    action_md = "\n".join(f"{i+1}. {a}" for i, a in enumerate(dec['action_items']))

    trend_arrow = {
        'escalating': '↗️ 악화 중',
        'stable': '→ 안정',
        'recovering': '↘️ 개선 중',
    }.get(t_info.get('risk_trajectory', 'stable'), '→')

    report = f"""# 설비 {machine_id} 건강도 보고서
**보고 기간**: {start_str} ~ {end_str}
**보고 시각**: {now_str}

---

## 1. 현황 요약

| 항목 | 현재값 | {period_days}일 평균 | 추세 |
|------|--------|---------|------|
| 이상탐지 점수 | {current_score:.3f} | {a_s['mean']:.3f} | {trend_arrow} |
| 잔여수명(RUL) | {current_rul:.1f}일 | {r_s['mean']:.1f}일 | {rul_trend['trend'].get('risk_trajectory', '-')} |
| 경보 횟수 ({period_days}일) | - | {a_s['alert_count']}회 | - |
| 종합 긴급도 | {dec['urgency_score']}/100 | - | - |

**현재 상태**: {"🔴 이상 감지" if current_status == "ANOMALY" else "🟢 정상"}
**의사결정**: **{dec['decision']}**

---

## 2. 이상탐지 이력 (최근 {period_days}일)

| 날짜 | 최대 이상점수 | 경보 횟수 | 상태 |
|------|-------------|---------|------|
{anomaly_table_rows}
> 임계값: 0.75 (이 값 초과 시 ANOMALY 경보)

---

## 3. 잔여수명(RUL) 추이

| 날짜 | 예측 잔여수명(일) | 신뢰도 |
|------|----------------|--------|
{rul_table_rows}
> 내일 예측: {rul_trend['forecast'].get('forecast_24h', 'N/A')}일

---

## 4. 의사결정 및 권고사항

**결정**: {dec['decision']}
**긴급도**: {dec['urgency_score']}/100 `[{decision_urgency_bar}]`
**권장 정비일**: {dec['recommended_date'] or '해당 없음'}

**근거**:
{reasoning_md}

**권장 조치**:
{action_md}

**비용 분석**:
- 계획 정비 비용: {ca['planned_cost']:,}원
- 긴급 정비 비용: {ca['emergency_cost']:,}원
- 계획 정비 시 절감액: **{ca['saving_by_planning']:,}원**

**방치 시 리스크**: {dec['risk_if_ignored']}
"""

    return report


# ── 7. 품질 보고서 ─────────────────────────────────────────────

def generate_quality_report(line_id: str, period_days: int = 7) -> str:
    """
    [Tool] 마크다운 형식 품질 보고서 생성.

    Args:
        line_id: 생산 라인 ID (예: 'LINE-A')
        period_days: 보고 기간

    Returns:
        str: 마크다운 보고서
    """
    now = datetime.now()
    start_str = (now - timedelta(days=period_days)).strftime('%Y-%m-%d')
    end_str = now.strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d %H:%M')

    stats = get_signal_statistics(line_id, 'defect', period_hours=period_days * 24)
    trend = get_trend_analysis(line_id, 'defect_rate', period_days=period_days)

    s = stats['statistics']
    d_vals = trend['daily_values']
    t_info = trend['trend']

    target_rate = 0.03  # 목표 불량률 3%
    current_pct = s['mean'] * 100
    target_met = "✅ 달성" if current_pct < target_rate * 100 else "❌ 미달성"

    # 일별 테이블
    daily_rows = ""
    for dv in d_vals:
        rate_pct = dv['mean'] * 100
        status_icon = "⚠️" if rate_pct > target_rate * 100 else "✅"
        daily_rows += f"| {dv['date']} | {rate_pct:.2f}% | {dv['alert_count']} | {status_icon} |\n"
    if not daily_rows:
        daily_rows = "| (데이터 없음) | - | - | - |\n"

    # 불량 유형 (시뮬레이션 값)
    total_defects = int(s['mean'] * 500 * period_days)
    defect_types = {
        "표면 스크래치": int(total_defects * 0.40),
        "치수 불량": int(total_defects * 0.30),
        "색상 불량": int(total_defects * 0.20),
        "기타": int(total_defects * 0.10),
    }
    dominant_type = max(defect_types, key=defect_types.get)
    defect_type_rows = "\n".join(
        f"| {k} | {v}개 | {v/max(total_defects,1)*100:.1f}% |"
        for k, v in defect_types.items()
    )

    trend_arrow = {
        'escalating': '↗️ 악화', 'stable': '→ 유지', 'recovering': '↘️ 개선'
    }.get(t_info.get('risk_trajectory', 'stable'), '→')

    # 개선 권고
    recommendations = []
    if s['mean'] > target_rate:
        recommendations.append("공정 파라미터 재검토 — 온도/압력/속도 설정값 점검")
    if s['alert_count'] > 3:
        recommendations.append(f"주요 불량 유형 '{dominant_type}' 집중 개선 조치 필요")
    if t_info.get('risk_trajectory') == 'escalating':
        recommendations.append("불량률 상승 추세 — 긴급 품질 회의 소집 권장")
    if not recommendations:
        recommendations.append("목표 불량률 유지 — 현 공정 파라미터 유지")

    rec_md = "\n".join(f"{i+1}. {r}" for i, r in enumerate(recommendations))

    report = f"""# 생산 라인 {line_id} 품질 보고서
**보고 기간**: {start_str} ~ {end_str}
**보고 시각**: {now_str}

---

## 1. 품질 현황 요약

| 항목 | 값 |
|------|-----|
| 평균 불량률 | {current_pct:.2f}% |
| 최대 불량률 | {s['max']*100:.2f}% |
| 목표 불량률 | {target_rate*100:.1f}% |
| 목표 달성 여부 | {target_met} |
| 경보 발생 | {s['alert_count']}회 |
| 추세 | {trend_arrow} |

---

## 2. 일별 불량률 이력

| 날짜 | 불량률 | 경보 횟수 | 상태 |
|------|--------|---------|------|
{daily_rows}
---

## 3. 불량 유형 분포 ({period_days}일 합계)

| 불량 유형 | 발생 건수 | 비율 |
|---------|---------|------|
{defect_type_rows}

> 가장 빈번한 불량 유형: **{dominant_type}** ({defect_types[dominant_type]}건)

---

## 4. 개선 권고사항

{rec_md}

**다음 품질 검토 일정**: {(now + timedelta(days=7)).strftime('%Y-%m-%d')}
"""

    return report


# ── 8. 공장 주간 요약 ──────────────────────────────────────────

def generate_factory_weekly_summary() -> str:
    """
    [Tool] 전체 공장 주간 요약 보고서 (마크다운).

    Returns:
        str: 마크다운 보고서
    """
    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    now_str = now.strftime('%Y-%m-%d %H:%M')

    # 설비 목록 (시뮬레이션)
    machines = ['M001', 'M002', 'M003']
    lines = ['LINE-A', 'LINE-B']

    # 설비별 상태 수집
    machine_summaries = []
    critical_count = warning_count = normal_count = 0
    total_alerts_this_week = 0

    for mid in machines:
        stats = get_signal_statistics(mid, 'anomaly', period_hours=168)
        s = stats['statistics']
        a_mean = s['mean']
        if a_mean > 0.75:
            status = "CRITICAL"
            critical_count += 1
        elif a_mean > 0.50:
            status = "WARNING"
            warning_count += 1
        else:
            status = "NORMAL"
            normal_count += 1
        total_alerts_this_week += s['alert_count']
        machine_summaries.append({
            "machine_id": mid,
            "status": status,
            "mean_score": a_mean,
            "alert_count": s['alert_count'],
        })

    # 품질 현황
    quality_summaries = []
    for lid in lines:
        q_stats = get_signal_statistics(lid, 'defect', period_hours=168)
        q_s = q_stats['statistics']
        quality_summaries.append({
            "line_id": lid,
            "mean_defect_rate": q_s['mean'],
            "alert_count": q_s['alert_count'],
        })

    # 최우선 조치 Top 3
    decisions = []
    for mid in machines:
        dec = get_maintenance_decision(mid)
        decisions.append(dec)
    decisions.sort(key=lambda d: d['urgency_score'], reverse=True)
    top3 = decisions[:3]

    top3_md = ""
    for i, d in enumerate(top3):
        top3_md += (
            f"{i+1}. **{d['machine_id']}** — {d['decision']} "
            f"(긴급도 {d['urgency_score']}/100): "
            f"{d['reasoning'][0] if d['reasoning'] else '-'}\n"
        )

    # 설비 상태 테이블
    machine_table = ""
    for ms in machine_summaries:
        icon = {"CRITICAL": "🔴", "WARNING": "🟠", "NORMAL": "🟢"}.get(ms['status'], "")
        machine_table += (
            f"| {ms['machine_id']} | {icon} {ms['status']} "
            f"| {ms['mean_score']:.3f} | {ms['alert_count']}회 |\n"
        )

    # 품질 테이블
    quality_table = ""
    for qs in quality_summaries:
        rate_pct = qs['mean_defect_rate'] * 100
        status_icon = "⚠️" if rate_pct > 3.0 else "✅"
        quality_table += (
            f"| {qs['line_id']} | {rate_pct:.2f}% | {qs['alert_count']}회 | {status_icon} |\n"
        )

    # 다음 주 예정 정비
    planned_maintenance = ""
    for d in decisions:
        if d['recommended_date'] and d['decision'] != "지속모니터링":
            planned_maintenance += (
                f"- {d['recommended_date']}: {d['machine_id']} — {d['decision']}\n"
            )
    if not planned_maintenance:
        planned_maintenance = "- 예정된 정비 없음\n"

    report = f"""# 공장 주간 종합 보고서
**보고 기간**: {week_start} ~ {now.strftime('%Y-%m-%d')}
**작성 시각**: {now_str}

---

## 1. 설비 가동 현황

| 설비 | 상태 | 평균 이상점수 | 주간 경보 |
|------|------|------------|---------|
{machine_table}
**요약**: 🔴 CRITICAL {critical_count}대 / 🟠 WARNING {warning_count}대 / 🟢 NORMAL {normal_count}대
**이번 주 총 경보**: {total_alerts_this_week}회

---

## 2. 품질 현황

| 라인 | 평균 불량률 | 주간 경보 | 목표(3%) 달성 |
|------|----------|---------|-------------|
{quality_table}
---

## 3. 최우선 조치 사항 Top 3

{top3_md}
---

## 4. 다음 주 예정 정비 일정

{planned_maintenance}---

*본 보고서는 제조 AI 시스템에 의해 자동 생성되었습니다.*
"""

    return report


# ── 9. 유지보수 로그 검색 ──────────────────────────────────────

# 내장 샘플 이력 데이터 (ChromaDB 없을 때 fallback)
_SAMPLE_MAINTENANCE_LOG = [
    {
        "date": "2026-01-15",
        "machine_id": "M001",
        "description": "베어링 과열 및 진동 증가. 이상탐지 점수 0.88 초과.",
        "action_taken": "베어링 교체 (6205ZZ → 6205-2RS), 오일 교체",
        "result": "정상 복구. 이상점수 0.25로 감소.",
        "cost": 650000
    },
    {
        "date": "2026-02-03",
        "machine_id": "M002",
        "description": "오일 누유 감지. 정기 점검 중 발견.",
        "action_taken": "씰(Seal) 교체, 오일 보충",
        "result": "누유 중단. 정상 운전 복귀.",
        "cost": 120000
    },
    {
        "date": "2026-02-20",
        "machine_id": "M001",
        "description": "진동 센서 드리프트. 측정값 불안정.",
        "action_taken": "진동 센서 재캘리브레이션, 브래킷 조임",
        "result": "센서 안정화. 측정 정확도 회복.",
        "cost": 50000
    },
    {
        "date": "2026-03-01",
        "machine_id": "M003",
        "description": "냉각 팬 소음 증가. 불균형 진동 발생.",
        "action_taken": "냉각 팬 블레이드 밸런싱, 볼트 조임",
        "result": "소음 50% 감소. 진동 정상 범위.",
        "cost": 80000
    },
    {
        "date": "2025-12-10",
        "machine_id": "M001",
        "description": "예방정비. 운전 시간 2000h 도달.",
        "action_taken": "오일 교체, 필터 교체, 전체 청소",
        "result": "예방정비 완료. 정상 운전.",
        "cost": 300000
    },
    {
        "date": "2026-01-28",
        "machine_id": "LINE-A",
        "description": "불량률 8% 초과. 표면 스크래치 급증.",
        "action_taken": "공구 교체, 절삭 속도 10% 감속, 냉각액 농도 재조정",
        "result": "불량률 2.5%로 정상화.",
        "cost": 200000
    },
]


def search_maintenance_log(
    query: str,
    machine_id: Optional[str] = None,
    top_k: int = 3
) -> dict:
    """
    [Tool] 유지보수 로그에서 유사 사례 검색.
    ChromaDB가 없으면 내장 샘플 이력으로 키워드 매칭.

    Args:
        query: 검색 쿼리 (예: '베어링 과열', '불량률 상승')
        machine_id: 특정 설비로 필터 (None이면 전체)
        top_k: 반환할 최대 결과 수

    Returns:
        dict: {"results": [{date, machine_id, description, action_taken, result}, ...]}
    """
    # ChromaDB 연동 시도 (없으면 fallback)
    results = []
    try:
        import chromadb  # noqa: F401
        # ChromaDB 연동 코드 (향후 구현)
        raise ImportError("ChromaDB 연동 미구현, fallback 사용")
    except ImportError:
        # 키워드 매칭 fallback
        query_lower = query.lower()
        query_tokens = set(query_lower.split())

        scored = []
        for log in _SAMPLE_MAINTENANCE_LOG:
            if machine_id and log.get('machine_id') != machine_id:
                continue
            # 점수: 쿼리 토큰이 설명/조치에 몇 개 포함되는지
            text = (log['description'] + ' ' + log['action_taken']).lower()
            score = sum(1 for tok in query_tokens if tok in text)
            if score > 0:
                scored.append((score, log))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [log for _, log in scored[:top_k]]

        # 결과가 없으면 상위 top_k 반환
        if not results:
            filtered = [
                l for l in _SAMPLE_MAINTENANCE_LOG
                if not machine_id or l.get('machine_id') == machine_id
            ]
            results = filtered[:top_k]

    return {
        "tool": "search_maintenance_log",
        "query": query,
        "machine_id": machine_id,
        "results": results,
        "count": len(results),
        "summary": f"검색 '{query}': {len(results)}건 유사 사례 발견"
    }


# ── 직접 실행 테스트 ───────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("analytics_tools.py 직접 실행 테스트")
    print("=" * 60)

    # 1. 이력 조회
    print("\n[1] 이력 조회 (anomaly, last 10)")
    h = get_signal_history("M001", "anomaly", last_n=10)
    print(f"  → {h['summary']}")
    print(f"  → 최근 레코드: {h['records'][-1] if h['records'] else 'N/A'}")

    # 2. 통계
    print("\n[2] 통계 분석 (7일)")
    st = get_signal_statistics("M001", "anomaly", period_hours=168)
    print(f"  → {st['summary']}")
    s = st['statistics']
    print(f"  → mean={s['mean']}, max={s['max']}, p95={s['p95']}, trend={s['trend_direction']}")

    # 3. 트렌드
    print("\n[3] 트렌드 분석 (7일)")
    tr = get_trend_analysis("M001", "anomaly_score", period_days=7)
    print(f"  → {tr['summary']}")

    # 4. 설비 비교
    print("\n[4] 설비 비교 (M001, M002, M003)")
    cmp = compare_machines(["M001", "M002", "M003"], "anomaly_score", 24)
    print(f"  → {cmp['summary']}")

    # 5. 의사결정
    print("\n[5] 의사결정")
    dec = get_maintenance_decision("M001")
    print(f"  → {dec['summary']}")
    print(f"  → 근거: {dec['reasoning']}")

    # 6. 설비 건강도 보고서
    print("\n[6] 설비 건강도 보고서 (첫 30줄)")
    report = generate_equipment_health_report("M001", period_days=7)
    lines = report.split('\n')
    for line in lines[:30]:
        print(line)
    print(f"  ... (총 {len(lines)}줄)")

    # 7. 품질 보고서
    print("\n[7] 품질 보고서 요약")
    qr = generate_quality_report("LINE-A", period_days=7)
    print(qr.split('\n')[0])
    print(f"  (총 {len(qr.split(chr(10)))}줄)")

    # 8. 공장 주간 요약
    print("\n[8] 공장 주간 요약 (첫 15줄)")
    ws = generate_factory_weekly_summary()
    for line in ws.split('\n')[:15]:
        print(line)

    # 9. 유지보수 로그 검색
    print("\n[9] 유지보수 로그 검색: '베어링 과열'")
    sr = search_maintenance_log("베어링 과열", machine_id=None, top_k=2)
    print(f"  → {sr['summary']}")
    for r in sr['results']:
        print(f"  [{r['date']}] {r['machine_id']}: {r['description'][:40]}...")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
