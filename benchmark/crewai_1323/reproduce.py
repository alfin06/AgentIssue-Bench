import os
import sys
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv

def main():
    load_dotenv()
    os.environ["OTEL_SDK_DISABLED"] = "true"

    researcher = Agent(
        role='Senior Research Analyst',
        goal='Uncover cutting-edge developments in AI and data science',
        backstory="""You work at a leading tech think tank.
        Your expertise lies in identifying emerging trends.
        You have a knack for dissecting complex data and presenting actionable insights.""",
        verbose=True,
        allow_delegation=False,
    )

    writer = Agent(
        role='Tech Content Strategist',
        goal='Craft compelling content on tech advancements',
        backstory="""You are a renowned Content Strategist, known for your insightful and engaging articles.
        You transform complex concepts into compelling narratives.""",
        verbose=True,
        allow_delegation=True,
    )

    task1 = Task(
        description="""Conduct a comprehensive analysis of the latest advancements in AI in 2024.
        Identify key trends, breakthrough technologies, and potential industry impacts.""",
        expected_output="Full analysis report in bullet points",
        agent=researcher
    )

    task2 = Task(
        description="""Using the insights provided, develop an engaging blog
        post that highlights the most significant AI advancements.
        Your post should be informative yet accessible, catering to a tech-savvy audience.
        Make it sound cool, avoid complex words so it doesn't sound like AI.""",
        expected_output="Full blog post of at least 4 paragraphs",
        agent=writer
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        verbose=True,
        process=Process.sequential
    )

    try:
        result = crew.kickoff()
        print("######################")
        print(result)
        print("Model used:", os.environ.get("OPENAI_MODEL_NAME", "not set"))
        print("✅ Model can be used.")
        sys.exit(0)

    except Exception as e:
        if "Unsupported parameter" in str(e) and "'stop'" in str(e):
            print("❌ BUG REPRODUCED: 'stop' parameter not supported error found.")
            print("Full error:", e)
            sys.exit(1)
        else:
            print("⚠️ Unexpected error:", e)
            sys.exit(2)

if __name__ == "__main__":
    main()
