from orchestrator import orchestrate

if __name__ == "__main__":
    out = orchestrate("Latest trends in speech LLMs")
    print("\nINSIGHTS:\n")
    print(out["insights"])

