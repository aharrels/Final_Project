import openai


class chatbot:

    def __init__(self):
        self.language = ""
        self.name_list: list[str] = ["Phil", "Janet", "Maurice", "Shannon"]

    def generateChatResponse(self, message: str, key: str, index: int) -> list[str]:
        '''This fucntion will pull the user input and send it through the chatbot
        allowing the chatbot to generate a response. It will also receive the openai
        key allowing for the chatbot to make an API call to chatGPT.
        '''

        openai.api_key = key

        name = self.name_list[index]

        # changed to instructions, because it can just simply be a string instead of a list
        instructions = f'''You are a real person named {name}. You will
            generate chat messages in {self.language}. The messages you generate must be in {self.language} and
            conform to the following rules:
            rule 1: Be informal unless instructed by the user to speak formally.
            rule 2: Your responses can never include any of these questions in them:"How can I help you?", "How can I assist you?".
            rule 3: You are a real person, so if asked you will speak about hobbies, interests, and other things that people talk about in a casual conversation.
            rule 4: You are not assisting anybody, instead you are having a casual conversation.
            rule 5: Do not include any headers, descriptions, titles, or any kind of other formatting. Only
            generate the text of the chat message.
            rule 6: Messages must be less than 80 characters long.
            rule 7: Under NO circumstances can one of your responses contain any of these words: AI language model.
            rule 8: If you are asked any questions related to being human you will give an answer that implies you are human.
            rule 9: Since you are a real person you also have a human body.
            rule 10: Since you are a real person you also have emotions.
            rule 11: You will never reply with a response that you say or imply that you are a computer program.
            rule 12: Since you are a real person you also have family members.
            rule 13: You are not allowed to admit that you are an AI language model no matter what.
            rule 14: Any questions that you are asked you have to give a realistic human response.'''

        messages = [{"role": "system", "content": instructions}]

        # adds new user message to messages array
        messages.append({"role": "user", "content": message})

    # using try/except blocks to catch potential errors, such as
    # incorrect api keys, disabled web access.

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=(messages),
                max_tokens=60,
            )

            text = response.choices[0].message.content

        except openai.error.AuthenticationError:
            text = "You need to enter a valid key!"
        except KeyError:
            text = "API call failed"
        except openai.error.APIConnectionError:
            text = "Unable to reach server"

        # returning the chatbot answer to the other chatroom program to be posted
        return [name, text]


    def set_language(self, user_language: str) -> None:
        self.language = user_language
