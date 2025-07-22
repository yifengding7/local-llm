#!/usr/bin/env python3
"""
项目部署验证脚本 v2.0
验证所有组件是否正确配置和可运行
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class DeploymentValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.validation_results = []
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """记录验证结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.validation_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    → {message}")

    def validate_directory_structure(self) -> bool:
        """验证目录结构"""
        print("\n🔍 验证项目目录结构...")
        
        required_dirs = [
            "ai-monitor",
            "ai-monitor/core", 
            "ai-monitor/performance/go",
            "ai-monitor/performance/rust",
            "claude_code",
            "claude_code/mcp_tools",
            "monitoring/logs"
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            exists = full_path.exists()
            self.log_result(f"目录存在: {dir_path}", exists)
            if not exists:
                all_exist = False
                
        return all_exist

    def validate_configuration_files(self) -> bool:
        """验证配置文件"""
        print("\n🔍 验证配置文件...")
        
        config_files = [
            "pyproject.toml",
            "docker-compose.yml", 
            "control_center.sh"
        ]
        
        all_valid = True
        for config_file in config_files:
            file_path = self.project_root / config_file
            exists = file_path.exists()
            
            if exists and config_file.endswith('.yml'):
                try:
                    result = subprocess.run(['docker', 'compose', 'config', '--quiet'], 
                                          cwd=self.project_root, capture_output=True)
                    valid = result.returncode == 0
                    self.log_result(f"配置文件: {config_file}", valid, 
                                  "Docker Compose配置正确" if valid else "配置有误")
                    if not valid:
                        all_valid = False
                except Exception as e:
                    self.log_result(f"配置文件: {config_file}", False, str(e))
                    all_valid = False
            else:
                self.log_result(f"配置文件: {config_file}", exists, "文件存在" if exists else "文件缺失")
                if not exists:
                    all_valid = False
                    
        return all_valid

    def validate_performance_layer(self) -> bool:
        """验证性能层"""
        print("\n🔍 验证性能层...")
        
        # 验证Go服务
        go_path = self.project_root / "ai-monitor/performance/go"
        go_files = ["main.go", "go.mod"]
        go_valid = all((go_path / f).exists() for f in go_files)
        self.log_result("Go文件存在", go_valid, "main.go和go.mod文件完整")
        
        # 验证Rust服务
        rust_path = self.project_root / "ai-monitor/performance/rust"
        rust_files = ["Cargo.toml", "src/main.rs"]
        rust_valid = all((rust_path / f).exists() for f in rust_files)
        self.log_result("Rust文件存在", rust_valid, "Cargo.toml和main.rs文件完整")
        
        return go_valid and rust_valid

    def validate_claude_code_integration(self) -> bool:
        """验证Claude Code集成"""
        print("\n🔍 验证Claude Code集成...")
        
        claude_files = [
            "claude_code/claude_simulator.py",
            "claude_code/mcp_tools/bridge.py",
            "claude_code/mcp_tools/executor.py",
            "claude_code/__init__.py",
            "claude_code/mcp_tools/__init__.py"
        ]
        
        all_valid = True
        for file_path in claude_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            self.log_result(f"Claude Code文件: {os.path.basename(file_path)}", exists)
            if not exists:
                all_valid = False
                
        return all_valid

    def validate_control_center(self) -> bool:
        """验证控制中心脚本"""
        print("\n🔍 验证控制中心...")
        
        script_path = self.project_root / "control_center.sh"
        exists = script_path.exists()
        
        if exists:
            # 检查脚本权限
            is_executable = os.access(script_path, os.X_OK)
            self.log_result("控制中心脚本", exists and is_executable, 
                          "脚本存在且可执行" if is_executable else "脚本存在但不可执行")
            return is_executable
        else:
            self.log_result("控制中心脚本", False, "脚本不存在")
            return False

    def generate_summary_report(self) -> Dict:
        """生成验证摘要报告"""
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for r in self.validation_results if r['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "overall_status": "READY" if failed_tests == 0 else "NEEDS_ATTENTION",
            "details": self.validation_results
        }

    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🚀 开始项目部署验证...\n")
        
        # 执行各项验证
        validations = [
            ("目录结构", self.validate_directory_structure),
            ("配置文件", self.validate_configuration_files),
            ("性能层", self.validate_performance_layer),
            ("Claude Code集成", self.validate_claude_code_integration),
            ("控制中心", self.validate_control_center)
        ]
        
        all_passed = True
        for name, validator in validations:
            try:
                passed = validator()
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"❌ {name} 验证时发生错误: {str(e)}")
                all_passed = False
        
        # 生成摘要报告
        summary = self.generate_summary_report()
        
        print(f"\n{'='*60}")
        print("📊 验证摘要报告")
        print(f"{'='*60}")
        print(f"总测试数量: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print(f"整体状态: {'🎉 部署就绪' if summary['overall_status'] == 'READY' else '⚠️ 需要关注'}")
        
        if summary['failed_tests'] > 0:
            print(f"\n⚠️ 需要关注的问题:")
            for result in summary['details']:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return all_passed

if __name__ == "__main__":
    validator = DeploymentValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)