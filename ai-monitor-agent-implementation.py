# api/monitor_agent.py
"""
AI监理代理 - 代码分析、问题检测和自动修复
"""

import os
import re
import git
import ast
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import difflib
from dataclasses import dataclass, asdict
import logging

# 导入规则引擎
from ..infrastructure.scaffold.rules import RuleEngine, Rule
from ..core.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

@dataclass
class Issue:
    """代码问题定义"""
    file_path: str
    line_number: int
    column: int
    severity: str  # error, warning, info
    rule_id: str
    message: str
    suggestion: str
    code_snippet: str
    
@dataclass
class Patch:
    """修复补丁"""
    file_path: str
    original_content: str
    patched_content: str
    diff: str
    issues_fixed: List[str]

class MonitorAgent:
    """AI监理代理主类"""
    
    def __init__(self, config_path: str = "config/monitor_rules.json"):
        self.config_path = config_path
        self.rules = self._load_rules()
        self.ollama_client = OllamaClient()
        self.repo = None
        self.cache = {}
        
    def _load_rules(self) -> List[Rule]:
        """加载监理规则"""
        try:
            with open(self.config_path, 'r') as f:
                rules_config = json.load(f)
            
            rules = []
            for rule_config in rules_config['rules']:
                rule = Rule(
                    id=rule_config['id'],
                    name=rule_config['name'],
                    severity=rule_config['severity'],
                    pattern=rule_config.get('pattern'),
                    checker=rule_config.get('checker'),
                    fixer=rule_config.get('fixer')
                )
                rules.append(rule)
            
            return rules
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> List[Rule]:
        """默认规则集"""
        return [
            Rule(
                id="PY001",
                name="未使用的导入",
                severity="warning",
                pattern=r"^import\s+(\w+)|^from\s+\S+\s+import\s+(\w+)",
                checker=self._check_unused_imports,
                fixer=self._fix_unused_imports
            ),
            Rule(
                id="PY002",
                name="代码复杂度过高",
                severity="warning",
                checker=self._check_complexity,
                fixer=self._fix_complexity
            ),
            Rule(
                id="PY003",
                name="缺少文档字符串",
                severity="info",
                checker=self._check_docstrings,
                fixer=self._fix_docstrings
            ),
            Rule(
                id="SEC001",
                name="潜在的安全问题",
                severity="error",
                pattern=r"eval\(|exec\(|__import__\(",
                checker=self._check_security,
                fixer=self._fix_security
            ),
            Rule(
                id="PERF001",
                name="性能优化建议",
                severity="info",
                checker=self._check_performance,
                fixer=self._fix_performance
            )
        ]
    
    async def analyze_code(self, file_path: str, rules: Optional[List[str]] = None) -> List[Issue]:
        """分析代码文件"""
        issues = []
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # 解析AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                issues.append(Issue(
                    file_path=file_path,
                    line_number=e.lineno or 0,
                    column=e.offset or 0,
                    severity="error",
                    rule_id="SYN001",
                    message=f"语法错误: {str(e)}",
                    suggestion="请修复语法错误",
                    code_snippet=lines[e.lineno-1] if e.lineno else ""
                ))
                return issues
            
            # 应用规则检查
            active_rules = self.rules
            if rules:
                active_rules = [r for r in self.rules if r.id in rules]
            
            for rule in active_rules:
                rule_issues = await self._apply_rule(rule, content, tree, file_path)
                issues.extend(rule_issues)
            
            # AI增强分析
            if len(issues) < 5:  # 如果问题较少，进行深度分析
                ai_issues = await self._ai_analyze(content, file_path)
                issues.extend(ai_issues)
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            issues.append(Issue(
                file_path=file_path,
                line_number=0,
                column=0,
                severity="error",
                rule_id="ANA001",
                message=f"分析错误: {str(e)}",
                suggestion="请检查文件是否可读",
                code_snippet=""
            ))
        
        return issues
    
    async def _apply_rule(self, rule: Rule, content: str, tree: ast.AST, file_path: str) -> List[Issue]:
        """应用单个规则"""
        issues = []
        
        try:
            if rule.pattern:
                # 基于正则表达式的规则
                for i, line in enumerate(content.splitlines(), 1):
                    if re.search(rule.pattern, line):
                        issues.append(Issue(
                            file_path=file_path,
                            line_number=i,
                            column=0,
                            severity=rule.severity,
                            rule_id=rule.id,
                            message=rule.name,
                            suggestion=f"违反规则: {rule.name}",
                            code_snippet=line.strip()
                        ))
            
            if rule.checker:
                # 基于函数的规则
                checker_issues = await rule.checker(content, tree, file_path)
                issues.extend(checker_issues)
                
        except Exception as e:
            logger.error(f"Error applying rule {rule.id}: {e}")
        
        return issues
    
    async def _ai_analyze(self, content: str, file_path: str) -> List[Issue]:
        """AI深度代码分析"""
        issues = []
        
        try:
            # 构建分析提示
            prompt = f"""作为代码审查专家，请分析以下代码并找出潜在问题：

文件：{file_path}
```python
{content[:2000]}  # 限制长度
```

请识别以下类型的问题：
1. 代码质量问题（复杂度、可读性）
2. 潜在的bug和错误
3. 性能优化机会
4. 安全隐患
5. 最佳实践违反

对每个问题，请提供：
- 行号
- 问题描述
- 严重程度（error/warning/info）
- 修复建议

以JSON格式返回结果。"""

            # 调用AI模型
            response = await self.ollama_client.chat(
                model="deepseek-coder",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            # 解析AI响应
            try:
                ai_results = json.loads(response['message']['content'])
                for result in ai_results.get('issues', []):
                    issues.append(Issue(
                        file_path=file_path,
                        line_number=result.get('line', 0),
                        column=0,
                        severity=result.get('severity', 'info'),
                        rule_id="AI001",
                        message=result.get('description', ''),
                        suggestion=result.get('suggestion', ''),
                        code_snippet=result.get('code', '')
                    ))
            except:
                # JSON解析失败，尝试文本解析
                pass
                
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
        
        return issues
    
    async def generate_patch(self, issues: List[Issue]) -> Patch:
        """生成修复补丁"""
        patches = {}
        
        # 按文件分组问题
        file_issues = {}
        for issue in issues:
            if issue.file_path not in file_issues:
                file_issues[issue.file_path] = []
            file_issues[issue.file_path].append(issue)
        
        # 为每个文件生成补丁
        all_patches = []
        for file_path, file_issues_list in file_issues.items():
            patch = await self._generate_file_patch(file_path, file_issues_list)
            if patch:
                all_patches.append(patch)
        
        # 合并补丁
        if len(all_patches) == 1:
            return all_patches[0]
        else:
            # 返回第一个补丁，实际应用中可能需要更复杂的合并逻辑
            return all_patches[0] if all_patches else None
    
    async def _generate_file_patch(self, file_path: str, issues: List[Issue]) -> Optional[Patch]:
        """为单个文件生成补丁"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            patched_content = original_content
            fixed_issues = []
            
            # 应用每个规则的修复器
            for issue in issues:
                rule = next((r for r in self.rules if r.id == issue.rule_id), None)
                if rule and rule.fixer:
                    try:
                        patched_content = await rule.fixer(patched_content, issue)
                        fixed_issues.append(issue.rule_id)
                    except Exception as e:
                        logger.error(f"Fix error for {issue.rule_id}: {e}")
            
            # 如果没有修复器，使用AI生成修复
            if not fixed_issues and issues:
                patched_content = await self._ai_fix(original_content, issues)
                fixed_issues = [i.rule_id for i in issues]
            
            # 生成diff
            diff = '\n'.join(difflib.unified_diff(
                original_content.splitlines(),
                patched_content.splitlines(),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=''
            ))
            
            return Patch(
                file_path=file_path,
                original_content=original_content,
                patched_content=patched_content,
                diff=diff,
                issues_fixed=fixed_issues
            )
            
        except Exception as e:
            logger.error(f"Patch generation error: {e}")
            return None
    
    async def _ai_fix(self, content: str, issues: List[Issue]) -> str:
        """使用AI生成修复代码"""
        # 构建修复提示
        issues_desc = "\n".join([
            f"- 第{i.line_number}行: {i.message} ({i.suggestion})"
            for i in issues
        ])
        
        prompt = f"""请修复以下代码中的问题：

原始代码：
```python
{content}
```

发现的问题：
{issues_desc}

请返回修复后的完整代码，保持原有功能不变，只修复指出的问题。"""

        response = await self.ollama_client.chat(
            model="deepseek-coder",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        # 提取修复后的代码
        fixed_code = response['message']['content']
        
        # 清理代码块标记
        if "```python" in fixed_code:
            fixed_code = fixed_code.split("```python")[1].split("```")[0]
        elif "```" in fixed_code:
            fixed_code = fixed_code.split("```")[1].split("```")[0]
        
        return fixed_code.strip()
    
    async def apply_patch(self, file_path: str, patch: Patch) -> bool:
        """应用补丁到文件"""
        try:
            # 备份原文件
            backup_path = f"{file_path}.backup"
            with open(file_path, 'r') as f:
                backup_content = f.read()
            with open(backup_path, 'w') as f:
                f.write(backup_content)
            
            # 应用补丁
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(patch.patched_content)
            
            # 如果有Git仓库，提交更改
            if self.repo:
                self.repo.index.add([file_path])
                self.repo.index.commit(
                    f"AI Monitor: Fixed {len(patch.issues_fixed)} issues in {os.path.basename(file_path)}"
                )
            
            logger.info(f"Successfully applied patch to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply patch: {e}")
            # 恢复备份
            if os.path.exists(backup_path):
                os.rename(backup_path, file_path)
            return False
    
    def init_repo(self, repo_path: str):
        """初始化Git仓库"""
        try:
            self.repo = git.Repo(repo_path)
        except:
            logger.warning(f"Not a git repository: {repo_path}")
            self.repo = None
    
    # 规则检查器实现
    
    async def _check_unused_imports(self, content: str, tree: ast.AST, file_path: str) -> List[Issue]:
        """检查未使用的导入"""
        issues = []
        
        class ImportVisitor(ast.NodeVisitor):
            def __init__(self):
                self.imports = {}
                self.names = set()
            
            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imports[name] = (node.lineno, alias.name)
            
            def visit_ImportFrom(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imports[name] = (node.lineno, f"{node.module}.{alias.name}")
            
            def visit_Name(self, node):
                self.names.add(node.id)
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        # 检查未使用的导入
        for name, (lineno, full_name) in visitor.imports.items():
            if name not in visitor.names:
                issues.append(Issue(
                    file_path=file_path,
                    line_number=lineno,
                    column=0,
                    severity="warning",
                    rule_id="PY001",
                    message=f"未使用的导入: {name}",
                    suggestion=f"移除未使用的导入 '{full_name}'",
                    code_snippet=content.splitlines()[lineno-1] if lineno <= len(content.splitlines()) else ""
                ))
        
        return issues
    
    async def _check_complexity(self, content: str, tree: ast.AST, file_path: str) -> List[Issue]:
        """检查代码复杂度"""
        issues = []
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity_map = {}
            
            def visit_FunctionDef(self, node):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.complexity_map[node.name] = (node.lineno, complexity)
                self.generic_visit(node)
            
            def _calculate_complexity(self, node):
                # 简化的圈复杂度计算
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For)):
                        complexity += 1
                    elif isinstance(child, ast.ExceptHandler):
                        complexity += 1
                return complexity
        
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        for func_name, (lineno, complexity) in visitor.complexity_map.items():
            issues.append(Issue(
                file_path=file_path,
                line_number=lineno,
                column=0,
                severity="warning",
                rule_id="PY002",
                message=f"函数 '{func_name}' 复杂度过高: {complexity}",
                suggestion="考虑将函数拆分为更小的函数",
                code_snippet=f"def {func_name}..."
            ))
        
        return issues
    
    async def _check_docstrings(self, content: str, tree: ast.AST, file_path: str) -> List[Issue]:
        """检查缺少的文档字符串"""
        issues = []
        
        class DocstringVisitor(ast.NodeVisitor):
            def __init__(self):
                self.missing_docstrings = []
            
            def visit_FunctionDef(self, node):
                if not ast.get_docstring(node) and not node.name.startswith('_'):
                    self.missing_docstrings.append((node.name, node.lineno, 'function'))
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                if not ast.get_docstring(node):
                    self.missing_docstrings.append((node.name, node.lineno, 'class'))
                self.generic_visit(node)
        
        visitor = DocstringVisitor()
        visitor.visit(tree)
        
        for name, lineno, type_ in visitor.missing_docstrings:
            issues.append(Issue(
                file_path=file_path,
                line_number=lineno,
                column=0,
                severity="info",
                rule_id="PY003",
                message=f"{type_.capitalize()} '{name}' 缺少文档字符串",
                suggestion=f"为{type_} '{name}' 添加文档字符串",
                code_snippet=f"{type_} {name}"
            ))
        
        return issues
    
    async def _check_security(self, content: str, tree: ast.AST, file_path: str) -> List[Issue]:
        """检查安全问题"""
        issues = []
        dangerous_calls = ['eval', 'exec', '__import__', 'compile', 'open']
        
        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.dangerous_calls = []
            
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in dangerous_calls:
                    self.dangerous_calls.append((node.func.id, node.lineno))
                self.generic_visit(node)
        
        visitor = SecurityVisitor()
        visitor.visit(tree)
        
        for func_name, lineno in visitor.dangerous_calls:
            issues.append(Issue(
                file_path=file_path,
                line_number=lineno,
                column=0,
                severity="error",
                rule_id="SEC001",
                message=f"潜在的安全风险: 使用了 '{func_name}'",
                suggestion=f"避免使用 '{func_name}'，考虑更安全的替代方案",
                code_snippet=content.splitlines()[lineno-1] if lineno <= len(content.splitlines()) else ""
            ))
        
        return issues
    
    async def _check_performance(self, content: str, tree: ast.AST, file_path: str) -> List[Issue]:
        """检查性能问题"""
        issues = []
        
        # 检查在循环中的昂贵操作
        class PerformanceVisitor(ast.NodeVisitor):
            def __init__(self):
                self.issues = []
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
                if self.in_loop:
                    # 检查循环中的昂贵操作
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['append', 'extend'] and isinstance(node.func.value, ast.Name):
                            # 检查是否在循环中频繁append
                            self.issues.append(('list_append_in_loop', node.lineno))
                self.generic_visit(node)
        
        visitor = PerformanceVisitor()
        visitor.visit(tree)
        
        for issue_type, lineno in visitor.issues:
            if issue_type == 'list_append_in_loop':
                issues.append(Issue(
                    file_path=file_path,
                    line_number=lineno,
                    column=0,
                    severity="info",
                    rule_id="PERF001",
                    message="循环中频繁使用append可能影响性能",
                    suggestion="考虑使用列表推导式或预分配列表大小",
                    code_snippet=content.splitlines()[lineno-1] if lineno <= len(content.splitlines()) else ""
                ))
        
        return issues
    
    # 修复器实现
    
    async def _fix_unused_imports(self, content: str, issue: Issue) -> str:
        """修复未使用的导入"""
        lines = content.splitlines()
        if 0 < issue.line_number <= len(lines):
            # 简单地注释掉未使用的导入
            lines[issue.line_number-1] = f"# {lines[issue.line_number-1]}  # Removed by AI Monitor"
        return '\n'.join(lines)
    
    async def _fix_complexity(self, content: str, issue: Issue) -> str:
        """修复高复杂度（需要AI辅助）"""
        return await self._ai_fix(content, [issue])
    
    async def _fix_docstrings(self, content: str, issue: Issue) -> str:
        """添加缺失的文档字符串"""
        lines = content.splitlines()
        if 0 < issue.line_number <= len(lines):
            indent = len(lines[issue.line_number-1]) - len(lines[issue.line_number-1].lstrip())
            docstring = f'{" " * (indent + 4)}"""TODO: Add docstring"""'
            lines.insert(issue.line_number, docstring)
        return '\n'.join(lines)
    
    async def _fix_security(self, content: str, issue: Issue) -> str:
        """修复安全问题（需要人工确认）"""
        # 安全问题通常需要人工确认，这里只是标记
        lines = content.splitlines()
        if 0 < issue.line_number <= len(lines):
            lines[issue.line_number-1] = f"{lines[issue.line_number-1]}  # SECURITY WARNING: {issue.message}"
        return '\n'.join(lines)
    
    async def _fix_performance(self, content: str, issue: Issue) -> str:
        """修复性能问题"""
        return await self._ai_fix(content, [issue])