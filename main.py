from typing import Dict, List
from autogen import ConversableAgent
import sys
import os


def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # TODO
    # This function takes in a restaurant name and returns the reviews for that restaurant.
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call.
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}

    with open("restaurant-data.txt", "r") as f:
        out = f.readlines()
    dset = {}
    for line in out:
        resto, review = line.split(".")[0], ".".join(line.split(".")[1:]).rstrip("\n")
        if resto.lower() not in dset.keys():
            dset[resto.lower()] = []
        dset[resto.lower()].append(review)

    return dset[restaurant_name.lower()]


def calculate_overall_score(
    restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]
) -> Dict[str, float]:
    # TODO
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service.
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have
    # at least 3 decimal places.
    pass


def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    # TODO
    # It may help to organize messages/prompts within a function which returns a string.
    # For example, you could use this function to return a prompt for the data fetch agent
    # to use to fetch reviews for a specific restaurant.
    prompt = f"""
    You are a helpful AI Assistant
    Your job is to identify the restaurant mentioned in the input query 
    Input Query: {restaurant_query}
    Output "END" if valid restaurant reviews are found
    """
    return prompt

def get_review_analyzer_agent_prompt() -> str:
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
    

    """
    return review_analyzer_agent_prompt


# TODO: feel free to write as many additional functions as you'd like.


def check_message_content(msg):
    if msg["content"] is not None:
        return "END" in msg["content"]
    else:
        return None


def review_summary_method(
    sender: ConversableAgent,
    recipient: ConversableAgent,
    messages: List[Dict[str, str]]
) -> str:
    """
    Custom summary method for review analysis conversation.
    
    Args:
        sender: The agent sending the message
        recipient: The agent receiving the message
        messages: List of all messages in the conversation
    
    Returns:
        str: The relevant summary of the conversation
    """
    
    reviews = sender.chat_messages_for_summary(recipient)[-2]['content']
    reviews = reviews.strip('[]')
    reviews = reviews.split('",')
    reviews = [f'Review {i+1}: '+review.strip(' "') for i,review in enumerate(reviews)]
    print('Number of reviews: ', len(reviews))
    #print('Number of reviews: ', len(reviews.split('\n')))
    
    return reviews


# Do not modify the signature of the "main" function.
def main(user_query: str):
    entrypoint_agent_system_message = """
    Your task is to initiate a conversation with the data fetch agent 
    to identify the restaurant mentioned in the input query and fetch the 
    reviews for that restaurant by executing the fetch_restaurant_data function. 
    On successful execution of the fetch_restaurant_data function, initiate a 
    conversation with the review analyzer agent to analyze the reviews for the 
    identified restaurant. Output "END" if valid scores for the reviews are returned 

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
        is_termination_msg=lambda msg: check_message_content(msg)
        
    )
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(
        fetch_restaurant_data
    )

    # TODO
    # Create more agents here.
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
        is_termination_msg=lambda msg: check_message_content(msg)
    )



    # result = entrypoint_agent.initiate_chat(
    #     recipient=data_fetch_agent, message=user_query
    # )

    results = entrypoint_agent.initiate_chats(
        [
            {
                "recipient": data_fetch_agent,
                "message": user_query,
                "summary_method": review_summary_method,
               
            },
            {
                "recipient": review_analyzer_agent,
                "message": 'This is the list of reviews for analysis',
                "max_turns": 2
            }

        ]
    )
    return results
    

# DO NOT modify this code below.
if __name__ == "__main__":
    assert (
        len(sys.argv) > 1
    ), "Please ensure you include a query for some restaurant when executing main."
    out = main(sys.argv[1])
    food_scores,service_scores = out[-1].chat_history[-2]['content'].split('\n')
    food_scores = food_scores.strip('[]')
    service_scores = service_scores.strip('[]')
    food_scores_ls = [(int)(x.split(':')[-1]) if x.split(':')[-1].strip().isdigit() else x.split(':')[-1].strip() for x in food_scores.split(',')]
    service_scores_ls = [(int)(x.split(':')[-1]) if x.split(':')[-1].strip().isdigit() else x.split(':')[-1].strip() for x in service_scores.split(',')]
    