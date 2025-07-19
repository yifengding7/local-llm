# infrastructure/scaffold/generator.py
"""
AI脚手架生成器 - 智能项目模板生成系统
支持多种项目类型，集成AI辅助生成最佳实践代码
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass
from enum import Enum
import jinja2
import logging
import yaml

from ...core.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class ProjectType(Enum):
    """项目类型"""
    FASTAPI_BACKEND = "fastapi_backend"
    REACT_FRONTEND = "react_frontend"
    PYTHON_PACKAGE = "python_package"
    ML_PROJECT = "ml_project"
    MICROSERVICE = "microservice"
    CLI_TOOL = "cli_tool"
    DATA_PIPELINE = "data_pipeline"
    FULL_STACK = "full_stack"

@dataclass
class ProjectConfig:
    """项目配置"""
    name: str
    type: ProjectType
    description: str
    author: str
    version: str = "0.1.0"
    python_version: str = "3.9"
    dependencies: List[str] = None
    dev_dependencies: List[str] = None
    features: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class FileTemplate:
    """文件模板"""
    path: str
    template: str
    variables: Dict[str, Any] = None
    should_format: bool = True

class ScaffoldGenerator:
    """脚手架生成器主类"""
    
    def __init__(self, templates_dir: str = "infrastructure/scaffold/templates"):
        self.templates_dir = Path(templates_dir)
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # 加载模板配置
        self.templates = self._load_templates()
        
        # AI客户端（用于生成代码）
        self.ollama_client = None
        
        # 项目规则
        self.rules = self._load_rules()
    
    def _load_templates(self) -> Dict[ProjectType, Dict[str, Any]]:
        """加载项目模板"""
        templates = {}
        
        for project_type in ProjectType:
            template_path = self.templates_dir / project_type.value
            if template_path.exists():
                config_file = template_path / "template.yaml"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        templates[project_type] = yaml.safe_load(f)
        
        return templates
    
    def _load_rules(self) -> Dict[str, Any]:
        """加载项目规则"""
        rules_file = self.templates_dir / "rules.json"
        if rules_file.exists():
            with open(rules_file, 'r') as f:
                return json.load(f)
        
        # 默认规则
        return {
            "naming_convention": "snake_case",
            "max_file_size": 100000,
            "required_files": ["README.md", ".gitignore"],
            "code_style": "black",
            "docstring_style": "google"
        }
    
    async def generate_project(self, config: ProjectConfig, output_dir: str, use_ai: bool = True) -> str:
        """生成项目脚手架"""
        output_path = Path(output_dir) / config.name
        
        # 检查目录是否存在
        if output_path.exists():
            raise ValueError(f"Directory {output_path} already exists")
        
        # 创建项目目录
        output_path.mkdir(parents=True)
        
        try:
            # 初始化AI客户端
            if use_ai and not self.ollama_client:
                self.ollama_client = OllamaClient()
            
            # 生成项目结构
            await self._generate_structure(config, output_path)
            
            # 生成基础文件
            await self._generate_base_files(config, output_path)
            
            # 根据项目类型生成特定文件
            await self._generate_type_specific_files(config, output_path, use_ai)
            
            # 生成配置文件
            await self._generate_config_files(config, output_path)
            
            # 如果启用AI，生成额外的最佳实践代码
            if use_ai:
                await self._generate_ai_enhanced_code(config, output_path)
            
            # 初始化Git仓库
            self._init_git_repo(output_path)
            
            logger.info(f"Successfully generated project: {config.name}")
            return str(output_path)
            
        except Exception as e:
            # 清理失败的项目
            if output_path.exists():
                shutil.rmtree(output_path)
            logger.error(f"Failed to generate project: {e}")
            raise
    
    async def _generate_structure(self, config: ProjectConfig, output_path: Path):
        """生成项目目录结构"""
        structure = self._get_project_structure(config.type)
        
        for dir_path in structure["directories"]:
            (output_path / dir_path).mkdir(parents=True, exist_ok=True)
            
            # 创建__init__.py文件（Python项目）
            if config.type in [ProjectType.PYTHON_PACKAGE, ProjectType.FASTAPI_BACKEND, ProjectType.ML_PROJECT]:
                if not any(part.startswith('.') for part in Path(dir_path).parts):
                    init_file = output_path / dir_path / "__init__.py"
                    init_file.touch()
    
    def _get_project_structure(self, project_type: ProjectType) -> Dict[str, List[str]]:
        """获取项目结构"""
        structures = {
            ProjectType.FASTAPI_BACKEND: {
                "directories": [
                    "app",
                    "app/api",
                    "app/api/endpoints",
                    "app/core",
                    "app/models",
                    "app/schemas",
                    "app/services",
                    "app/utils",
                    "tests",
                    "tests/unit",
                    "tests/integration",
                    "scripts",
                    "docs"
                ]
            },
            ProjectType.REACT_FRONTEND: {
                "directories": [
                    "src",
                    "src/components",
                    "src/pages",
                    "src/hooks",
                    "src/utils",
                    "src/services",
                    "src/styles",
                    "public",
                    "tests"
                ]
            },
            ProjectType.ML_PROJECT: {
                "directories": [
                    "data",
                    "data/raw",
                    "data/processed",
                    "notebooks",
                    "src",
                    "src/data",
                    "src/features",
                    "src/models",
                    "src/visualization",
                    "models",
                    "reports",
                    "reports/figures"
                ]
            },
            ProjectType.MICROSERVICE: {
                "directories": [
                    "src",
                    "src/handlers",
                    "src/services",
                    "src/repositories",
                    "src/models",
                    "src/utils",
                    "config",
                    "tests",
                    "docker",
                    "k8s"
                ]
            },
            ProjectType.PYTHON_PACKAGE: {
                "directories": [
                    config.name.replace("-", "_"),
                    "tests",
                    "docs",
                    "examples"
                ]
            },
            ProjectType.CLI_TOOL: {
                "directories": [
                    config.name.replace("-", "_"),
                    f"{config.name.replace('-', '_')}/commands",
                    f"{config.name.replace('-', '_')}/utils",
                    "tests"
                ]
            },
            ProjectType.DATA_PIPELINE: {
                "directories": [
                    "pipelines",
                    "pipelines/extract",
                    "pipelines/transform",
                    "pipelines/load",
                    "config",
                    "tests",
                    "data",
                    "logs"
                ]
            },
            ProjectType.FULL_STACK: {
                "directories": [
                    "backend",
                    "backend/app",
                    "backend/app/api",
                    "backend/app/models",
                    "backend/tests",
                    "frontend",
                    "frontend/src",
                    "frontend/src/components",
                    "frontend/src/pages",
                    "frontend/public",
                    "docker",
                    "docs"
                ]
            }
        }
        
        return structures.get(project_type, {"directories": ["src", "tests", "docs"]})
    
    async def _generate_base_files(self, config: ProjectConfig, output_path: Path):
        """生成基础文件"""
        # README.md
        readme_content = self._render_template("base/README.md.j2", {
            "project_name": config.name,
            "description": config.description,
            "author": config.author,
            "project_type": config.type.value
        })
        (output_path / "README.md").write_text(readme_content)
        
        # .gitignore
        gitignore_content = self._render_template("base/gitignore.j2", {
            "project_type": config.type.value
        })
        (output_path / ".gitignore").write_text(gitignore_content)
        
        # LICENSE
        license_content = self._render_template("base/LICENSE.j2", {
            "year": datetime.now().year,
            "author": config.author
        })
        (output_path / "LICENSE").write_text(license_content)
        
        # .env.example
        env_content = self._render_template("base/env.example.j2", {
            "project_name": config.name
        })
        (output_path / ".env.example").write_text(env_content)
    
    async def _generate_type_specific_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成特定类型的项目文件"""
        generators = {
            ProjectType.FASTAPI_BACKEND: self._generate_fastapi_files,
            ProjectType.REACT_FRONTEND: self._generate_react_files,
            ProjectType.ML_PROJECT: self._generate_ml_files,
            ProjectType.MICROSERVICE: self._generate_microservice_files,
            ProjectType.PYTHON_PACKAGE: self._generate_package_files,
            ProjectType.CLI_TOOL: self._generate_cli_files,
            ProjectType.DATA_PIPELINE: self._generate_pipeline_files,
            ProjectType.FULL_STACK: self._generate_fullstack_files
        }
        
        generator = generators.get(config.type)
        if generator:
            await generator(config, output_path, use_ai)
    
    async def _generate_fastapi_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成FastAPI项目文件"""
        # main.py
        main_content = self._render_template("fastapi/main.py.j2", {
            "project_name": config.name,
            "description": config.description
        })
        (output_path / "app" / "main.py").write_text(main_content)
        
        # 配置文件
        config_content = self._render_template("fastapi/config.py.j2", {
            "project_name": config.name
        })
        (output_path / "app" / "core" / "config.py").write_text(config_content)
        
        # 数据库模型
        if use_ai:
            models_content = await self._generate_ai_code(
                "database_models",
                config,
                "Generate SQLAlchemy models for a user authentication system"
            )
            (output_path / "app" / "models" / "user.py").write_text(models_content)
        
        # API路由
        router_content = self._render_template("fastapi/router.py.j2", {})
        (output_path / "app" / "api" / "endpoints" / "users.py").write_text(router_content)
        
        # Docker文件
        dockerfile_content = self._render_template("fastapi/Dockerfile.j2", {
            "python_version": config.python_version
        })
        (output_path / "Dockerfile").write_text(dockerfile_content)
    
    async def _generate_react_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成React项目文件"""
        # package.json
        package_json = {
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.8.0",
                "axios": "^1.3.0"
            },
            "devDependencies": {
                "react-scripts": "5.0.1",
                "@types/react": "^18.0.0",
                "@types/react-dom": "^18.0.0",
                "typescript": "^4.9.0"
            }
        }
        
        (output_path / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # App组件
        app_content = self._render_template("react/App.tsx.j2", {
            "project_name": config.name
        })
        (output_path / "src" / "App.tsx").write_text(app_content)
        
        # index文件
        index_content = self._render_template("react/index.tsx.j2", {})
        (output_path / "src" / "index.tsx").write_text(index_content)
        
        if use_ai:
            # 生成一个示例组件
            component_content = await self._generate_ai_code(
                "react_component",
                config,
                "Generate a modern React functional component with TypeScript for a user profile card with hooks"
            )
            (output_path / "src" / "components" / "UserProfile.tsx").write_text(component_content)
    
    async def _generate_ml_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成机器学习项目文件"""
        # 训练脚本
        train_content = self._render_template("ml/train.py.j2", {
            "project_name": config.name
        })
        (output_path / "src" / "train.py").write_text(train_content)
        
        # 数据处理
        data_content = self._render_template("ml/data_loader.py.j2", {})
        (output_path / "src" / "data" / "data_loader.py").write_text(data_content)
        
        # 模型定义
        if use_ai:
            model_content = await self._generate_ai_code(
                "ml_model",
                config,
                "Generate a PyTorch neural network model for image classification with modern best practices"
            )
            (output_path / "src" / "models" / "classifier.py").write_text(model_content)
        
        # Jupyter notebook模板
        notebook_content = self._render_template("ml/exploration.ipynb.j2", {
            "project_name": config.name
        })
        (output_path / "notebooks" / "01_exploration.ipynb").write_text(notebook_content)
    
    async def _generate_microservice_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成微服务项目文件"""
        # 主服务文件
        service_content = self._render_template("microservice/service.py.j2", {
            "service_name": config.name
        })
        (output_path / "src" / "main.py").write_text(service_content)
        
        # Kubernetes配置
        k8s_content = self._render_template("microservice/deployment.yaml.j2", {
            "service_name": config.name,
            "image_name": config.name.lower().replace("_", "-")
        })
        (output_path / "k8s" / "deployment.yaml").write_text(k8s_content)
        
        # Docker Compose
        compose_content = self._render_template("microservice/docker-compose.yml.j2", {
            "service_name": config.name
        })
        (output_path / "docker-compose.yml").write_text(compose_content)
    
    async def _generate_package_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成Python包项目文件"""
        package_name = config.name.replace("-", "_")
        
        # setup.py
        setup_content = self._render_template("package/setup.py.j2", {
            "package_name": config.name,
            "module_name": package_name,
            "version": config.version,
            "description": config.description,
            "author": config.author,
            "python_version": config.python_version,
            "dependencies": config.dependencies or []
        })
        (output_path / "setup.py").write_text(setup_content)
        
        # pyproject.toml
        pyproject_content = self._render_template("package/pyproject.toml.j2", {
            "package_name": config.name,
            "version": config.version,
            "description": config.description,
            "author": config.author,
            "python_version": config.python_version
        })
        (output_path / "pyproject.toml").write_text(pyproject_content)
        
        # 包初始化文件
        init_content = f'"""' + config.description + '"""' + f'\n\n__version__ = "{config.version}"\n'
        (output_path / package_name / "__init__.py").write_text(init_content)
    
    async def _generate_cli_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成CLI工具项目文件"""
        package_name = config.name.replace("-", "_")
        
        # 主CLI文件
        cli_content = self._render_template("cli/cli.py.j2", {
            "cli_name": config.name,
            "package_name": package_name
        })
        (output_path / package_name / "cli.py").write_text(cli_content)
        
        # 命令示例
        if use_ai:
            command_content = await self._generate_ai_code(
                "cli_command",
                config,
                "Generate a Click CLI command for file processing with progress bar and error handling"
            )
            (output_path / package_name / "commands" / "process.py").write_text(command_content)
    
    async def _generate_pipeline_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成数据管道项目文件"""
        # DAG配置
        dag_content = self._render_template("pipeline/dag.py.j2", {
            "pipeline_name": config.name
        })
        (output_path / "pipelines" / "main_dag.py").write_text(dag_content)
        
        # ETL示例
        if use_ai:
            etl_content = await self._generate_ai_code(
                "etl_pipeline",
                config,
                "Generate a data pipeline with extract, transform, load stages using modern Python patterns"
            )
            (output_path / "pipelines" / "etl_example.py").write_text(etl_content)
    
    async def _generate_fullstack_files(self, config: ProjectConfig, output_path: Path, use_ai: bool):
        """生成全栈项目文件"""
        # 复用FastAPI和React生成器
        backend_config = ProjectConfig(
            name=config.name + "_backend",
            type=ProjectType.FASTAPI_BACKEND,
            description=config.description + " - Backend",
            author=config.author,
            version=config.version
        )
        
        frontend_config = ProjectConfig(
            name=config.name + "_frontend",
            type=ProjectType.REACT_FRONTEND,
            description=config.description + " - Frontend",
            author=config.author,
            version=config.version
        )
        
        # 生成后端文件到backend目录
        await self._generate_fastapi_files(backend_config, output_path / "backend", use_ai)
        
        # 生成前端文件到frontend目录
        await self._generate_react_files(frontend_config, output_path / "frontend", use_ai)
        
        # 生成docker-compose用于全栈
        compose_content = self._render_template("fullstack/docker-compose.yml.j2", {
            "project_name": config.name
        })
        (output_path / "docker-compose.yml").write_text(compose_content)
    
    async def _generate_config_files(self, config: ProjectConfig, output_path: Path):
        """生成配置文件"""
        # Makefile
        if config.type in [ProjectType.PYTHON_PACKAGE, ProjectType.FASTAPI_BACKEND, ProjectType.ML_PROJECT]:
            makefile_content = self._render_template("config/Makefile.j2", {
                "project_name": config.name,
                "project_type": config.type.value
            })
            (output_path / "Makefile").write_text(makefile_content)
        
        # GitHub Actions
        github_dir = output_path / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)
        
        ci_content = self._render_template("config/ci.yml.j2", {
            "project_name": config.name,
            "project_type": config.type.value,
            "python_version": config.python_version
        })
        (github_dir / "ci.yml").write_text(ci_content)
        
        # Pre-commit配置
        precommit_content = self._render_template("config/pre-commit-config.yaml.j2", {})
        (output_path / ".pre-commit-config.yaml").write_text(precommit_content)
        
        # requirements文件（Python项目）
        if config.type != ProjectType.REACT_FRONTEND:
            requirements = config.dependencies or self._get_default_dependencies(config.type)
            requirements_content = "\n".join(requirements)
            (output_path / "requirements.txt").write_text(requirements_content)
            
            dev_requirements = config.dev_dependencies or self._get_default_dev_dependencies()
            dev_requirements_content = "\n".join(dev_requirements)
            (output_path / "requirements-dev.txt").write_text(dev_requirements_content)
    
    async def _generate_ai_enhanced_code(self, config: ProjectConfig, output_path: Path):
        """使用AI生成增强代码"""
        if not self.ollama_client:
            return
        
        enhancements = {
            ProjectType.FASTAPI_BACKEND: [
                ("app/middleware/security.py", "Generate FastAPI security middleware with JWT authentication and rate limiting"),
                ("app/utils/validators.py", "Generate Pydantic validators for common data types like email, phone, URL"),
                ("tests/test_api.py", "Generate comprehensive pytest tests for FastAPI endpoints")
            ],
            ProjectType.ML_PROJECT: [
                ("src/utils/metrics.py", "Generate custom metrics for model evaluation including classification and regression"),
                ("src/visualization/plots.py", "Generate matplotlib/seaborn visualization functions for ML results"),
                ("src/features/engineering.py", "Generate feature engineering pipeline with common transformations")
            ],
            ProjectType.REACT_FRONTEND: [
                ("src/hooks/useApi.ts", "Generate custom React hook for API calls with loading, error states and TypeScript"),
                ("src/utils/validators.ts", "Generate TypeScript validation functions for forms"),
                ("src/components/ErrorBoundary.tsx", "Generate React Error Boundary component with fallback UI")
            ]
        }
        
        project_enhancements = enhancements.get(config.type, [])
        
        for file_path, prompt in project_enhancements:
            try:
                code = await self._generate_ai_code(file_path, config, prompt)
                full_path = output_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(code)
                logger.info(f"Generated AI-enhanced code: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to generate AI code for {file_path}: {e}")
    
    async def _generate_ai_code(self, context: str, config: ProjectConfig, prompt: str) -> str:
        """使用AI生成代码"""
        if not self.ollama_client:
            return "# AI generation not available\npass"
        
        full_prompt = f"""You are an expert software engineer. Generate high-quality, production-ready code.

Project: {config.name}
Type: {config.type.value}
Description: {config.description}

{prompt}

Requirements:
- Follow best practices and design patterns
- Include comprehensive error handling
- Add detailed docstrings and type hints
- Make the code maintainable and testable
- Follow the project's coding standards

Generate only the code without any explanations."""

        try:
            response = await self.ollama_client.generate(
                model="deepseek-coder:6.7b",
                prompt=full_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            return self._clean_generated_code(response)
            
        except Exception as e:
            logger.error(f"AI code generation failed: {e}")
            return "# AI generation failed\npass"
    
    def _clean_generated_code(self, code: str) -> str:
        """清理生成的代码"""
        # 移除可能的markdown代码块标记
        if "```" in code:
            # 提取代码块内容
            lines = code.split("\n")
            in_code_block = False
            cleaned_lines = []
            
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or not line.strip().startswith("```"):
                    cleaned_lines.append(line)
            
            code = "\n".join(cleaned_lines)
        
        return code.strip()
    
    def _init_git_repo(self, project_path: Path):
        """初始化Git仓库"""
        try:
            import subprocess
            subprocess.run(["git", "init"], cwd=project_path, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=project_path,
                capture_output=True
            )
            logger.info("Initialized Git repository")
        except Exception as e:
            logger.warning(f"Failed to initialize Git repository: {e}")
    
    def _render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """渲染Jinja2模板"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**variables)
        except jinja2.TemplateNotFound:
            logger.warning(f"Template not found: {template_name}")
            return ""
    
    def _get_default_dependencies(self, project_type: ProjectType) -> List[str]:
        """获取默认依赖"""
        deps = {
            ProjectType.FASTAPI_BACKEND: [
                "fastapi>=0.104.0",
                "uvicorn[standard]>=0.24.0",
                "pydantic>=2.5.0",
                "sqlalchemy>=2.0.0",
                "alembic>=1.12.0",
                "python-jose[cryptography]>=3.3.0",
                "passlib[bcrypt]>=1.7.4",
                "python-multipart>=0.0.6",
                "httpx>=0.25.0",
                "redis>=5.0.0"
            ],
            ProjectType.ML_PROJECT: [
                "numpy>=1.24.0",
                "pandas>=2.1.0",
                "scikit-learn>=1.3.0",
                "torch>=2.1.0",
                "matplotlib>=3.7.0",
                "seaborn>=0.12.0",
                "jupyter>=1.0.0",
                "tensorboard>=2.14.0",
                "tqdm>=4.66.0"
            ],
            ProjectType.PYTHON_PACKAGE: [
                "click>=8.1.0",
                "requests>=2.31.0",
                "pydantic>=2.5.0"
            ],
            ProjectType.CLI_TOOL: [
                "click>=8.1.0",
                "rich>=13.7.0",
                "typer>=0.9.0"
            ],
            ProjectType.DATA_PIPELINE: [
                "apache-airflow>=2.7.0",
                "pandas>=2.1.0",
                "sqlalchemy>=2.0.0",
                "great-expectations>=0.17.0"
            ]
        }
        
        return deps.get(project_type, [])
    
    def _get_default_dev_dependencies(self) -> List[str]:
        """获取默认开发依赖"""
        return [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "ruff>=0.1.6",
            "mypy>=1.7.0",
            "pre-commit>=3.5.0"
        ]

# 命令行接口
async def generate_scaffold(
    project_name: str,
    project_type: str,
    description: str,
    author: str,
    output_dir: str = ".",
    use_ai: bool = True
):
    """生成项目脚手架的便捷函数"""
    
    # 转换项目类型
    try:
        proj_type = ProjectType(project_type)
    except ValueError:
        raise ValueError(f"Invalid project type: {project_type}")
    
    # 创建配置
    config = ProjectConfig(
        name=project_name,
        type=proj_type,
        description=description,
        author=author
    )
    
    # 创建生成器
    generator = ScaffoldGenerator()
    
    # 生成项目
    project_path = await generator.generate_project(config, output_dir, use_ai)
    
    return project_path