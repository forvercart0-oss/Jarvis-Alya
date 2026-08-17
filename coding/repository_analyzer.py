"""Repository analyzer for JARVIS Phase 27."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from coding.models import ProjectInfo

logger = logging.getLogger("jarvis.coding.repository_analyzer")


class RepositoryAnalyzer:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._indicators = {
            "python": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile", "uv.lock"],
            "node": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "go": ["go.mod", "go.sum"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "ruby": ["Gemfile", "Gemfile.lock"],
            "php": ["composer.json", "composer.lock"],
            "dotnet": ["*.csproj", "*.sln"],
        }
        self._frameworks = {
            "fastapi": ["fastapi"],
            "django": ["django"],
            "flask": ["flask"],
            "react": ["react"],
            "vue": ["vue"],
            "angular": ["angular"],
            "next": ["next"],
            "express": ["express"],
            "postgresql": ["psycopg2", "postgresql", "pg"],
            "sqlite": ["sqlite3", "aiosqlite"],
            "mongodb": ["pymongo", "mongoose", "mongodb"],
            "docker": ["Dockerfile", "docker-compose.yml", "compose.yaml", ".dockerignore"],
            "ci_cd": [".github", ".gitlab-ci.yml", "Jenkinsfile", ".circleci"],
        }

    async def analyze(self, project_path: str) -> ProjectInfo:
        path = Path(project_path)
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Project path does not exist: {project_path}")
        info = ProjectInfo(name=path.name, path=str(path))
        self._detect_language(info, path)
        self._detect_framework(info, path)
        self._detect_package_manager(info, path)
        self._detect_database(info, path)
        self._detect_frontend(info, path)
        self._detect_backend(info, path)
        self._detect_tests(info, path)
        self._detect_configuration(info, path)
        self._detect_docker(info, path)
        self._detect_ci_cd(info, path)
        self._detect_git(info, path)
        self._detect_environment_files(info, path)
        return info

    def _detect_language(self, info: ProjectInfo, path: Path) -> None:
        for lang, files in self._indicators.items():
            for indicator in files:
                if "*" in indicator:
                    if any(path.match(indicator) for p in path.rglob("*") if p.is_file()):
                        info.language = lang
                        return
                elif (path / indicator).exists():
                    info.language = lang
                    return

    def _detect_framework(self, info: ProjectInfo, path: Path) -> None:
        for framework, keywords in self._frameworks.items():
            for keyword in keywords:
                if self._contains_keyword(path, keyword):
                    info.framework = framework
                    return

    def _detect_package_manager(self, info: ProjectInfo, path: Path) -> None:
        if (path / "package-lock.json").exists():
            info.package_manager = "npm"
        elif (path / "yarn.lock").exists():
            info.package_manager = "yarn"
        elif (path / "pnpm-lock.yaml").exists():
            info.package_manager = "pnpm"
        elif (path / "bun.lock").exists():
            info.package_manager = "bun"
        elif (path / "pyproject.toml").exists():
            info.package_manager = "pip/uv"
        elif (path / "requirements.txt").exists():
            info.package_manager = "pip"
        elif (path / "Pipfile").exists():
            info.package_manager = "pipenv"
        elif (path / "Cargo.toml").exists():
            info.package_manager = "cargo"
        elif (path / "go.mod").exists():
            info.package_manager = "go"

    def _detect_database(self, info: ProjectInfo, path: Path) -> None:
        for db, keywords in self._frameworks.items():
            if db in ("postgresql", "sqlite", "mongodb"):
                for keyword in keywords:
                    if self._contains_keyword(path, keyword):
                        info.database = db
                        return

    def _detect_frontend(self, info: ProjectInfo, path: Path) -> None:
        if (path / "package.json").exists():
            try:
                pkg = json.loads((path / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "react" in deps:
                    info.frontend = "react"
                elif "vue" in deps:
                    info.frontend = "vue"
                elif "angular" in deps:
                    info.frontend = "angular"
                elif "next" in deps:
                    info.frontend = "next"
            except Exception:
                pass

    def _detect_backend(self, info: ProjectInfo, path: Path) -> None:
        if self._contains_keyword(path, "fastapi"):
            info.backend = "fastapi"
        elif self._contains_keyword(path, "django"):
            info.backend = "django"
        elif self._contains_keyword(path, "flask"):
            info.backend = "flask"
        elif self._contains_keyword(path, "express"):
            info.backend = "express"

    def _detect_tests(self, info: ProjectInfo, path: Path) -> None:
        if (path / "tests").is_dir() or (path / "test").is_dir() or self._contains_keyword(path, "pytest"):
            info.tests = "pytest"
        elif self._contains_keyword(path, "jest"):
            info.tests = "jest"
        elif self._contains_keyword(path, "mocha"):
            info.tests = "mocha"

    def _detect_configuration(self, info: ProjectInfo, path: Path) -> None:
        configs = [".env", ".env.example", "config.py", "settings.py", "config.yaml", "config.json"]
        for config in configs:
            if (path / config).exists():
                info.configuration.append(config)

    def _detect_docker(self, info: ProjectInfo, path: Path) -> None:
        for indicator in self._frameworks["docker"]:
            if (path / indicator).exists():
                info.docker = True
                return

    def _detect_ci_cd(self, info: ProjectInfo, path: Path) -> None:
        for indicator in self._frameworks["ci_cd"]:
            if (path / indicator).exists():
                info.ci_cd = True
                return

    def _detect_git(self, info: ProjectInfo, path: Path) -> None:
        info.git = (path / ".git").is_dir()

    def _detect_environment_files(self, info: ProjectInfo, path: Path) -> None:
        for env_file in [".env", ".env.local", ".env.development", ".env.production", ".env.example"]:
            if (path / env_file).exists():
                info.environment_files.append(env_file)

    def _contains_keyword(self, path: Path, keyword: str) -> bool:
        try:
            for f in path.rglob("*"):
                if f.is_file() and f.suffix in (".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml"):
                    try:
                        if keyword in f.read_text(errors="ignore"):
                            return True
                    except Exception:
                        continue
        except Exception:
            pass
        return False


repository_analyzer = RepositoryAnalyzer
