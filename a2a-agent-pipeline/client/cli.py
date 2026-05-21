"""
CLI client — talks to the orchestrator and prints the full transcript.
"""
import sys
import httpx

ORCHESTRATOR_URL = "http://localhost:8000"


def main() -> None:
    print("=" * 60)
    print("A2A Grok Demo — Client")
    print("=" * 60)
    print("Talks to the orchestrator at", ORCHESTRATOR_URL)
    print("Type a goal and press Enter. Empty line or 'quit' to exit.")
    print()

    # Show discovered agents up front
    try:
        info = httpx.get(f"{ORCHESTRATOR_URL}/", timeout=5).json()
        print("Discovered agents:")
        for name, meta in info.get("discovered_agents", {}).items():
            print(f"  - {name} ({meta['url']}) skills={meta['skills']}")
        print()
    except Exception as e:
        print(f"[warn] could not reach orchestrator: {e}")
        print("Make sure orchestrator.py is running.")
        sys.exit(1)

    while True:
        try:
            goal = input("goal> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not goal or goal.lower() in {"quit", "exit"}:
            break

        try:
            with httpx.Client(timeout=300) as c:
                r = c.post(f"{ORCHESTRATOR_URL}/run", json={"goal": goal})
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            print(f"[error] {e}")
            continue

        print()
        print("─" * 60)
        print("PLAN")
        print("─" * 60)
        for i, step in enumerate(data["plan"], 1):
            print(f"{i}. {step['agent']}")
            print(f"   input: {step['input'][:200]}"
                  + ("..." if len(step['input']) > 200 else ""))
        print()

        for entry in data["transcript"]:
            print("─" * 60)
            print(f"STEP {entry['step']} — {entry['agent']}")
            print("─" * 60)
            print(entry["output"])
            print()

        print("=" * 60)
        print("FINAL OUTPUT")
        print("=" * 60)
        print(data["final_output"])
        print()


if __name__ == "__main__":
    main()
