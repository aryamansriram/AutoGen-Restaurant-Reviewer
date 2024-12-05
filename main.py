from typing import Dict, List
from autogen import ConversableAgent
import sys
import os


def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    """
    Fetches reviews for a given restaurant from a text file.

    Args:
        restaurant_name (str): The name of the restaurant to fetch reviews for.

    Returns:
        Dict[str, List[str]]: A dictionary with the restaurant name as key and a list of reviews as value.

    Example:
        >>> fetch_restaurant_data("Applebee's")
        {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    """

    with open("restaurant-data.txt", "r") as f:
        out = f.readlines()
    dset = {}
    for line in out:
        resto, review = line.split(".")[0], ".".join(line.split(".")[1:]).rstrip("\n")
        if resto.lower() not in dset.keys():
            dset[resto.lower()] = []
        dset[resto.lower()].append(review)

    return {restaurant_name.lower(): dset[restaurant_name.lower()]}


def calculate_overall_score(
    restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]
) -> Dict[str, float]:
    """
    Calculates an overall score for a restaurant based on food and customer service ratings.

    Args:
        restaurant_name (str): Name of the restaurant.
        food_scores (List[int]): List of food quality scores (1-5).
        customer_service_scores (List[int]): List of customer service scores (1-5).

    Returns:
        Dict[str, float]: Dictionary with restaurant name as key and computed score as value.
                         Score is between 0-10 with at least 3 decimal places.

    Example:
        >>> calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        {"Applebee's": 5.048}
    """
    score = 0
    N = len(food_scores)
    for i in range(N):
        score += (food_scores[i] ** 2 * customer_service_scores[i]) ** 0.5
    score = (score / (N * 125**0.5)) * 10
    return {restaurant_name: f"{score:.3f}"}


def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    """
    Generates a prompt for the data fetch agent to identify and fetch restaurant reviews.

    Args:
        restaurant_query (str): The user's query containing a restaurant name.

    Returns:
        str: A formatted prompt string for the data fetch agent.
    """
    prompt = f"""
    You are a helpful AI Assistant
    Your job is to identify the restaurant mentioned in the input query 
    Input Query: {restaurant_query}
    Output "END" if valid restaurant reviews are found
    """
    return prompt


def get_review_analyzer_agent_prompt() -> str:
    """
    Generates a prompt for the review analyzer agent with scoring guidelines.

    Returns:
        str: A detailed prompt containing instructions for analyzing restaurant reviews
             and assigning food quality and customer service scores.
    """
    review_analyzer_agent_prompt = """
    You are an expert review analyzer specializing in restaurant reviews. Your task is to carefully analyze restaurant reviews and extract numerical scores for both food quality and customer service.
    You will be provided with a list of reviews for a specific restaurant.
    
    
    For each review, you should assign two separate scores on a scale of 1-5:
    - Food Quality Score (1-5)
    - Customer Service Score (1-5)

    Here is how you should assign these scores:
    - If the food quality is described as "awful", "horrible", or "disgusting", assign a food quality score of 1.
    - If the customer service is described as "awful", "horrible", or "disgusting", assign a customer service score of 1.
    - If the food quality is described as "bad", "unpleasant", or "offensive", assign a food quality score of 2.
    - If the customer service is described as "bad", "unpleasant", or "offensive", assign a customer service score of 2.
    - If the food quality is described as "average", "uninspiring", or "forgettable", assign a food quality score of 3.
    - If the customer service is described as "average", "uninspiring", or "forgettable", assign a customer service score of 3.
    - If the food quality is described as "good", "enjoyable", or "satisfying", assign a food quality score of 4.
    - If the customer service is described as "good", "enjoyable", or "satisfying", assign a customer service score of 4.
    - If the food quality is described as "awesome", "incredible", or "amazing", assign a food quality score of 5.

    Your output format should be that of two lists:
    
    food_scores: [Review 1: Review 1 food score, Review 2: Review 2 food score, ...]
    service_scores: [Review 1: Review 1 customer service score, Review 2: Review 2 customer service score, ...]
    
    REMEMBER: Number of reviews should be equal to number of food_scores and number of service_scores
    Output "END" on successful completion of task

    """
    return review_analyzer_agent_prompt


def check_message_content(msg):
    """
    Checks if a message contains the termination signal "END".

    Args:
        msg (Dict): Message dictionary containing content.

    Returns:
        bool or None: True if "END" is in content, None if content is None.
    """
    if msg["content"] is not None:
        return "END" in msg["content"]
    else:
        return None


