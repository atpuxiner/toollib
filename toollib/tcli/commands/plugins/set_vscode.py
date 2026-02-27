"""
@author axiner
@version v1.0.0
@created 2023/9/21 10:10
@abstract VSCode 配置
@description
@history
"""
import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any


class SetVSCode:
    """VSCode 配置"""

    def __init__(self):
        # 目录和文件名称常量
        self.PrettierConfigName = ".prettierrc"
        self.PrettierIgnoreName = ".prettierignore"
        self.VSCodeDirName = ".vscode"
        self.SettingsFileName = "settings.json"
        self.LaunchFileName = "launch.json"
        self.ExtensionsFileName = "extensions.json"
        self.BackupDirName = ".vscode-backup"

        # 用户主目录
        self.user_profile = Path.home()
        self.temp_dir = Path(tempfile.gettempdir())

        # 配置模板
        self._init_config_templates()

    def _init_config_templates(self):
        """初始化配置模板"""
        self.prettier_config = {
            "semi": True,
            "singleQuote": False,
            "tabWidth": 2,
            "useTabs": False,
            "printWidth": 100,
            "trailingComma": "es5",
            "bracketSpacing": True,
            "arrowParens": "avoid",
            "endOfLine": "auto",
            "htmlWhitespaceSensitivity": "css",
            "vueIndentScriptAndStyle": False
        }

        self.prettier_ignore_content = '''# 依赖目录
node_modules/
dist/
build/

# Python 相关
__pycache__/
*.pyc
.venv/
venv/

# 日志和数据
*.log
*.min.js
*.min.css

# 其他
.git/
.idea/
#.vscode/
'''

    def get_vscode_dir(self, project_path: Path) -> Path:
        """获取或创建VS Code配置目录"""
        vscode_dir = project_path / self.VSCodeDirName
        if not vscode_dir.exists():
            vscode_dir.mkdir(parents=True, exist_ok=True)
            print(f"  创建目录: {vscode_dir}")
        return vscode_dir

    def backup_config_file(self, file_path: Path) -> Path | None:
        """备份配置文件到临时目录"""
        if file_path.exists():
            backup_dir = self.temp_dir / self.BackupDirName
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{file_path.name}.{timestamp}.bak"

            shutil.copy2(file_path, backup_file)
            print(f"  已备份: {backup_file}")

            # 清理旧备份文件
            self.cleanup_old_backups(backup_dir)

            return backup_file
        return None

    @staticmethod
    def cleanup_old_backups(backup_dir: Path, max_age_days: int = 30, max_count: int = 5*2) -> int:
        """
        清理旧的备份文件

        Args:
            backup_dir: 备份目录路径
            max_age_days: 最大保留天数（默认30天）
            max_count: 最大保留数量（默认10个）

        Returns:
            清理的文件数量
        """
        if not backup_dir.exists():
            return 0

        now = datetime.now()
        backup_files = sorted(
            backup_dir.glob("*.bak"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        cleaned_count = 0

        # 按数量限制清理（保留最新的N个）
        if len(backup_files) > max_count:
            for old_file in backup_files[max_count:]:
                try:
                    old_file.unlink()
                    cleaned_count += 1
                except Exception:
                    pass

        # 按时间清理（删除超过N天的备份）
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

    def _write_config_file(self, file_path: Path, config_data: dict[str, Any], description: str):
        """写入配置文件的通用方法"""
        self.backup_config_file(file_path)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print(f"  {description}: {file_path}")
        except Exception as e:
            print(f"  错误: 无法写入 {description} - {str(e)}")

    def install_prettier_config(self):
        """安装Prettier配置"""
        print("\n[*] 配置 Prettier...")

        # 安装 Prettier 配置文件
        prettier_config_file = self.user_profile / self.PrettierConfigName
        self._write_config_file(
            prettier_config_file,
            self.prettier_config,
            "已安装 Prettier 配置"
        )

        # 安装 Prettier 忽略文件
        prettier_ignore_file = self.user_profile / self.PrettierIgnoreName
        self.backup_config_file(prettier_ignore_file)
        try:
            with open(prettier_ignore_file, 'w', encoding='utf-8') as f:
                f.write(self.prettier_ignore_content)
            print(f"  已安装: {prettier_ignore_file}")
        except Exception as e:
            print(f"  错误: 无法写入 Prettier 忽略文件 - {str(e)}")

    def get_vscode_settings_template(self) -> str:
        """获取VS Code设置模板"""
        return '''{
  // ==================== Conda 默认环境（自行修改） ====================
  "terminal.integrated.profiles.windows": {
    "PowerShell": {
      "source": "PowerShell",
      "args": ["-NoExit", "-Command", "conda activate base"]
    }
  },

  // ==================== 基本配置 ====================
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "editor.formatOnSave": true,
  "editor.rulers": [120],
  "editor.fontSize": 14,
  "editor.lineHeight": 1.5,
  "editor.tabSize": 2,
  "editor.detectIndentation": false,
  "editor.insertSpaces": true,
  "editor.wordWrap": "off",
  "editor.minimap.enabled": false,
  "editor.stickyScroll.enabled": true,
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": true,
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
  "files.exclude": {
    "**/.git": true,
    "**/.idea": true,
    "**/__pycache__": true,
    "**/.venv": true,
    "**/venv": true,
    "**/node_modules": true,
    "**/.DS_Store": true,
    "**/Thumbs.db": true
  },
  "files.enableTrash": true,
  "explorer.decorations.badges": true,
  "explorer.confirmDelete": true,
  "explorer.confirmDragAndDrop": true,
  "explorer.decorations.colors": true,

  // ==================== 终端配置 ====================
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.enablePersistentSessions": true,
  "terminal.integrated.fontSize": 13,
  "terminal.integrated.lineHeight": 1.2,
  "python.terminal.activateEnvironment": false,
  "python.terminal.executeInFileDir": true,
  "python.terminal.focusAfterLaunch": true,

  // ==================== Code Runner 配置 ====================
  "code-runner.runInTerminal": true,
  "code-runner.executorMap": {
    "python": "python -u"
  },
  "code-runner.preserveFocus": true,
  "code-runner.clearPreviousOutput": false,
  "code-runner.ignoreSelection": false,
  "code-runner.showRunIconInEditorTitleMenu": false,
  "code-runner.showRunCommandInEditorContextMenu": false,

  // ==================== Python 格式化与检查 ====================
  "autopep8.path": ["autopep8"],
  "autopep8.args": ["--max-line-length=120"],
  "[python]": {
    "editor.tabSize": 4,
    "editor.defaultFormatter": "ms-python.autopep8",
    "editor.quickSuggestions": {
      "other": true,
      "comments": false,
      "strings": true
    },
    "editor.acceptSuggestionOnEnter": "on"
  },
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
  "[scss]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[yaml]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "isort.args": ["--profile=pycharm", "--line-length=120"],

  // ==================== Python 类型检查与分析 (Pyright) ====================
  "python.analysis.typeCheckingMode": "standard",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.autoSearchPaths": true,
  "python.analysis.diagnosticMode": "openFilesOnly",
  "python.analysis.diagnosticSeverityOverrides": {
    // --- Error (会阻止代码运行或导致严重问题) ---
    "reportPropertyTypeMismatch": "error",
    "reportFunctionMemberAccess": "error",
    "reportInvalidTypeForm": "error",
    "reportOptionalSubscript": "error",
    "reportOptionalMemberAccess": "error",
    "reportOptionalCall": "error",
    "reportOptionalIterable": "error",
    "reportOptionalContextManager": "error",
    "reportOptionalOperand": "error",
    "reportIncompatibleMethodOverride": "error",
    "reportIncompatibleVariableOverride": "error",
    "reportOverlappingOverload": "error",
    "reportUndefinedVariable": "error",
    "reportUnboundVariable": "error",
    "reportMatchNotExhaustive": "error",
    // --- Warning (代码质量问题, 建议修复) ---
    "reportPossiblyUnboundVariable": "warning",
    "reportMissingImports": "warning",
    "reportReturnType": "warning",
    "reportMissingModuleSource": "warning",
    "reportImportCycles": "warning",
    "reportUnusedImport": "warning",
    "reportUnusedClass": "warning",
    "reportUnusedFunction": "warning",
    "reportUnusedVariable": "warning",
    "reportDuplicateImport": "warning",
    "reportUntypedClassDecorator": "warning",
    "reportUntypedBaseClass": "warning",
    "reportUntypedNamedTuple": "warning",
    "reportPrivateUsage": "warning",
    "reportConstantRedefinition": "warning",
    "reportDeprecated": "warning",
    "reportInvalidTypeVarUse": "warning",
    "reportUnnecessaryCast": "warning",
    "reportAssertAlwaysTrue": "warning",
    "reportSelfClsParameterName": "warning",
    "reportUnsupportedDunderAll": "warning",
    "reportUnusedExpression": "warning",
    "reportShadowedImports": "warning",
    // --- Information (提示信息) ---
    "reportUnnecessaryTypeIgnoreComment": "information",
    // --- None (禁用检查) ---
    "reportCallInDefaultInitializer": "none",
    "reportCallIssue": "none",
    "reportAttributeAccessIssue": "none",
    "reportAssignmentType": "none",
    "reportArgumentType": "none",
    "reportUnknownParameterType": "none",
    "reportUnknownArgumentType": "none",
    "reportUnknownLambdaType": "none",
    "reportUnknownVariableType": "none",
    "reportUnknownMemberType": "none",
    "reportMissingTypeStubs": "none",
    "reportUntypedFunctionDecorator": "none",
    "reportUninitializedInstanceVariable": "none",
    "reportMissingTypeArgument": "none",
    "reportMissingSuperCall": "none",
    "reportUnnecessaryComparison": "none",
    "reportUnnecessaryContains": "none",
    "reportImplicitStringConcatenation": "none",
    "reportInvalidStubStatement": "none",
    "reportIncompleteStub": "none",
    "reportGeneralTypeIssues": "none",
    "reportInvalidStringEscapeSequence": "none",
    "reportUnnecessaryIsInstance": "none"
  },

  // ==================== Python 代码检查 (Pylint) ====================
  "pylint.args": [
    "--max-line-length=120",
    "--disable=C0103,C0114,C0115,C0116,C0209,C0303,E1101,W0511,W0613,W0702,W0707,W0718,W1203,W1510,W1514",
    "--enable=W0101,W0102,W0104,W0404,W0611,W0612,W0621,W0622,W1515"
  ]
}'''

    def install_vscode_settings(self, project_path: Path):
        """安装VS Code项目设置"""
        print("\n[*] 配置 VS Code 项目设置...")

        vscode_dir = self.get_vscode_dir(project_path)
        vscode_settings_file = vscode_dir / self.SettingsFileName

        settings_content = self.get_vscode_settings_template()
        self.backup_config_file(vscode_settings_file)
        try:
            with open(vscode_settings_file, 'w', encoding='utf-8') as f:
                f.write(settings_content)
            print(f"  已创建 VS Code 设置: {vscode_settings_file}")
        except Exception as e:
            print(f"  错误: 无法写入 VS Code 设置 - {str(e)}")

    def install_project_debug_config(self, project_path: Path):
        """安装项目调试配置"""
        print("\n[*] 创建项目调试配置...")

        vscode_dir = self.get_vscode_dir(project_path)
        launch_config_file = vscode_dir / self.LaunchFileName

        launch_config = {
            "version": "0.0.1",
            "configurations": [
                {
                    "name": "Python: 当前文件",
                    "type": "debugpy",
                    "request": "launch",
                    "program": "${file}",
                    "cwd": "${fileDirname}",
                    "console": "integratedTerminal",
                    "justMyCode": False,
                    "python": "${command:python.interpreterPath}"
                },
                {
                    "name": "Python: 指定模块",
                    "type": "debugpy",
                    "request": "launch",
                    "module": "${input:moduleName}",
                    "cwd": "${workspaceFolder}",
                    "console": "integratedTerminal",
                    "justMyCode": False,
                    "python": "${command:python.interpreterPath}"
                },
                {
                    "name": "Python: 带参数调试",
                    "type": "debugpy",
                    "request": "launch",
                    "program": "${file}",
                    "cwd": "${fileDirname}",
                    "console": "integratedTerminal",
                    "args": "${input:arguments}",
                    "justMyCode": False,
                    "python": "${command:python.interpreterPath}"
                },
                {
                    "name": "Python: 附加到进程",
                    "type": "debugpy",
                    "request": "attach",
                    "connect": {
                        "host": "localhost",
                        "port": 5678
                    }
                }
            ],
            "inputs": [
                {
                    "id": "moduleName",
                    "type": "promptString",
                    "description": "输入要调试的模块名 (如: main 或 src.main)"
                },
                {
                    "id": "arguments",
                    "type": "promptString",
                    "description": "输入命令行参数"
                }
            ]
        }

        self._write_config_file(launch_config_file, launch_config, "已创建调试配置")

    def install_vscode_extensions_config(self, project_path: Path):
        """安装VS Code扩展配置"""
        print("\n[*] 创建扩展配置...")

        vscode_dir = self.get_vscode_dir(project_path)
        extensions_file = vscode_dir / self.ExtensionsFileName
        extensions_content = '''{
  "recommendations": [
    // ==================== Python开发 (必选) ====================
    "ms-python.python",
    "ms-python.debugpy",
    "ms-python.autopep8",
    "ms-python.isort",
    "ms-pyright.pyright",
    "ms-python.pylint",
    "formulahendry.code-runner",
    "njpwerner.autodocstring",

    // ==================== 前端开发 (可选) ====================
    "esbenp.prettier-vscode",
    "Vue.volar",

    // ==================== 效率工具 (可选) ====================
    "alefragnani.project-manager",
    "k--kato.intellij-idea-keybindings",
    "mhutchie.git-graph",
    "Alibaba-cloud.tongyi-lingma",

    // ==================== 数据库工具 (可选) ====================
    "mtxr.sqltools",
    "mtxr.sqltools-driver-mysql",
    "mtxr.sqltools-driver-pg",
    "mtxr.sqltools-driver-sqlite",
    "cweijan.vscode-redis-client"
  ]
}'''

        self.backup_config_file(extensions_file)
        try:
            with open(extensions_file, 'w', encoding='utf-8') as f:
                f.write(extensions_content)
            print(f"  已创建扩展配置: {extensions_file}")
        except Exception as e:
            print(f"  错误: 无法写入扩展配置 - {str(e)}")

    def install_all_global(self, project_path: Path):
        """安装所有全局配置"""
        self.install_prettier_config()
        self.install_vscode_settings(project_path)
        self.install_project_debug_config(project_path)
        self.install_vscode_extensions_config(project_path)

    def remove_global_config(self):
        """删除全局配置"""
        print("\n[*] 删除全局配置...")

        # 删除 Prettier 配置
        prettier_config_file = self.user_profile / self.PrettierConfigName
        prettier_ignore_file = self.user_profile / self.PrettierIgnoreName

        for config_file in [prettier_config_file, prettier_ignore_file]:
            if config_file.exists():
                config_file.unlink()
                print(f"  已删除: {config_file}")
            else:
                print(f"  不存在: {config_file}")

        print("  全局配置文件已清理")

    def remove_project_config(self, project_path: Path):
        """删除项目配置"""
        print("\n[*] 删除项目配置...")

        vscode_dir = project_path / self.VSCodeDirName
        if vscode_dir.exists():
            shutil.rmtree(vscode_dir)
            print(f"  已删除: {vscode_dir}")
        else:
            print(f"  不存在: {vscode_dir}")

    def run_command(self, cmd_list: list, cwd: Path = None) -> tuple:
        """运行命令并返回结果"""
        try:
            # 在 Windows 上使用 shell=True 以正确解析 PATH
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                shell=os.name == 'nt'  # Windows 使用 shell=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def install_python_tools(self):
        """安装Python工具包"""
        print("\n[*] 安装 Python 工具包...")

        # 检查python命令是否存在
        success, _, _ = self.run_command(['python', '--version'])
        if not success:
            print("  警告: 未找到 python 命令，跳过 Python 工具安装")
            return

        print("  正在安装 autopep8, isort, pylint...")
        success, _, _ = self.run_command([
            'python', '-m', 'pip', 'install', '-U', 'autopep8', 'isort', 'pylint', '-q', '--no-warn-script-location'
        ])

        # 检查npm命令是否存在
        npm_success, _, _ = self.run_command(['npm', '--version'])
        if not npm_success:
            print("  警告: 未找到 npm，跳过 pyright 安装")
        else:
            print("  正在安装 pyright (Node.js 工具)...")
            npm_success, _, npm_stderr = self.run_command(['npm', 'install', '-g', 'pyright'])
            if npm_success:
                print("    pyright 安装成功")
            else:
                print(f"    pyright 安装失败: {npm_stderr}")

        print("  Python 工具包安装完成")

    def initialize_conda(self):
        """初始化Conda for PowerShell"""
        print("[*] 初始化 Conda for PowerShell...")

        success, _, _ = self.run_command(['conda', 'init', 'powershell'])
        if success:
            print("  Conda 初始化完成 (请重启 VS Code 生效)")
        else:
            print("  警告: 未找到 conda，跳过 Conda 初始化")

    def print_completion_message(self, project_path: Path):
        """打印完成消息"""
        print("-" * 25)
        print("  全部配置安装完成!")
        print("-" * 25)
        print("")
        print("配置文件位置:")
        print(f"  - 全局:     {self.user_profile / self.PrettierConfigName}")
        print(f"  - 项目:     {project_path / self.VSCodeDirName / self.SettingsFileName}")
        print(f"  - 项目:     {project_path / self.VSCodeDirName / self.LaunchFileName}")
        print(f"  - 项目:     {project_path / self.VSCodeDirName / self.ExtensionsFileName}")
        print("")
        print("-" * 50)
        print("  重要: 安装 VS Code 扩展（请查看项目根目录下的 .vscode/extensions.json）")
        print("")
        print("安装方式:")
        print("  - 按 Ctrl+Shift+X 打开扩展面板")
        print("  - 搜索扩展名称并安装")
        print("-" * 35)

    def run(self):
        """入口"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("┌" + "─" * 46 + "┐")
        print("│" + " " * 14 + "VSCode环境配置工具" + " " * 14 + "│")
        print("└" + "─" * 46 + "┘")
        print("")
        print("请选择要执行的配置:")
        print("")
        print("  [1] 配置 (全局 + 项目)")
        print("  [2] 删除配置 (全局 + 项目)")
        print("  [q] 退出")
        print("")

        choice = input("请输入选项 (默认q): ").strip() or "q"

        if choice == "1":
            print("")
            default_path = Path.cwd()
            project_path_input = input(f"请输入项目根目录路径 [默认: {default_path}]: ").strip()
            project_path = Path(project_path_input) if project_path_input else default_path
            print(f"  将采用默认路径: {project_path}")

            if not project_path.exists():
                print(f"错误: 路径不存在 {project_path}")
                return
            if not project_path.is_dir():
                print(f"错误: 路径不是目录 {project_path}")
                return

            print("")
            print("-" * 25)
            print("  开始安装全局配置")
            print("-" * 25)

            # 初始化Conda
            self.initialize_conda()

            # 安装Python工具
            self.install_python_tools()

            # 安装所有配置
            self.install_all_global(project_path)

            print("")
            self.print_completion_message(project_path)

        elif choice == "2":
            print("")
            default_path = Path.cwd()
            project_path_input = input(f"请输入项目根目录路径 [默认: {default_path}]: ").strip()
            project_path = Path(project_path_input) if project_path_input else default_path
            print(f"  将采用默认路径: {project_path}")

            print("")
            print("-" * 25)
            print("  开始删除配置")
            print("-" * 25)

            self.remove_global_config()
            self.remove_project_config(project_path)

            print("")
            print("-" * 25)
            print("  配置删除完成!")
            print("-" * 25)
            print("")
            print("已删除的配置:")
            print(f"  - 全局: {self.user_profile / self.PrettierConfigName}")
            print(f"  - 全局: {self.user_profile / self.PrettierIgnoreName}")
            print(f"  - 项目: {project_path / self.VSCodeDirName}")

        elif choice == "q":
            print("已取消")
            return
        else:
            print("无效选项")
            return

        input("\n按 Enter 键退出...")
