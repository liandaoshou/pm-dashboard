#!/usr/bin/env python3
"""用 gh CLI 刷新 data.json 中所有带 repo 链接项目的仓库字段（描述、最近提交、待办=open issues、open PR）。
用法：python3 update_data.py   （需已 gh auth login）。手工字段（阶段、进度、里程碑、风险等）不会被改动。"""
import json, subprocess, base64, re, datetime, pathlib
P = pathlib.Path(__file__).with_name("data.json")
def gh(*a): return json.loads(subprocess.check_output(["gh", *a]))
def readme_desc(r):
    try: t = base64.b64decode(gh("api", f"repos/{r}/readme")["content"]).decode()
    except Exception: return ""
    for para in re.split(r"\n\s*\n", t):
        p = para.strip()
        if p and not p.startswith(("#", "|", "```", "!", "<")): return p
    return ""
d = json.loads(P.read_text("utf-8"))
for p in d["projects"]:
    m = re.match(r"https://github.com/([^/]+/[^/#?]+)", p.get("repo") or "")
    if not m: continue
    r = m.group(1)
    info = gh("repo", "view", r, "--json", "description")
    p["description"] = info.get("description") or readme_desc(r) or p.get("description", "")
    c = gh("api", f"repos/{r}/commits?per_page=1")[0]
    p["lastCommit"] = {"date": c["commit"]["committer"]["date"], "message": c["commit"]["message"].split("\n")[0], "url": c["html_url"]}
    p["todos"] = [f"#{i['number']} {i['title']}" for i in gh("issue", "list", "-R", r, "--state", "open", "--json", "number,title")]
    p["openPRs"] = [{"number": x["number"], "title": x["title"], "url": x["url"]} for x in gh("pr", "list", "-R", r, "--json", "number,title,url")]
d["updatedAt"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
P.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", "utf-8")
print("updated", P)
