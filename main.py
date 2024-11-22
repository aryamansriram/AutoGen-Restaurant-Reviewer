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
   
    with open('restaurant-data.txt','r') as f:
        out = f.readlines()
    dset = {}
    for line in out:
        resto,review = line.split('.')[0],'.'.join(line.split('.')[1:]).rstrip('\n')
        if resto.lower() not in dset.keys():
            dset[resto.lower()] = []
        dset[resto.lower()].append(review)
    
    return dset[restaurant_name.lower()]


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
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
    prompt = f'''
    You are a helpful AI Assistant
    Your job is to identify the restaurant mentioned in the input query 
    Input Query: {restaurant_query}
    Output END if the restaurant is successfully found
    '''
    return prompt

# TODO: feel free to write as many additional functions as you'd like.

def check_message_content(msg):
    if msg['content'] is not None:
        
        return 'END' in msg['content']
    else:
        return None


# Do not modify the signature of the "main" function.
def main(user_query: str):
    entrypoint_agent_system_message = '''
    You are a helpful AI assistant, your job is to send the input query
    to the other agents to fetch required tool arguments and execute 
    the registered tools with the tool arguments to get the final answer
    ''' 
    # example LLM config for the entrypoint agent
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent("entrypoint_agent", 
                                        system_message=entrypoint_agent_system_message, 
                                        llm_config=llm_config,
                                        human_input_mode='NEVER',
                                        is_termination_msg=lambda msg: check_message_content(msg)
                                        )
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    # TODO
    # Create more agents here. 
    data_fetch_agent = ConversableAgent(
        "data_fetch_agent",
        system_message=get_data_fetch_agent_prompt(user_query),
        human_input_mode='NEVER',
        llm_config=llm_config,
        
    )
    data_fetch_agent.register_for_llm(name='fetch_restaurant_data',description='fetches required restaurant data for the input query')(fetch_restaurant_data)
    
    
    result = entrypoint_agent.initiate_chat(recipient=data_fetch_agent,message=user_query)
    print(result)
    
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    out = main(sys.argv[1])
    