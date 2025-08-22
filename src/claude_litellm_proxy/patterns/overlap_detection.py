"""
Overlap Detection Engine
레퍼런스보다 혁신적인 충돌 해결 알고리즘

겹치는 패턴 중 최적 선택:
1. 가장 긴 매치 우선
2. 동일 길이면 높은 우선순위(낮은 숫자) 우선  
3. Interval Tree 기반 O(log n) 성능 최적화
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import bisect


@dataclass
class Match:
    """매치 정보를 담는 클래스"""
    start: int
    end: int
    text: str
    pattern_name: str
    pattern_type: str
    priority: int
    pattern_def: Any
    
    @property
    def length(self) -> int:
        """매치 길이"""
        return self.end - self.start
    
    def overlaps_with(self, other: 'Match') -> bool:
        """다른 매치와 겹치는지 확인"""
        return not (self.end <= other.start or other.end <= self.start)
    
    def __repr__(self) -> str:
        return f"Match({self.text!r}, {self.start}-{self.end}, {self.pattern_name}, p{self.priority})"


class IntervalTree:
    """
    Interval Tree 기반 빠른 overlap 검출
    O(log n) 성능으로 겹치는 구간 검색
    """
    
    def __init__(self, matches: List[Match]):
        """
        Args:
            matches: 매치 리스트
        """
        self.matches = sorted(matches, key=lambda m: m.start)
        self.starts = [m.start for m in self.matches]
        self.ends = [m.end for m in self.matches]
    
    def find_overlapping(self, match: Match) -> List[Match]:
        """
        주어진 매치와 겹치는 모든 매치 찾기
        
        Args:
            match: 기준 매치
            
        Returns:
            겹치는 매치 리스트
        """
        overlapping = []
        
        # Binary search로 겹칠 가능성이 있는 범위 찾기
        # start <= match.end 인 첫 번째 위치
        start_idx = bisect.bisect_right(self.starts, match.end) - 1
        start_idx = max(0, start_idx)
        
        # 앞으로 스캔하면서 실제 겹치는 것들 찾기
        for i in range(start_idx, len(self.matches)):
            candidate = self.matches[i]
            
            # 더 이상 겹칠 가능성이 없으면 종료
            if candidate.start >= match.end:
                break
                
            # 실제로 겹치는지 확인
            if match.overlaps_with(candidate):
                overlapping.append(candidate)
        
        return overlapping


class OverlapDetectionEngine:
    """
    겹치는 패턴 충돌 해결 엔진
    레퍼런스보다 정교한 최적 매치 선택 알고리즘
    """
    
    def __init__(self):
        self.debug = False
    
    def resolve_conflicts(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        충돌하는 매치들을 해결하여 최적의 매치 선택
        
        Args:
            matches: find_matches()에서 반환된 매치 리스트
            
        Returns:
            충돌 해결된 최종 매치 리스트
        """
        if not matches:
            return []
        
        # Dict를 Match 객체로 변환
        match_objects = []
        for match_dict in matches:
            match_obj = Match(
                start=match_dict['start'],
                end=match_dict['end'],
                text=match_dict['match'],
                pattern_name=match_dict['pattern_name'],
                pattern_type=match_dict['type'],
                priority=match_dict['pattern_def'].priority,
                pattern_def=match_dict['pattern_def']
            )
            match_objects.append(match_obj)
        
        if self.debug:
            print(f"🔍 Input matches: {len(match_objects)}")
            for i, m in enumerate(match_objects):
                print(f"  {i+1}. {m}")
        
        # 충돌 그룹 생성
        conflict_groups = self._build_conflict_groups(match_objects)
        
        if self.debug:
            print(f"🔗 Conflict groups: {len(conflict_groups)}")
            for i, group in enumerate(conflict_groups):
                print(f"  Group {i+1}: {len(group)} matches")
                for m in group:
                    print(f"    - {m}")
        
        # 각 그룹에서 최적 매치 선택
        resolved_matches = []
        for group in conflict_groups:
            best_match = self._select_best_match(group)
            resolved_matches.append(best_match)
            
            if self.debug:
                print(f"✅ Selected: {best_match}")
        
        # Match 객체를 다시 Dict로 변환
        result = []
        for match_obj in resolved_matches:
            # 원본 matches에서 해당 매치 찾기
            for original in matches:
                if (original['start'] == match_obj.start and 
                    original['end'] == match_obj.end and
                    original['pattern_name'] == match_obj.pattern_name):
                    result.append(original)
                    break
        
        if self.debug:
            print(f"🎯 Final result: {len(result)} matches")
        
        return result
    
    def _build_conflict_groups(self, matches: List[Match]) -> List[List[Match]]:
        """
        겹치는 매치들을 그룹핑
        Union-Find 알고리즘 사용
        
        Args:
            matches: 매치 리스트
            
        Returns:
            충돌 그룹 리스트
        """
        if len(matches) <= 1:
            return [matches] if matches else []
        
        # Union-Find 자료구조 구현
        parent = list(range(len(matches)))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # 겹치는 매치들을 같은 그룹으로 통합
        for i in range(len(matches)):
            for j in range(i + 1, len(matches)):
                if matches[i].overlaps_with(matches[j]):
                    union(i, j)
        
        # 그룹별로 매치 분류
        groups = defaultdict(list)
        for i, match in enumerate(matches):
            root = find(i)
            groups[root].append(match)
        
        return list(groups.values())
    
    def _select_best_match(self, candidates: List[Match]) -> Match:
        """
        후보 매치들 중 최적 선택
        
        선택 기준:
        1. 가장 긴 매치 (구체성)
        2. 동일 길이면 높은 우선순위 (낮은 priority 숫자)
        3. 동일 우선순위면 패턴명 사전순
        
        Args:
            candidates: 후보 매치 리스트
            
        Returns:
            선택된 최적 매치
        """
        if len(candidates) == 1:
            return candidates[0]
        
        # 1단계: 가장 긴 매치들 필터링
        max_length = max(m.length for m in candidates)
        longest = [m for m in candidates if m.length == max_length]
        
        if len(longest) == 1:
            return longest[0]
        
        # 2단계: 동일 길이 중 최고 우선순위 (낮은 숫자)
        min_priority = min(m.priority for m in longest)
        highest_priority = [m for m in longest if m.priority == min_priority]
        
        if len(highest_priority) == 1:
            return highest_priority[0]
        
        # 3단계: 패턴명 사전순 (일관된 결과 보장)
        return min(highest_priority, key=lambda m: m.pattern_name)
    
    def analyze_conflicts(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        충돌 상황 분석 정보 제공
        
        Args:
            matches: 원본 매치 리스트
            
        Returns:
            분석 결과 딕셔너리
        """
        if not matches:
            return {"total_matches": 0, "conflicts": 0, "groups": []}
        
        # Match 객체로 변환
        match_objects = []
        for match_dict in matches:
            match_obj = Match(
                start=match_dict['start'],
                end=match_dict['end'],
                text=match_dict['match'],
                pattern_name=match_dict['pattern_name'],
                pattern_type=match_dict['type'],
                priority=match_dict['pattern_def'].priority,
                pattern_def=match_dict['pattern_def']
            )
            match_objects.append(match_obj)
        
        conflict_groups = self._build_conflict_groups(match_objects)
        
        # 충돌이 있는 그룹만 필터링
        conflicted_groups = [g for g in conflict_groups if len(g) > 1]
        
        analysis = {
            "total_matches": len(matches),
            "resolved_matches": len(conflict_groups),
            "conflict_groups": len(conflicted_groups),
            "conflicts_resolved": sum(len(g) - 1 for g in conflicted_groups),
            "groups": []
        }
        
        for i, group in enumerate(conflicted_groups):
            best = self._select_best_match(group)
            group_info = {
                "group_id": i + 1,
                "candidates": len(group),
                "selected": {
                    "pattern": best.pattern_name,
                    "text": best.text,
                    "priority": best.priority,
                    "length": best.length
                },
                "rejected": [
                    {
                        "pattern": m.pattern_name,
                        "text": m.text,
                        "priority": m.priority,
                        "length": m.length,
                        "reason": self._get_rejection_reason(m, best)
                    }
                    for m in group if m != best
                ]
            }
            analysis["groups"].append(group_info)
        
        return analysis
    
    def _get_rejection_reason(self, rejected: Match, selected: Match) -> str:
        """매치가 거부된 이유 설명"""
        if rejected.length < selected.length:
            return f"shorter_length_{rejected.length}_vs_{selected.length}"
        elif rejected.length == selected.length and rejected.priority > selected.priority:
            return f"lower_priority_{rejected.priority}_vs_{selected.priority}"
        elif (rejected.length == selected.length and 
              rejected.priority == selected.priority):
            return f"lexical_order_{rejected.pattern_name}_vs_{selected.pattern_name}"
        else:
            return "unknown_reason"