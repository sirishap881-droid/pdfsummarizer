"""Phase 0: validate required API keys and GitHub login."""

import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

results = []


def check_gemini_key() -> bool:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        results.append(("GEMINI_API_KEY", "MISSING"))
        return False
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    results.append(("GEMINI_API_KEY", f"set (len={len(key)}, model={model})"))
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(model=model, google_api_key=key, temperature=0.3)
        reply = llm.invoke("Say OK in one word.").text
        results.append(("Gemini live call", f"OK -> {reply.strip()[:30]}"))
        return True
    except Exception as e:  # noqa: BLE001
        results.append(("Gemini live call", f"FAILED: {type(e).__name__}: {e}"))
        return False


def check_gh_login() -> bool:
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, timeout=30
        )
        output = proc.stdout + proc.stderr
        logged_in = proc.returncode == 0 and "Logged in to github.com" in output
        account = ""
        for line in output.splitlines():
            if "Logged in to" in line:
                account = line.strip()
        results.append(
            ("GitHub login", f"OK ({account})" if logged_in else "NOT LOGGED IN")
        )
        return logged_in
    except Exception as e:  # noqa: BLE001
        results.append(("GitHub login", f"FAILED: {e}"))
        return False


if __name__ == "__main__":
    ok_gem = check_gemini_key()
    ok_gh = check_gh_login()
    for name, status in results:
        print(f"{name}: {status}")
    sys.exit(0 if (ok_gem and ok_gh) else 1)
