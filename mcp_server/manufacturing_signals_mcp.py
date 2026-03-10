"""
manufacturing_signals_mcp.py — 제조 신호 MCP 서버
Claude가 MCP 프로토콜로 Track A/B 신호를 조회할 수 있도록 서버 구현

실행 방법:
  pip install fastmcp
  python mcp_server/manufacturing_signals_mcp.py

Claude Code MCP 등록 (.claude/mcp_settings.json):
  {
    "mcpServers": {
      "manufacturing-signals": {
        "command": "python",
        "args": ["x1-s4-agent-react/mcp_server/manufacturing_signals_mcp.py"]
      }
    }
  }
"""
import sys
import os

# 상위 경로에서 signal_tools 임포트
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  fastmcp 미설치. pip install fastmcp 실행 후 재시도하세요.")

from tools.signal_tools import (
    get_anomaly_status,
    get_rul_prediction,
    get_maintenance_schedule,
    get_defect_rate,
    get_detection_results,
    get_manufacturing_dashboard,
)

if MCP_AVAILABLE:
    mcp = FastMCP("manufacturing-signals")

    @mcp.tool()
    def anomaly_status(machine_id: str = "M001") -> dict:
        """Track A-2: 설비 이상탐지(AutoEncoder) 결과 조회. 이상점수와 상태(NORMAL/ANOMALY) 반환."""
        return get_anomaly_status(machine_id)

    @mcp.tool()
    def rul_prediction(machine_id: str = "M001") -> dict:
        """Track A-2: 설비 잔여수명(RUL) 예측 결과 조회. LSTM 기반 잔여수명(일) 반환."""
        return get_rul_prediction(machine_id)

    @mcp.tool()
    def maintenance_schedule(machine_id: str = "M001") -> dict:
        """Track A-2: 예지보전 정비 스케줄 조회. 다음 정비일, 우선순위, 권장 조치 반환."""
        return get_maintenance_schedule(machine_id)

    @mcp.tool()
    def defect_rate(line_id: str = "LINE-A") -> dict:
        """Track B-1: CNN ResNet18 품질검사 결과 조회. 불량률, 등급, 불량 유형별 집계 반환."""
        return get_defect_rate(line_id)

    @mcp.tool()
    def detection_results(line_id: str = "LINE-B") -> dict:
        """Track B-2: YOLOv8 실시간 객체탐지 결과 조회. 탐지 불량 개수, 종류, mAP 반환."""
        return get_detection_results(line_id)

    @mcp.tool()
    def manufacturing_dashboard() -> dict:
        """제조 현장 통합 대시보드: Track A(설비) + Track B(품질) 전체 신호 종합 분석 및 권장사항 반환."""
        return get_manufacturing_dashboard()

    if __name__ == "__main__":
        mcp.run()
else:
    # fastmcp 없을 때 기본 테스트
    if __name__ == "__main__":
        print("=== MCP 없이 직접 테스트 ===")
        dashboard = get_manufacturing_dashboard()
        print(f"종합 상태: {dashboard['summary']}")
