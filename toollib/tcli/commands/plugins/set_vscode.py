"""
@author axiner
@version v1.0.0
@created 2023/9/21 10:10
@abstract 设置 VS Code
@description
@history
"""

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import shutil


class SetVSCode:
    def __init__(
        self,
        project_dir: str | Path | None = None,
        enable_conda: bool = False,
        enable_prettier: bool = False,
    ):
        self.project_dir = Path(project_dir).resolve() if project_dir else Path.cwd()
        self.enable_conda = enable_conda
        self.enable_prettier = enable_prettier

        self.PrettierConfigName = ".prettierrc"
        self.PrettierIgnoreName = ".prettierignore"

        self.VSCodeDirName = ".vscode"
        self.SettingsFileName = "settings.json"
        self.LaunchFileName = "launch.json"
        self.ExtensionsFileName = "extensions.json"
        self.PyprojectFileName = "pyproject.toml"

        self.BackupDirName = ".config-backup"

    def backup_config_file(self, file_path: Path) -> Path | None:
        if not self.project_dir:
            return None
        if file_path.exists():
            backup_dir = self.project_dir / self.BackupDirName
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_file = backup_dir / f"{file_path.name}.{timestamp}.bak"

            shutil.copy2(file_path, backup_file)
            print(f"  已备份: {backup_file}")

            self._cleanup_old_backups(backup_dir)

            return backup_file
        return None

    @staticmethod
    def _cleanup_old_backups(backup_dir: Path, max_age_days: int = 30, max_count: int = 6 * 2) -> int:
        if not backup_dir.exists():
            return 0

        now = datetime.now()
        backup_files = sorted(backup_dir.glob("*.bak"), key=lambda f: f.stat().st_mtime, reverse=True)

        cleaned_count = 0

        if len(backup_files) > max_count:
            for old_file in backup_files[max_count:]:
                try:
                    old_file.unlink()
                    cleaned_count += 1
                except Exception:
                    pass

        for backup_file in backup_files[:max_count]:
            try:
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if (now - file_mtime).days > max_age_days:
                    backup_file.unlink()
                    cleaned_count += 1
            except Exception:
                pass

        if cleaned_count > 0:
            print(f"  已清理 {cleaned_count} 个旧备份文件")

        return cleaned_count

    def write_config_file(self, file_path: Path, config_data: dict | str, description: str):
        self.backup_config_file(file_path)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                if isinstance(config_data, dict):
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(config_data)
            print(f"  已写入 {description}: {file_path}")
        except Exception as e:
            print(f"  错误: 无法写入 {description} - {e}")

    def set_vscode_settings(self, vscode_dir: Path):
        print("\n[*] 配置 VS Code 设置...")
        vscode_settings_content = """{
  // ================= basic =================
  "explorer.decorations.badges": true,
  "explorer.confirmDelete": true,
  "explorer.confirmDragAndDrop": true,
  "explorer.decorations.colors": true,
  "workbench.colorCustomizations": {
    "editorGroup.border": "#888888",
    "sideBar.border": "#666666",
    "panel.border": "#666666",
    "activityBar.border": "#555555",
    "statusBar.border": "#555555",
    "titleBar.border": "#555555",
    "tab.activeBorder": "#00aaff",
    "tab.activeBorderTop": "#00aaff"
  },
  "editor.formatOnSave": true,
  "editor.rulers": [120],
  "editor.fontSize": 14,
  "editor.lineHeight": 1.5,
  "editor.tabSize": 2,
  "editor.insertSpaces": true,
  "editor.detectIndentation": false,
  "editor.wordWrap": "off",
  "editor.minimap.enabled": false,
  "editor.stickyScroll.enabled": true,
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": true,
  "files.enableTrash": true,
  "files.exclude": {
    "**/.git": true,
    "**/.hg": true,
    "**/.svn": true,
    "**/venv": true,
    "**/.venv": true,
    "**/env": true,
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/*.pyo": true,
    "**/*.pyd": true,
    "**/.pytest_cache": true,
    "**/.tox": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/.pyright": true,
    "**/.coverage": true,
    "**/htmlcov": true
  },
  "search.exclude": {
    "**/.git": true,
    "**/.hg": true,
    "**/.svn": true,
    "**/venv": true,
    "**/.venv": true,
    "**/env": true,
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/*.pyo": true,
    "**/*.pyd": true,
    "**/.pytest_cache": true,
    "**/.tox": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/.pyright": true,
    "**/.coverage": true,
    "**/htmlcov": true,
    "**/build": true,
    "**/dist": true,
    "**/*.egg-info": true,
    "**/*.log": true,
    "**/*.tmp": true,
    "**/temp": true,
    "**/tmp": true
  },

  // ================= Terminal =================
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.fontSize": 13,
  "terminal.integrated.lineHeight": 1.2,
  "terminal.integrated.enablePersistentSessions": true,
  "python.terminal.activateEnvironment": true,
  "python.terminal.executeInFileDir": true,
  "python.terminal.focusAfterLaunch": true,

  // ================= Python analysis =================
  "basedpyright.analysis.typeCheckingMode": "standard",
  "basedpyright.analysis.diagnosticMode": "openFilesOnly",
  "basedpyright.analysis.autoImportCompletions": true,
  "basedpyright.analysis.inlayHints.variableTypes": false,
  "basedpyright.analysis.inlayHints.functionReturnTypes": false,
  "basedpyright.analysis.inlayHints.callArgumentNames": false,

  // ================= Ruff =================
  "[python]": {
    "editor.tabSize": 4,
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },

  // ================= Prettier =================
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[css]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
"""
        vscode_settings_file = vscode_dir / self.SettingsFileName
        self.write_config_file(vscode_settings_file, vscode_settings_content, "VS Code 设置配置")

    def set_vscode_debug_config(self, vscode_dir: Path):
        print("\n[*] 配置 VS Code 调试...")
        launch_config_file = vscode_dir / self.LaunchFileName
        launch_config = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: 当前文件",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: 当前文件(切目录)",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "cwd": "${fileDirname}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: 当前模块",
      "type": "debugpy",
      "request": "launch",
      "module": "${relativeFileDirname}.${fileBasenameNoExtension}",
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: 当前模块(带参数)",
      "type": "debugpy",
      "request": "launch",
      "module": "${relativeFileDirname}.${fileBasenameNoExtension}",
      "cwd": "${workspaceFolder}",
      "args": "${input:programArgs}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: PYTEST(当前文件)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-s", "-vv"],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: 附加到(本地进程)",
      "type": "debugpy",
      "request": "attach",
      "processId": "${command:pickProcess}"
    }
  ],
  "inputs": [
    {
      "id": "programArgs",
      "type": "promptString",
      "description": "输入程序参数 (例如: --config config.yaml)"
    }
  ]
}
"""
        self.write_config_file(launch_config_file, launch_config, "VS Code 调试配置")

    def set_vscode_extensions_config(self, vscode_dir: Path):
        print("\n[*] 配置 VS Code 扩展...")
        extensions_file = vscode_dir / self.ExtensionsFileName
        extensions_content = """{
  "recommendations": [
    // ==================== Python开发 (必选) ====================
    "ms-python.python",
    "ms-python.debugpy",
    "detachhead.basedpyright",
    "charliermarsh.ruff",
    "njpwerner.autodocstring",

    // ==================== 前端开发 (可选) ====================
    "esbenp.prettier-vscode",
    "vue.volar",

    // ==================== 效率工具 (可选) ====================
    "alefragnani.project-manager",
    "k--kato.intellij-idea-keybindings",
    "mhutchie.git-graph",
    "cweijan.vscode-database-client2",
    "cweijan.dbclient-jdbc",
    "alibaba-cloud.tongyi-lingma"
  ]
}
"""
        self.write_config_file(extensions_file, extensions_content, "VS Code 扩展配置")

    @staticmethod
    def _get_pyproject_config(tool_name: str) -> str:
        if tool_name == "basedpyright":
            return """# ==================== BasedPyright 配置 ====================
