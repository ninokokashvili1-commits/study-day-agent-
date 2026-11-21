from typing import Annotated
from typing_extensions import TypedDict
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt

def build_graph():
    tasks = []

    @tool
    def add_task(task: str) -> str:
        """Adds a new study task to the task list."""
        tasks.append(task)
        return f"დავალება დამატებულია: '{task}'"

    @tool
    def list_tasks() -> str:
        """Lists all current study tasks."""
        if not tasks:
            return "დავალებების სია ცარიელია."
        return "დავალებები:\n" + "\n".join(f"- {t}" for t in tasks)

    @tool
    def delete_task(task: str) -> str:
        """Deletes a task from the list after user confirmation."""
        if task not in tasks:
            return f"დავალება '{task}' სიაში არ არის."
        decision = interrupt(f"ნამდვილად გსურთ წაშალოთ დავალება: '{task}'?")
        if decision:
            tasks.remove(task)
            return f"დავალება '{task}' წაიშალა."
        return f"წაშლა გაუქმდა. '{task}' ისევ სიაშია."

    @tool
    def get_tbilisi_weather() -> dict:
        """Get current temperature in Tbilisi, in Celsius."""
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": 41.72, "longitude": 44.79, "current": "temperature_2m"},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["current"]

    @tool
    def search_books(topic: str) -> str:
        """Search for books on a given topic using Open Library API."""
        r = requests.get(
            "https://openlibrary.org/search.json",
            params={"q": topic, "limit": 3},
            timeout=20,
        )
        r.raise_for_status()
        docs = r.json().get("docs", [])
        if not docs:
            return "წიგნები ვერ მოიძებნა."
        return "\n".join(f"{d.get('title')} - {', '.join(d.get('author_name', ['უცნობი']))}" for d in docs)

    tools = [add_task, list_tasks, delete_task, get_tbilisi_weather, search_books]

    class State(TypedDict):
        messages: Annotated[list, add_messages]

    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0).bind_tools(tools)
    sys_msg = SystemMessage(content="შენ ხარ Study Day Assistant. უპასუხე ქართულად, მოკლედ და გასაგებად.")

    def assistant(state: State):
        return {"messages": [llm.invoke([sys_msg] + state["messages"])]}

    builder = StateGraph(State)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")

    return builder.compile(checkpointer=InMemorySaver())
