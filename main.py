import os
import getpass
from langgraph.types import Command
from agent import build_graph

if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("შეიყვანეთ GROQ_API_KEY: ")

graph = build_graph()
config = {"configurable": {"thread_id": "cli-session-1"}}

print("Study Day Assistant მზადაა! გამოსასვლელად აკრიფეთ 'exit'.\n")

while True:
    user_input = input("თქვენ: ")
    if user_input.strip().lower() == "exit":
        break

    res = graph.invoke({"messages": [("user", user_input)]}, config)
    state = graph.get_state(config)

    if state.tasks and state.tasks[0].interrupts:
        question = state.tasks[0].interrupts[0].value
        ans = input(f"⚠️ {question} (yes/no): ").strip().lower()
        res = graph.invoke(Command(resume=(ans in ["yes", "y", "კი"])), config)

    print(f"აგენტი: {res['messages'][-1].content}\n")
