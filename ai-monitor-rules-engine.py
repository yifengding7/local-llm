# infrastructure/scaffold/rules.py
"""
规则引擎 - 代码质量和项目结构规则
"""

import re
import ast
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RuleSeverity(Enum):
    """规则严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class RuleCategory(Enum):
    """规则类别"""
    STYLE = "style"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"
    DOCUMENTATION = "documentation"

@dataclass
class Rule:
    """规则定义"""
    id: str
    name: str
    description: str = ""
    severity: RuleSeverity = RuleSeverity.WARNING
    category: RuleCategory = RuleCategory.STYLE
    pattern: Optional[str] = None
    checker: Optional[Callable] = None
    fixer: Optional[Callable] = None
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    
    def check(self, content: str, ast_tree: Optional[ast.AST] = None) -> List[Dict[str, Any]]:
        """执行规则检查"""
        violations = []
        
        if self.pattern and content:
            # 基于正则表达式的检查
            for i, line in enumerate(content.splitlines(), 1):
                if re.search(self.pattern, line):
                    violations.append({
                        "line": i,
                        "column": 0,
                        "message": self.name,
                        "rule_id": self.id,
                        "severity": self.severity.value
                    })
        
        if self.checker:
            # 基于函数的检查
            try:
                custom_violations = self.checker(content, ast_tree)
                violations.extend(custom_violations)
            except Exception as e:
                logger.error(f"Rule {self.id} checker failed: {e}")
        
        return violations

class RuleEngine:
    """规则引擎主类"""
    
    def __init__(self, rules_config: Optional[str] = None):
        self.rules = self._load_rules(rules_config)
        self.custom_rules = {}
        self.rule_stats = {}
    
    def _load_rules(self, config_path: Optional[str]) -> Dict[str, Rule]:
        """加载规则配置"""
        rules = {}
        
        # 加载内置规则
        for rule in self._get_builtin_rules():
            rules[rule.id] = rule
        
        # 加载自定义规则
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                
            for rule_data in custom_config.get('rules', []):
                rule = Rule(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    description=rule_data.get('description', ''),
                    severity=RuleSeverity(rule_data.get('severity', 'warning')),
                    category=RuleCategory(rule_data.get('category', 'style')),
                    pattern=rule_data.get('pattern'),
                    enabled=rule_data.get('enabled', True),
                    tags=rule_data.get('tags', [])
                )
                rules[rule.id] = rule
        
        return rules
    
    def _get_builtin_rules(self) -> List[Rule]:
        """获取内置规则"""
        return [
            # 代码风格规则
            Rule(
                id="S001",
                name="行长度超限",
                description="单行代码不应超过120个字符",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.STYLE,
                checker=self._check_line_length
            ),
            Rule(
                id="S002",
                name="尾随空格",
                description="行尾不应有空格",
                severity=RuleSeverity.INFO,
                category=RuleCategory.STYLE,
                pattern=r"\s+$",
                fixer=self._fix_trailing_whitespace
            ),
            Rule(
                id="S003",
                name="多个空行",
                description="不应有超过2个连续空行",
                severity=RuleSeverity.INFO,
                category=RuleCategory.STYLE,
                checker=self._check_multiple_blank_lines
            ),
            
            # 性能规则
            Rule(
                id="P001",
                name="循环中的append",
                description="在循环中使用append可能影响性能",
                severity=RuleSeverity.INFO,
                category=RuleCategory.PERFORMANCE,
                checker=self._check_loop_append
            ),
            Rule(
                id="P002",
                name="重复计算",
                description="避免在循环中重复计算不变的值",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.PERFORMANCE,
                checker=self._check_repeated_calculations
            ),
            
            # 安全规则
            Rule(
                id="SEC001",
                name="使用eval",
                description="避免使用eval，存在安全风险",
                severity=RuleSeverity.ERROR,
                category=RuleCategory.SECURITY,
                pattern=r"\beval\s*\("
            ),
            Rule(
                id="SEC002",
                name="硬编码密码",
                description="不应在代码中硬编码密码",
                severity=RuleSeverity.ERROR,
                category=RuleCategory.SECURITY,
                pattern=r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
                tags=["security", "critical"]
            ),
            Rule(
                id="SEC003",
                name="不安全的随机数",
                description="密码学应用应使用secrets模块",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.SECURITY,
                checker=self._check_insecure_random
            ),
            
            # 可维护性规则
            Rule(
                id="M001",
                name="函数过长",
                description="函数不应超过50行",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.MAINTAINABILITY,
                checker=self._check_function_length
            ),
            Rule(
                id="M002",
                name="圈复杂度过高",
                description="函数圈复杂度不应超过10",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.MAINTAINABILITY,
                checker=self._check_cyclomatic_complexity
            ),
            Rule(
                id="M003",
                name="重复代码",
                description="避免重复的代码块",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.MAINTAINABILITY,
                checker=self._check_code_duplication
            ),
            
            # 最佳实践规则
            Rule(
                id="BP001",
                name="使用is比较None",
                description="与None比较应使用is而不是==",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.BEST_PRACTICE,
                pattern=r"==\s*None|!=\s*None",
                fixer=self._fix_none_comparison
            ),
            Rule(
                id="BP002",
                name="可变默认参数",
                description="不应使用可变对象作为默认参数",
                severity=RuleSeverity.ERROR,
                category=RuleCategory.BEST_PRACTICE,
                checker=self._check_mutable_defaults
            ),
            Rule(
                id="BP003",
                name="裸except",
                description="避免使用裸except子句",
                severity=RuleSeverity.WARNING,
                category=RuleCategory.BEST_PRACTICE,
                pattern=r"except\s*:",
                tags=["exception-handling"]
            ),
            
            # 文档规则
            Rule(
                id="D001",
                name="缺少模块文档",
                description="模块应有文档字符串",
                severity=RuleSeverity.INFO,
                category=RuleCategory.DOCUMENTATION,
                checker=self._check_module_docstring
            ),
            Rule(
                id="D002",
                name="缺少函数文档",
                description="公共函数应有文档字符串",
                severity=RuleSeverity.INFO,
                category=RuleCategory.DOCUMENTATION,
                checker=self._check_function_docstring
            ),
            Rule(
                id="D003",
                name="文档格式错误",
                description="文档字符串应符合Google风格",
                severity=RuleSeverity.INFO,
                category=RuleCategory.DOCUMENTATION,
                checker=self._check_docstring_format
            )
        ]
    
    def register_rule(self, rule: Rule):
        """注册自定义规则"""
        self.custom_rules[rule.id] = rule
        self.rules[rule.id] = rule
    
    def check_content(self, content: str, file_path: str = "", 
                     enabled_rules: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """检查内容"""
        violations = []
        
        # 解析AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return [{
                "file": file_path,
                "line": e.lineno or 1,
                "column": e.offset or 0,
                "rule_id": "SYNTAX",
                "severity": "error",
                "message": f"Syntax error: {str(e)}"
            }]
        
        # 应用规则
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
                
            if enabled_rules and rule_id not in enabled_rules:
                continue
            
            try:
                rule_violations = rule.check(content, tree)
                
                # 添加文件路径和规则信息
                for violation in rule_violations:
                    violation['file'] = file_path
                    violation['rule_name'] = rule.name
                    violation['category'] = rule.category.value
                    violations.append(violation)
                
                # 更新统计
                if rule_id not in self.rule_stats:
                    self.rule_stats[rule_id] = 0
                self.rule_stats[rule_id] += len(rule_violations)
                
            except Exception as e:
                logger.error(f"Rule {rule_id} failed on {file_path}: {e}")
        
        return violations
    
    def fix_violations(self, content: str, violations: List[Dict[str, Any]]) -> str:
        """修复违规"""
        fixed_content = content
        
        # 按行号倒序排序，避免修复时行号变化
        sorted_violations = sorted(violations, key=lambda v: v.get('line', 0), reverse=True)
        
        for violation in sorted_violations:
            rule_id = violation.get('rule_id')
            rule = self.rules.get(rule_id)
            
            if rule and rule.fixer:
                try:
                    fixed_content = rule.fixer(fixed_content, violation)
                except Exception as e:
                    logger.error(f"Fixer for rule {rule_id} failed: {e}")
        
        return fixed_content
    
    def get_stats(self) -> Dict[str, Any]:
        """获取规则统计"""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "violations_by_rule": self.rule_stats,
            "violations_by_category": self._get_category_stats(),
            "violations_by_severity": self._get_severity_stats()
        }
    
    def _get_category_stats(self) -> Dict[str, int]:
        """按类别统计违规"""
        stats = {}
        for rule_id, count in self.rule_stats.items():
            rule = self.rules.get(rule_id)
            if rule:
                category = rule.category.value
                stats[category] = stats.get(category, 0) + count
        return stats
    
    def _get_severity_stats(self) -> Dict[str, int]:
        """按严重程度统计违规"""
        stats = {}
        for rule_id, count in self.rule_stats.items():
            rule = self.rules.get(rule_id)
            if rule:
                severity = rule.severity.value
                stats[severity] = stats.get(severity, 0) + count
        return stats
    
    # 规则检查器实现
    
    def _check_line_length(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查行长度"""
        violations = []
        max_length = 120
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > max_length:
                violations.append({
                    "line": i,
                    "column": max_length,
                    "message": f"Line too long ({len(line)} > {max_length} characters)",
                    "rule_id": "S001",
                    "severity": "warning"
                })
        
        return violations
    
    def _check_multiple_blank_lines(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查多个空行"""
        violations = []
        lines = content.splitlines()
        blank_count = 0
        
        for i, line in enumerate(lines):
            if not line.strip():
                blank_count += 1
                if blank_count > 2:
                    violations.append({
                        "line": i + 1,
                        "column": 0,
                        "message": "Too many blank lines (>2)",
                        "rule_id": "S003",
                        "severity": "info"
                    })
            else:
                blank_count = 0
        
        return violations
    
    def _check_loop_append(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查循环中的append"""
        violations = []
        
        class AppendChecker(ast.NodeVisitor):
            def __init__(self):
                self.violations = []
                self.in_loop = False
            
            def visit_For(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def visit_While(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def visit_Call(self, node):
                if self.in_loop and isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'append':
                        self.violations.append({
                            "line": node.lineno,
                            "column": node.col_offset,
                            "message": "Consider using list comprehension instead of append in loop",
                            "rule_id": "P001",
                            "severity": "info"
                        })
                self.generic_visit(node)
        
        checker = AppendChecker()
        checker.visit(tree)
        
        return checker.violations
    
    def _check_repeated_calculations(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查重复计算"""
        # 简化实现：检查循环中的len()调用
        violations = []
        
        class CalculationChecker(ast.NodeVisitor):
            def __init__(self):
                self.violations = []
                self.in_loop = False
            
            def visit_For(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def visit_While(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def visit_Call(self, node):
                if self.in_loop and isinstance(node.func, ast.Name):
                    if node.func.id in ['len', 'sum', 'max', 'min']:
                        self.violations.append({
                            "line": node.lineno,
                            "column": node.col_offset,
                            "message": f"Consider moving {node.func.id}() outside the loop",
                            "rule_id": "P002",
                            "severity": "warning"
                        })
                self.generic_visit(node)
        
        checker = CalculationChecker()
        checker.visit(tree)
        
        return checker.violations
    
    def _check_insecure_random(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查不安全的随机数使用"""
        violations = []
        
        # 检查是否在密码相关上下文中使用random
        if re.search(r'(password|token|secret|key)', content, re.IGNORECASE):
            if 'import random' in content and 'import secrets' not in content:
                for i, line in enumerate(content.splitlines(), 1):
                    if 'random.' in line:
                        violations.append({
                            "line": i,
                            "column": 0,
                            "message": "Use secrets module for cryptographic purposes",
                            "rule_id": "SEC003",
                            "severity": "warning"
                        })
        
        return violations
    
    def _check_function_length(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查函数长度"""
        violations = []
        max_lines = 50
        
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self, lines):
                self.violations = []
                self.lines = lines
            
            def visit_FunctionDef(self, node):
                func_lines = node.end_lineno - node.lineno + 1
                if func_lines > max_lines:
                    self.violations.append({
                        "line": node.lineno,
                        "column": 0,
                        "message": f"Function '{node.name}' is too long ({func_lines} > {max_lines} lines)",
                        "rule_id": "M001",
                        "severity": "warning"
                    })
                self.generic_visit(node)
        
        visitor = FunctionVisitor(content.splitlines())
        visitor.visit(tree)
        
        return visitor.violations
    
    def _check_cyclomatic_complexity(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查圈复杂度"""
        violations = []
        max_complexity = 10
        
        class ComplexityCalculator(ast.NodeVisitor):
            def __init__(self):
                self.violations = []
            
            def visit_FunctionDef(self, node):
                complexity = self._calculate_complexity(node)
                if complexity > max_complexity:
                    self.violations.append({
                        "line": node.lineno,
                        "column": 0,
                        "message": f"Function '{node.name}' has high cyclomatic complexity ({complexity} > {max_complexity})",
                        "rule_id": "M002",
                        "severity": "warning"
                    })
                self.generic_visit(node)
            
            def _calculate_complexity(self, node):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For)):
                        complexity += 1
                    elif isinstance(child, ast.ExceptHandler):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                return complexity
        
        calculator = ComplexityCalculator()
        calculator.visit(tree)
        
        return calculator.violations
    
    def _check_code_duplication(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查代码重复（简化版）"""
        violations = []
        lines = content.splitlines()
        min_duplicate_lines = 5
        
        # 简单的基于行的重复检测
        line_groups = {}
        
        for i in range(len(lines) - min_duplicate_lines + 1):
            group = '\n'.join(lines[i:i + min_duplicate_lines])
            if group.strip():
                if group in line_groups:
                    violations.append({
                        "line": i + 1,
                        "column": 0,
                        "message": f"Duplicate code block (also at line {line_groups[group] + 1})",
                        "rule_id": "M003",
                        "severity": "warning"
                    })
                else:
                    line_groups[group] = i
        
        return violations
    
    def _check_mutable_defaults(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查可变默认参数"""
        violations = []
        
        class DefaultArgChecker(ast.NodeVisitor):
            def __init__(self):
                self.violations = []
            
            def visit_FunctionDef(self, node):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self.violations.append({
                            "line": node.lineno,
                            "column": 0,
                            "message": f"Function '{node.name}' has mutable default argument",
                            "rule_id": "BP002",
                            "severity": "error"
                        })
                self.generic_visit(node)
        
        checker = DefaultArgChecker()
        checker.visit(tree)
        
        return checker.violations
    
    def _check_module_docstring(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查模块文档字符串"""
        violations = []
        
        if not ast.get_docstring(tree):
            violations.append({
                "line": 1,
                "column": 0,
                "message": "Missing module docstring",
                "rule_id": "D001",
                "severity": "info"
            })
        
        return violations
    
    def _check_function_docstring(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查函数文档字符串"""
        violations = []
        
        class DocstringChecker(ast.NodeVisitor):
            def __init__(self):
                self.violations = []
            
            def visit_FunctionDef(self, node):
                # 跳过私有函数
                if not node.name.startswith('_'):
                    if not ast.get_docstring(node):
                        self.violations.append({
                            "line": node.lineno,
                            "column": 0,
                            "message": f"Function '{node.name}' missing docstring",
                            "rule_id": "D002",
                            "severity": "info"
                        })
                self.generic_visit(node)
        
        checker = DocstringChecker()
        checker.visit(tree)
        
        return checker.violations
    
    def _check_docstring_format(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """检查文档字符串格式"""
        violations = []
        
        class FormatChecker(ast.NodeVisitor):
            def __init__(self):
                self.violations = []
            
            def visit_FunctionDef(self, node):
                docstring = ast.get_docstring(node)
                if docstring:
                    # 简单检查Google风格的关键字
                    if node.args.args and 'Args:' not in docstring and 'Parameters:' not in docstring:
                        self.violations.append({
                            "line": node.lineno,
                            "column": 0,
                            "message": f"Function '{node.name}' docstring missing Args section",
                            "rule_id": "D003",
                            "severity": "info"
                        })
                    
                    if 'return' in node.name.lower() and 'Returns:' not in docstring:
                        self.violations.append({
                            "line": node.lineno,
                            "column": 0,
                            "message": f"Function '{node.name}' docstring missing Returns section",
                            "rule_id": "D003",
                            "severity": "info"
                        })
                
                self.generic_visit(node)
        
        checker = FormatChecker()
        checker.visit(tree)
        
        return checker.violations
    
    # 修复器实现
    
    def _fix_trailing_whitespace(self, content: str, violation: Dict[str, Any]) -> str:
        """修复尾随空格"""
        lines = content.splitlines()
        if 0 < violation['line'] <= len(lines):
            lines[violation['line'] - 1] = lines[violation['line'] - 1].rstrip()
        return '\n'.join(lines)
    
    def _fix_none_comparison(self, content: str, violation: Dict[str, Any]) -> str:
        """修复None比较"""
        lines = content.splitlines()
        if 0 < violation['line'] <= len(lines):
            line = lines[violation['line'] - 1]
            line = re.sub(r'==\s*None', 'is None', line)
            line = re.sub(r'!=\s*None', 'is not None', line)
            lines[violation['line'] - 1] = line
        return '\n'.join(lines)