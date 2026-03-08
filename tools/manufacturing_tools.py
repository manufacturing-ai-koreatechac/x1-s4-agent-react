"""제조 현장 특화 Agent Tools

각 Tool은 실제 현장 시스템(MES, QMS, ERP)과 연결하는 인터페이스입니다.
현재는 Mock 데이터를 사용하며, 실제 운영 시 API 연동으로 교체합니다.
"""


def quality_inspector(product_id: str) -> str:
    """
    특정 제품의 품질 검사 결과 조회 (QMS 연동)

    Args:
        product_id: 제품 ID (예: 'P001', 'P002')

    Returns:
        품질 검사 결과 문자열 (상태, 불량률, 검사기 정보 포함)

    Example:
        >>> quality_inspector('P001')
        '✅ 제품 P001: 합격 (불량률: 0.02, 검사기: AI-Vision-B1)'
        >>> quality_inspector('P002')
        '❌ 제품 P002: 불합격 (불량률: 0.15, 검사기: AI-Vision-B1)'
    """
    mock_data = {
        "P001": {"status": "합격", "defect_rate": 0.02, "inspector": "AI-Vision-B1"},
        "P002": {"status": "불합격", "defect_rate": 0.15, "inspector": "AI-Vision-B1"},
        "P003": {"status": "합격", "defect_rate": 0.01, "inspector": "AI-Vision-B2"},
        "P004": {"status": "보류", "defect_rate": 0.08, "inspector": "AI-Vision-B1"},
    }
    result = mock_data.get(product_id, {"status": "미검사", "defect_rate": None, "inspector": "N/A"})
    status_icon = {"합격": "✅", "불합격": "❌", "보류": "⏳", "미검사": "❓"}.get(result["status"], "")
    return f"{status_icon} 제품 {product_id}: {result['status']} (불량률: {result.get('defect_rate', 'N/A')}, 검사기: {result['inspector']})"


def anomaly_alerter(location: str, severity: str = "warning") -> str:
    """
    설비 이상 알림 전송 (알림 시스템 연동)

    Args:
        location: 이상 발생 위치 (예: '라인 A 베어링', '압축기 3호')
        severity: 심각도 — 'critical' | 'warning' | 'info' (기본값: 'warning')

    Returns:
        알림 전송 결과 문자열 (수신자 정보 포함)

    Example:
        >>> anomaly_alerter('라인 A 베어링', 'critical')
        '🔴 [CRITICAL] 라인 A 베어링 이상 감지 → 알림 전송 완료 (수신: 정비팀장, 생산관리자, 공장장)'
    """
    icons = {"critical": "🔴", "warning": "🟠", "info": "🟡"}
    icon = icons.get(severity, "⚪")
    recipients = {
        "critical": "정비팀장, 생산관리자, 공장장",
        "warning": "정비팀장, 생산관리자",
        "info": "정비팀",
    }.get(severity, "정비팀")
    return f"{icon} [{severity.upper()}] {location} 이상 감지 → 알림 전송 완료 (수신: {recipients})"


def inventory_checker(part_name: str) -> str:
    """
    부품 재고 확인 (ERP 연동)

    Args:
        part_name: 부품명 (예: '베어링 6205', '오일씰 A형')

    Returns:
        재고 현황 문자열 (수량, 상태, 창고 위치 포함)

    Example:
        >>> inventory_checker('베어링 6205')
        '베어링 6205: 12개 ✅ 충분 | 위치: 창고 A-3'
        >>> inventory_checker('오일씰 A형')
        '오일씰 A형: 3개 ⚠️ 부족 (발주 필요) | 위치: 창고 B-1'
    """
    inventory = {
        "베어링 6205": {"stock": 12, "min_stock": 5, "unit": "개", "location": "창고 A-3"},
        "오일씰 A형": {"stock": 3, "min_stock": 10, "unit": "개", "location": "창고 B-1"},
        "V벨트 B형": {"stock": 8, "min_stock": 5, "unit": "개", "location": "창고 A-5"},
        "필터 FE-100": {"stock": 0, "min_stock": 3, "unit": "개", "location": "입고 대기"},
    }
    item = inventory.get(part_name)
    if not item:
        return f"'{part_name}' 재고 정보 없음 (ERP 직접 확인 필요)"

    if item["stock"] == 0:
        status = "🚫 재고 없음 (긴급 발주)"
    elif item["stock"] >= item["min_stock"]:
        status = "✅ 충분"
    else:
        status = "⚠️ 부족 (발주 필요)"

    return f"{part_name}: {item['stock']}{item['unit']} {status} | 위치: {item['location']}"


def work_order_creator(task: str, priority: str = "normal") -> str:
    """
    작업 지시서 생성 (MES 연동)

    Args:
        task: 작업 내용 (예: '라인 A 베어링 교체', '압축기 3호 점검')
        priority: 우선순위 — 'urgent' | 'normal' | 'low' (기본값: 'normal')

    Returns:
        작업 지시서 ID 및 상세 정보 문자열

    Example:
        >>> work_order_creator('베어링 교체', 'urgent')
        '📋 작업 지시서 생성 완료: WO-03081423 | 내용: 베어링 교체 | 우선순위: 🔴 urgent | 예상 소요: 2h'
    """
    import datetime

    order_id = f"WO-{datetime.datetime.now().strftime('%m%d%H%M')}"
    priority_icon = {"urgent": "🔴", "normal": "🟡", "low": "🟢"}.get(priority, "⚪")
    estimated_hours = {"urgent": 2, "normal": 8, "low": 24}.get(priority, 8)
    return (
        f"📋 작업 지시서 생성 완료: {order_id} | "
        f"내용: {task} | "
        f"우선순위: {priority_icon} {priority} | "
        f"예상 소요: {estimated_hours}h"
    )


# ===== 모든 Tool 목록 =====
ALL_TOOLS = [quality_inspector, anomaly_alerter, inventory_checker, work_order_creator]


if __name__ == "__main__":
    # 각 Tool 테스트
    print("=== 제조 현장 Tool 테스트 ===\n")

    print("[quality_inspector]")
    print(quality_inspector("P001"))
    print(quality_inspector("P002"))
    print()

    print("[anomaly_alerter]")
    print(anomaly_alerter("라인 A 베어링", "critical"))
    print(anomaly_alerter("냉각 팬", "warning"))
    print()

    print("[inventory_checker]")
    print(inventory_checker("베어링 6205"))
    print(inventory_checker("오일씰 A형"))
    print(inventory_checker("필터 FE-100"))
    print()

    print("[work_order_creator]")
    print(work_order_creator("라인 A 베어링 교체", "urgent"))
    print(work_order_creator("필터 정기 교체", "low"))
