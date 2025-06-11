from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from model_factory import create_model_client
import asyncio
from agents.article_research.survey_director import get_survey_director
from agents.article_research.paper_retriver import get_paper_retriever
from agents.article_research.paper_summarizer import get_paper_summarizer
from agents.article_research.survey_analyst import get_survey_analyst
from autogen_core.tools import FunctionTool
from tools.search_tool import search_arxiv
from tools.search_tool import get_arxiv_tool

## use console pattern
async def chat():
    # Create the agents.
    arxiv_tool = get_arxiv_tool()
    # arxiv_tool = FunctionTool(
    #     func=search_arxiv,
    #     description=(
    #         "Search for papers on arXiv. Parameters:\n"
    #         "- query: Search keywords (required)\n"
    #     ),
    #     strict=False
    # )
    model_client = create_model_client("default_model")
    assistant = AssistantAgent("assistant", model_client=model_client,tools=[arxiv_tool],reflect_on_tool_use=True,model_client_stream=False)
    #assistant = get_paper_retriever(model_client)
    user_proxy = UserProxyAgent("user_proxy", input_func=input)  # Use input() to get user input from console.

    # Create the termination condition which will end the conversation when the user says "APPROVE".
    termination = TextMentionTermination("APPROVE")

    survey_director=get_survey_director()
    paper_retriever=get_paper_retriever()
    paper_summarizer=get_paper_summarizer()
    survey_analyst=get_survey_analyst()

    #Create team
    team = RoundRobinGroupChat(
        [survey_director, paper_retriever, paper_summarizer, survey_analyst, user_proxy],
        termination_condition=termination
    )


    # Run the conversation and stream to the console.
    # stream = team.run_stream(task="Write a 4-line poem about the ocean.")
    stream = team.run_stream(task="New study about machine learning.")
    # Use asyncio.run(...) when running in a script.
    await Console(stream)
    await model_client.close()

if __name__ == "__main__":
    asyncio.run(chat())