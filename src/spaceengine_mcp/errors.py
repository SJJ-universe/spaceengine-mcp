"""SpaceEngine MCP — 구조화된 에러 유형"""


class MCPError(Exception):
    """MCP 에러 기본 클래스"""
    error_type: str = "mcp_error"
    http_status: int = 500


class SENotFoundError(MCPError):
    """SpaceEngine 창을 찾을 수 없음"""
    error_type = "se_not_found"
    http_status = 502  # Bad Gateway (SE가 게이트웨이 역할)


class ClipboardError(MCPError):
    """클립보드 접근 실패"""
    error_type = "clipboard_error"
    http_status = 500


class CommandTimeoutError(MCPError):
    """명령어 실행 시간 초과"""
    error_type = "command_timeout"
    http_status = 408


class InvalidCommandError(MCPError):
    """허용되지 않은 명령어"""
    error_type = "invalid_command"
    http_status = 422


class ConfigError(MCPError):
    """설정 파일 접근/수정 오류"""
    error_type = "config_error"
    http_status = 500
