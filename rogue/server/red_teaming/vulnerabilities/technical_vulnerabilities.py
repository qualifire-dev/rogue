"""
Technical Vulnerabilities.

SQL Injection, Shell Injection, SSRF, Debug Access.
"""

from enum import Enum
from typing import List, Optional

from ..metrics.code_injection_metric import CodeInjectionMetric
from .base_vulnerability import BaseVulnerability


class SQLInjectionType(Enum):
    ERROR_BASED = "error_based"
    UNION_BASED = "union_based"
    BLIND = "blind"


class SQLInjection(BaseVulnerability):
    name = "SQL Injection"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in SQLInjectionType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = CodeInjectionMetric(types=["sql", "xss", "html_injection"])


class ShellInjectionType(Enum):
    COMMAND_EXEC = "command_execution"
    FILE_ACCESS = "file_access"


class ShellInjection(BaseVulnerability):
    name = "Shell Injection"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in ShellInjectionType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = CodeInjectionMetric(
            types=["shell", "path", "xss", "html_injection"],
        )


class SSRFType(Enum):
    INTERNAL_ACCESS = "internal_access"
    CLOUD_METADATA = "cloud_metadata"


class SSRF(BaseVulnerability):
    name = "SSRF"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in SSRFType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = CodeInjectionMetric(types=["cloud"])


class DebugAccessType(Enum):
    STACK_TRACE = "stack_trace"
    CONFIG_DUMP = "config_dump"


class DebugAccess(BaseVulnerability):
    name = "Debug Access"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in DebugAccessType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        # We can use CodeInjectionMetric or a new one. CodeInjection checks for some error patterns.  # noqa: E501
        self.metric = CodeInjectionMetric(types=["sql", "shell"])