def review_summary_method(
    sender: ConversableAgent,
    recipient: ConversableAgent,
    messages: List[Dict[str, str]],
) -> str:
    """
    Custom summary method for review analysis conversation.

    Args:
        sender (ConversableAgent): The agent sending the message.
        recipient (ConversableAgent): The agent receiving the message.
        messages (List[Dict[str, str]]): List of all messages in the conversation.

    Returns:
        List[str]: List of formatted review strings.
    """

    reviews = sender.chat_messages_for_summary(recipient)[-2]["content"]
    reviews = reviews.strip("[]")
    reviews = reviews.split('",')
    reviews = [
        f"Review {i+1}: " + review.strip(' "') for i, review in enumerate(reviews)
    ]
    print("Number of reviews: ", len(reviews))
    # print('Number of reviews: ', len(reviews.split('\n')))

    return reviews


def get_scores_summary_method_prompt():
    """
    Generates a prompt for summarizing restaurant scores from a conversation.

    Returns:
        str: A prompt template requesting restaurant name, food scores,
             and customer service scores in a specific format.
    """
    prompt = """
    Given a conversation between two agents previously, return the following details as output:
    - Restaurant name: The name of the restaurant whose reviews are being analyzed
    - Food scores: The food quality scores assigned for each review
    - Customer service scores: The customer service scores assigned for each review

    Format the output as follows:
    Restaurant name: <restaurant_name>
    Food scores: [Review 1: Review 1 food score, Review 2: Review 2 food score, ...]
    Customer service scores: [Review 1: Review 1 customer service score, Review 2: Review 2 customer service score, ...]
    
    Do not fetch any other information from the conversation.
    """
    return prompt


def get_scorer_prompt():
    """
    Generates a prompt for the scoring agent to calculate overall restaurant scores.

    Returns:
        str: A prompt template for processing restaurant scores and preparing
             arguments for the calculate_overall_score function.
    """
    prompt = """
    Given the following details:
    - Restaurant name: The name of the restaurant whose reviews are being analyzed
    - Food scores: The food quality scores assigned for each review
    - Customer service scores: The customer service scores assigned for each review

    Return the appropriate arguments for the calculate_overall_score function.
    Output "END" on successful completion of task
    """
    return prompt


# Do not modify the signature of the "main" function.
def main(user_query: str):
    """
    Main function to process a user's restaurant query through a multi-agent system.

    Args:
        user_query (str): User's input query about a restaurant.

    The function orchestrates multiple agents to:
    1. Fetch restaurant data
    2. Analyze reviews
    3. Calculate overall scores
    """
    entrypoint_agent_system_message = """
    Your task is to initiate a conversation with the data fetch agent 
    to identify the restaurant mentioned in the input query and fetch the 
    reviews for that restaurant by executing the fetch_restaurant_data function. 
    On successful execution of the fetch_restaurant_data function, initiate a 
    conversation with the review analyzer agent to analyze the reviews for the 
    identified restaurant. 
    Finally, initiate a conversation with the scoring agent to calculate the 
    overall score for the identified restaurant.
    
    """
    # example LLM config for the entrypoint agent
    llm_config = {
        "config_list": [
            {"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}
        ]
    }
    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent(
        "entrypoint_agent",
        system_message=entrypoint_agent_system_message,
        llm_config=llm_config,
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: check_message_content(msg),
    )
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(
        fetch_restaurant_data
    )
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(
        calculate_overall_score
    )

    data_fetch_agent = ConversableAgent(
        "data_fetch_agent",
        system_message=get_data_fetch_agent_prompt(user_query),
        human_input_mode="NEVER",
        llm_config=llm_config,
    )
    data_fetch_agent.register_for_llm(
        name="fetch_restaurant_data",
        description="fetches required restaurant data for the input query",
    )(fetch_restaurant_data)

    review_analyzer_agent = ConversableAgent(
        "review_analyzer_agent",
        system_message=get_review_analyzer_agent_prompt(),
        human_input_mode="NEVER",
        llm_config=llm_config,
    )

    scoring_agent = ConversableAgent(
        "scoring_agent",
        system_message=get_scorer_prompt(),
        human_input_mode="NEVER",
        llm_config=llm_config,
    )

    scoring_agent.register_for_llm(
        name="calculate_overall_score",
        description="calculates overall score given the food and customer service scores for a given restaurant",
    )(calculate_overall_score)

    results = entrypoint_agent.initiate_chats(
        [
            {
                "recipient": data_fetch_agent,
                "message": user_query,
                "summary_method": review_summary_method,
            },
            {
                "recipient": review_analyzer_agent,
                "message": "This is the list of reviews for analysis",
            },
            {
                "recipient": scoring_agent,
                "message": "These are the scores and restaurant name required for score calculation",
                "summary_method": "reflection_with_llm",
                "summary_args": {"summary_prompt": get_scores_summary_method_prompt()},
            },
        ]
    )
    return results


# DO NOT modify this code below.
if __name__ == "__main__":
    assert (
        len(sys.argv) > 1
    ), "Please ensure you include a query for some restaurant when executing main."
    out = main(sys.argv[1])
