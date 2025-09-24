from crewai import Agent, LLM, Task, Crew, Process
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Initialize the Gemini LLM using CrewAI's LLM wrapper
my_llm = LLM(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini/gemini-1.5-flash",
    temperature=0.5,
    verbose=True
)

# Also initialize the ChatGoogleGenerativeAI (though note that my_llm is used in agents)
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    verbose=True,
    temperature=0.5,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Initialize a tool
tool = SerperDevTool()

# Define agents
news_researcher = Agent(
    role="Senior Researcher",
    goal="Uncover ground breaking tech in {topic}",
    verbose=True,
    memory=True,
    backstory=(
        "Driven by curiosity, you're at the forefront of innovation, eager to explore and share the knowledge with the world."
    ),
    tools=[tool],
    llm=my_llm,
    allow_delegation=True
)

news_writer = Agent(
    role="Writer",
    goal="Narrate compelling tech stories about {topic}",
    verbose=True,
    memory=True,
    backstory=(
        "With a flair for simplifying complex topics, you craft engaging narratives that captivate and educate, bringing new discoveries to light."
    ),
    tools=[tool],
    llm=my_llm,
    allow_delegation=False
)

# Define tasks
researcher_task = Task(
    description=(
        "Identify the next big trend in {topic}."
        "Focus on identifying pros and cons and the overall narrative."
        "Your final report should clearly articulate the key points, its market opportunities and potential risks."
    ),
    expected_output='A comprehensive 3 paragraphs long report on the latest AI trends',
    tools=[tool],
    agent=news_researcher
)

writer_task = Task(
    description=(
        "Compose an insightful article on {topic}."
        "Focus on the latest trends and how it's impacting the industry."
        "This article should be easy to understand, engaging, and positive."
        "Provide compelling examples and statistics to keep the reader interested."
    ),
    expected_output='A 4 paragraph article on {topic} advancements formatted as markdown.',
    tools=[tool],
    agent=news_writer,
    async_execution=False,
    output_file='new-blog-post.md'
)

# Create and run the crew
crew = Crew(
    agents=[news_researcher, news_writer],
    tasks=[researcher_task, writer_task],
    process=Process.sequential,
)

result = crew.kickoff(inputs={'topic': 'AI in automotive'})
print(result)