from agents.orchestrator import OrchestratorAgent


if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    query = "I'm leaving from Chicago. Give me today's weather and UV, quick news, commute advice, and a 10-minute breakfast idea with eggs."
    print(orchestrator.run(query))