[tool.basedpyright]
typeCheckingMode = "standard"
include = [
  "**/*.py",
]
exclude = [
  "**/build/**",
  "**/dist/**",
  "**/.egg-info/**",
  "**/venv/**",
  "**/.venv/**",
  "**/__pycache__/**",
  "**/.mypy_cache/**",
  "**/.pytest_cache/**",
  "**/.tox/**",
  "**/migrations/**",
  "**/node_modules/**",
]

# diagnosticSeverityOverrides
reportAttributeAccessIssue = "warning"
reportCallIssue = "warning"
reportOptionalMemberAccess = "warning"
reportUnusedImport = "information"
reportUnusedClass = "information"
reportUnusedFunction = "information"
reportArgumentType = "none"
reportAssignmentType = "none"
reportUnknownVariableType = "none"
reportUnknownMemberType = "none"
reportUnknownParameterType = "none"
reportMissingTypeStubs = "none"
"""
        elif tool_name == "ruff":
            return """# ==================== Ruff 配置 ====================
[tool.ruff]
line-length = 120

[tool.ruff.format]
skip-magic-trailing-comma = false

[tool.ruff.lint]
select = [
  "E",   # pycodestyle errors
  "W",   # pycodestyle warnings
  "F",   # pyflakes
  "I",   # isort (导入排序)
  "UP",  # pyupgrade (提示新语法)
  "B",   # flake8-bugbear (常见bug)
  "SIM", # flake8-simplify (代码简化)
  "C4",  # flake8-comprehensions (推导式优化)
  "RUF", # Ruff 特有规则
]

