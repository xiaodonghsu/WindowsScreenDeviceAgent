import subprocess
import time

def run_command(command: str):
    """
    执行 Windows 命令行，并返回执行结果
    """
    try:
        result = subprocess.run(
            command,
            shell=True,              # 允许执行完整命令行
            capture_output=True,     # 捕获输出
            text=True,               # 返回字符串而不是字节
            # encoding="utf-8",        # 避免中文乱码
            timeout=10               # 防止卡死
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timeout"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def screen_shutdown(delay: int = 5):
    from player import close_browser
    close_browser()
    time.sleep(1)
    run_command(f"shutdown -s -t {delay}")

def screen_restart(delay: int = 5):
    from player import close_browser
    close_browser()
    time.sleep(1)
    run_command(f"shutdown -r -t {delay}")

def screen_startup():
    pass