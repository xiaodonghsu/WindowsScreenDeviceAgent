import json
import re
import urllib.request

def get_cpu_temperature(host="127.0.0.1", port=8110, timeout=3) -> dict:
    """
    从 LibreHardwareMonitor Web Server 读取 CPU 温度。
    返回格式: [current, min, max]
    失败时返回: [-1, -1, -1]
    """

    url = f"http://{host}:{port}/data.json"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        return [-1, -1, -1]

    matches = []

    def parse_temp(text):
        """
        从 '54.2 °C' / '54 °C' / '54' 中提取数字
        """
        if text is None:
            return None
        if isinstance(text, (int, float)):
            return float(text)

        s = str(text).strip()
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        return float(m.group()) if m else None

    def is_cpu_temp_node(node):
        """
        判断节点是否像 CPU 温度传感器
        """
        text_parts = [
            str(node.get("Text", "")),
            str(node.get("Name", "")),
            str(node.get("Id", "")),
            str(node.get("ImageURL", "")),
            str(node.get("Min", "")),
            str(node.get("Value", "")),
            str(node.get("Max", "")),
        ]
        text = " ".join(text_parts).lower()

        has_cpu = any(k in text for k in ["cpu", "package", "core", "ccd"])
        has_temp = ("temperature" in text) or ("°c" in text) or ("temp" in text)

        return has_cpu and has_temp

    def walk(node, parent_text=""):
        if isinstance(node, dict):
            current_text = f"{parent_text} {node.get('Text', '')}".lower()

            if is_cpu_temp_node(node) or (
                any(k in current_text for k in ["cpu", "package", "core", "ccd"])
                and any(k in current_text for k in ["temperature", "temp", "°c"])
            ):
                cur = parse_temp(node.get("Value"))
                mn = parse_temp(node.get("Min"))
                mx = parse_temp(node.get("Max"))

                if cur is not None:
                    matches.append({
                        "current": cur,
                        "min": mn if mn is not None else cur,
                        "max": mx if mx is not None else cur,
                        "text": node.get("Text", "")
                    })

            for v in node.values():
                walk(v, current_text)

        elif isinstance(node, list):
            for item in node:
                walk(item, parent_text)

    walk(data)

    if not matches:
        return {"current": -1, "min": -1, "max": -1}

    # 取最高当前温度作为 CPU 当前温度，适合监控/告警
    current = max(x["current"] for x in matches)
    min_val = min(x["min"] for x in matches if x["min"] is not None)
    max_val = max(x["max"] for x in matches if x["max"] is not None)

    return {"current": round(current, 2), "min": round(min_val, 2), "max": round(max_val, 2)}


if __name__ == "__main__":
    print(get_cpu_temperature())