ignore = [
  "E501",   # 行长度由 formatter 控制，lint 不需要报错
  "B008",   # 允许在函数默认参数中调用函数 (常用于 FastAPI/Depends)
  "COM812", # 避免与 formatter 的 trailing comma 冲突
  "D",      # 忽略所有文档字符串相关规则（如 D100、D205 等）
  "RUF001", # 允许注释中使用非 ASCII 字符（如中文）
  "RUF002", # 允许字符串字面量中使用非 ASCII 字符（如中文提示语）
  "RUF003", # 允许文档字符串（docstring）中使用非 ASCII 字符
  "I001",
  "W293",
  "UP015",
  "RUF022",
  "RUF012",
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**" = ["S101", "PLR2004", "ARG", "B018"]
"test_*.py" = ["S101", "PLR2004", "ARG", "B018"]
"*_test.py" = ["S101", "PLR2004", "ARG", "B018"]
"scripts/**" = ["T201", "INP001"]
"bin/**" = ["T201", "INP001"]
"conftest.py" = ["F401"]
"settings.py" = ["F401"]
"config.py" = ["F401"]
"*.ipynb" = ["E402", "E703"]
"**/migrations/**" = ["E501", "N999"]
"**/alembic/versions/**" = ["E501", "N999"]
"""
        else:
            return ""

    def set_pyproject_config(self):
        print("\n[*] 配置 pyproject.toml (basedpyright & ruff)...")

        description = "pyproject.toml 配置"
        tool_names = ["basedpyright", "ruff"]

        pyproject_file = self.project_dir / self.PyprojectFileName
        if pyproject_file.is_file():
            try:
                with open(pyproject_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"  错误: 无法读取 {description} - {e}")
                return

            self.backup_config_file(pyproject_file)

            append_content = ""
            for tool_name in tool_names:
                if f"[tool.{tool_name}]" not in content:
                    append_content += self._get_pyproject_config(tool_name).strip()
                    append_content += "\n\n"
                    print(f"  已追加 {tool_name} 配置")
                else:
                    print(f"  已忽略 {tool_name} 配置已存在")

            if append_content:
                content = content.strip() + "\n\n"
                new_content = content + append_content
                try:
                    with open(pyproject_file, "w", encoding="utf-8") as f:
                        f.write(new_content.strip() + "\n")
                    print(f"  已更新 {description} - {pyproject_file}")
                except Exception as e:
                    print(f"  错误: 无法写入 {description} - {e}")
            else:
                print("  已忽略 BasedPyright & Ruff 配置已存在")
        else:
            new_content = ""
            for tool_name in tool_names:
                new_content += self._get_pyproject_config(tool_name).strip()
                new_content += "\n\n"
            self.write_config_file(pyproject_file, new_content.strip() + "\n", description)

    def set_prettier_config(self):
        print("\n[*] 配置 Prettier...")
        prettier_config_content = """{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "useTabs": false,
  "printWidth": 120,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "auto",
  "htmlWhitespaceSensitivity": "css",
  "vueIndentScriptAndStyle": false
}
"""
        prettier_config_file = self.project_dir / self.PrettierConfigName
        self.write_config_file(prettier_config_file, prettier_config_content, "Prettier 配置")
        # 安装 Prettier 忽略配置
        prettier_ignore_content = """# === 构建产物 & 打包输出 ===
dist/
out/
build/
public/build/
.next/
.nuxt/
.cache/

# === 依赖目录 ===
node_modules/
.venv/
venv/
env/

# === Python 相关 ===
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/

# === 日志 & 临时文件 ===
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# === 压缩/编译后的资源（Prettier 不应格式化）===
*.min.js
*.min.css
*.bundle.js
*.chunk.js

# === 版本控制 ===
.git/
.svn/
.hg/

# === IDE / 编辑器 ===
.idea/
.vscode/
*.sublime-project
*.sublime-workspace

# === 系统文件 ===
.DS_Store
Thumbs.db
desktop.ini
Icon?

# === 配置与锁文件（通常不格式化）===
package-lock.json
yarn.lock
pnpm-lock.yaml
poetry.lock
Pipfile.lock

# === 静态资源（图片、字体、二进制等）===
*.png
*.jpg
*.jpeg
*.gif
*.svg
*.ico
*.woff
*.woff2
*.ttf
*.eot
*.pdf
*.zip
*.tar.gz

# === 其他不应格式化的文件 ===
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
Dockerfile
Makefile
"""
        prettier_ignore_file = self.project_dir / self.PrettierIgnoreName
        self.write_config_file(prettier_ignore_file, prettier_ignore_content, "Prettier 忽略配置")

    def set_configs(self, enable_prettier: bool = False):
        vscode_dir = self.project_dir / self.VSCodeDirName
        if not vscode_dir.exists():
            vscode_dir.mkdir(parents=True, exist_ok=True)
        self.set_vscode_settings(vscode_dir)
        self.set_vscode_debug_config(vscode_dir)
        self.set_vscode_extensions_config(vscode_dir)
        self.set_pyproject_config()
        if enable_prettier:
            self.set_prettier_config()

    def _run_command(self, cmd_list: list, cwd: Path | None = None) -> tuple:
        try:
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding="utf-8",
                shell=os.name == "nt",  # Windows 使用 shell=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def install_tools(self):
        print("\n[*] 安装工具包...")
        success, _, _ = self._run_command(["python", "--version"])
        if not success:
            print("  警告: 未找到 python 命令，跳过 ruff 安装")
            return
        print("  正在安装 ruff...")
        success, _, _ = self._run_command(
            [
                "python",
                "-m",
                "pip",
                "install",
                "-U",
                "ruff",
                "-q",
                "--user",
                "--no-warn-script-location",
            ]
        )
        if success:
            print("  已安装 ruff")
        else:
            print("  警告: ruff 安装失败")

    def initialize_conda(self):
        print("[*] 初始化 Conda for PowerShell...")
        success, _, _ = self._run_command(["conda", "init", "powershell"])
        if success:
            print("  已初始化 Conda (请重启 VS Code 生效)")
        else:
            print("  警告: 未找到 conda，跳过 Conda 初始化")

    def run(self):
        """入口"""
        os.system("cls" if os.name == "nt" else "clear")

        if not self.project_dir.is_dir():
            print(f"错误: 路径不是目录 {self.project_dir}")
            return

        print("")
        print("-" * 25)
        print("  开始配置")
        print("-" * 25)

        # 初始化Conda
        if self.enable_conda:
            self.initialize_conda()
        # 安装工具
        self.install_tools()
        # 设置配置
        self.set_configs(enable_prettier=self.enable_prettier)

        print("")
        print("-" * 25)
        print("  全部配置完成!")
        print("-" * 25)
        print("")
        print("配置文件位置:")
        print(f"  - 项目:     {self.project_dir / self.VSCodeDirName / self.SettingsFileName}")
        print(f"  - 项目:     {self.project_dir / self.VSCodeDirName / self.LaunchFileName}")
        print(f"  - 项目:     {self.project_dir / self.VSCodeDirName / self.ExtensionsFileName}")
        print(f"  - 项目:     {self.project_dir / self.PyprojectFileName}")
        if self.enable_prettier:
            print(f"  - 项目:     {self.project_dir / self.PrettierConfigName}")
            print(f"  - 项目:     {self.project_dir / self.PrettierIgnoreName}")
        print(f"  - 备份:     {self.project_dir / self.BackupDirName}")
        print("")
        print("-" * 50)
        print("  重要: 安装 VS Code 扩展（请查看项目根目录下的 .vscode/extensions.json）")
        print("")
        print("  安装方式:")
        print("    - 按 Ctrl+Shift+X 打开扩展面板")
        print("    - 搜索扩展名称并安装")
        print("-" * 35)


if __name__ == "__main__":
    s = SetVSCode(
        enable_conda=True,
        enable_prettier=True,
    )
    s.run()
