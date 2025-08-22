"""
클라우드 민감정보 패턴 정의

ref-1 Kong 플러그인의 patterns.lua를 Python으로 포팅
실제 AWS 리소스 패턴만 정의, 정확한 정규식 매칭
"""

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, NamedTuple, Optional, Any


@dataclass
class PatternDefinition:
    """패턴 정의 클래스"""

    pattern: str  # 정규식 패턴
    replacement: str  # 대체 형식 (예: "ec2-{:03d}")
    type: str  # 리소스 타입
    description: str  # 설명
    priority: int  # 우선순위 (낮을수록 먼저 처리)
    validator: Optional[Callable[[str], tuple[bool, str]]] = None  # 추가 검증 함수


class CloudPatterns:
    """클라우드 리소스 패턴 관리 클래스"""

    def __init__(self) -> None:
        """패턴 초기화"""
        self._patterns = self._initialize_patterns()
        self._compiled_patterns = self._compile_patterns()

    def _initialize_patterns(self) -> Dict[str, PatternDefinition]:
        """
        AWS 리소스 패턴 초기화
        ref-1 Kong 플러그인의 patterns.lua 기반
        """
        return {
            # EC2 Instance ID (i-xxxxxxxxxxxxxxxxx)
            "ec2_instance": PatternDefinition(
                pattern=r"i-[0-9a-f]{17}",
                replacement="ec2-{:03d}",
                type="ec2",
                description="EC2 instance identifier",
                priority=250,
            ),
            # AWS Access Key ID (AKIA로 시작)
            "access_key": PatternDefinition(
                pattern=r"AKIA[0-9A-Z]{16}",
                replacement="iam-{:03d}",
                type="credentials",
                description="AWS Access Key ID",
                priority=310,
            ),
            # Security Group (sg-xxxxxxxx)
            "security_group": PatternDefinition(
                pattern=r"sg-[0-9a-f]{8}",
                replacement="sg-{:03d}",
                type="vpc",
                description="Security group identifier",
                priority=240,
            ),
            # Subnet (subnet-xxxxxxxxxxxxxxxxx)
            "subnet": PatternDefinition(
                pattern=r"subnet-[0-9a-f]{17}",
                replacement="subnet-{:03d}",
                type="vpc",
                description="Subnet identifier",
                priority=220,
            ),
            # VPC (vpc-xxxxxxxx)
            "vpc": PatternDefinition(
                pattern=r"vpc-[0-9a-f]{8}",
                replacement="vpc-{:03d}",
                type="vpc",
                description="VPC identifier",
                priority=230,
            ),
            # S3 Bucket (다양한 버킷 패턴)
            "s3_bucket": PatternDefinition(
                pattern=r"[a-z0-9][a-z0-9\-]*bucket[a-z0-9\-]*",
                replacement="bucket-{:03d}",
                type="s3",
                description="S3 bucket names containing 'bucket'",
                priority=500,
            ),
            # S3 Logs Bucket
            "s3_logs_bucket": PatternDefinition(
                pattern=r"[a-z0-9][a-z0-9\-]*logs[a-z0-9\-]*",
                replacement="bucket-{:03d}",
                type="s3",
                description="S3 bucket names containing 'logs'",
                priority=510,
            ),
            # RDS Instance
            "rds_instance": PatternDefinition(
                pattern=r"[a-z\-]*db[a-z\-]*",
                replacement="rds-{:03d}",
                type="rds",
                description="RDS database names containing 'db'",
                priority=520,
            ),
            # AMI (ami-xxxxxxxx)
            "ami": PatternDefinition(
                pattern=r"ami-[0-9a-f]{8}",
                replacement="ami-{:03d}",
                type="ec2",
                description="AMI identifier",
                priority=260,
            ),
            # EBS Volume (vol-xxxxxxxxxxxxxxxxx)
            "ebs_volume": PatternDefinition(
                pattern=r"vol-[0-9a-f]{17}",
                replacement="vol-{:03d}",
                type="storage",
                description="EBS Volume ID",
                priority=210,
            ),
            # AWS Account ID (12자리 숫자)
            "account_id": PatternDefinition(
                pattern=r"\b\d{12}\b",
                replacement="account-{:03d}",
                type="account",
                description="AWS Account ID (12 digits)",
                priority=600,
            ),
            # IAM Role ARN
            "iam_role": PatternDefinition(
                pattern=r"arn:aws:iam::\d+:role/[a-zA-Z0-9\-_+=,.@]+",
                replacement="iam-role-{:03d}",
                type="iam",
                description="IAM Role ARN",
                priority=115,
            ),
            # Lambda Function ARN
            "lambda_arn": PatternDefinition(
                pattern=r"arn:aws:lambda:[a-z0-9\-]+:\d+:function:[a-zA-Z0-9\-_]+",
                replacement="lambda-{:03d}",
                type="lambda",
                description="Lambda function ARN",
                priority=100,
            ),
        }

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """정규식 패턴 컴파일"""
        compiled = {}
        for name, pattern_def in self._patterns.items():
            try:
                compiled[name] = re.compile(pattern_def.pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern for {name}: {e}")
        return compiled

    def find_matches(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트에서 모든 AWS 리소스 패턴 찾기

        Args:
            text: 검사할 텍스트

        Returns:
            매치된 패턴 정보 리스트
        """
        if not text or not isinstance(text, str):
            return []

        matches: List[Dict[str, Any]] = []

        # 우선순위 순으로 정렬
        sorted_patterns = sorted(self._patterns.items(), key=lambda x: x[1].priority)

        for pattern_name, pattern_def in sorted_patterns:
            compiled_pattern = self._compiled_patterns[pattern_name]

            for match in compiled_pattern.finditer(text):
                matched_text = match.group(0)

                # 추가 검증이 있으면 실행
                if pattern_def.validator:
                    is_valid, reason = pattern_def.validator(matched_text)
                    if not is_valid:
                        continue

                matches.append(
                    {
                        "match": matched_text,
                        "pattern_name": pattern_name,
                        "pattern_def": pattern_def,
                        "start": match.start(),
                        "end": match.end(),
                        "type": pattern_def.type,
                    }
                )

        # 중복 제거 (같은 위치의 매치)
        unique_matches: List[Dict[str, Any]] = []
        used_positions = set()

        for match_info in matches:
            pos_key = (match_info["start"], match_info["end"])
            if pos_key not in used_positions:
                unique_matches.append(match_info)
                used_positions.add(pos_key)

        return unique_matches

    def get_pattern(self, pattern_name: str) -> Optional[PatternDefinition]:
        """패턴 정의 가져오기"""
        return self._patterns.get(pattern_name)

    def get_pattern_types(self) -> List[str]:
        """모든 패턴 타입 리스트 반환"""
        return list(set(p.type for p in self._patterns.values()))

    def contains_aws_resources(self, text: str) -> bool:
        """텍스트에 AWS 리소스가 포함되어 있는지 확인"""
        return len(self.find_matches(text)) > 0
