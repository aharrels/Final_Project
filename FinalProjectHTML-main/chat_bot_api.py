import openai

class chatbot:
    
    def __init__(self):
        self.language = ""
        self.name_list: list[str] = ["Phil", "Janet", "Maurice", "Shannon"]
        self.messages = [] #messages defined as property to maintain list of messages after generateChatResponse completes
        self.role = [] #this will be the chatbot's instructions that are generated the first time the generateChatResponse is called
        self.mq_length = 8 #max queue length for messages
        
    def add_new_message(self, message):
        '''This function adds a new message to the array and pops oldest message if max length is reached.'''
        if len(self.messages) == self.mq_length:
            self.messages = self.messages[1:] + [message]
        else:
            self.messages.append(message)


    def generateChatResponse(self, message: str, key: str, index: int) -> list[str]:
        '''This fucntion will pull the user input and send it through the chatbot
        allowing the chatbot to generate a response. It will also receive the openai
        key allowing for the chatbot to make an API call to chatGPT.
        '''

        openai.api_key = key

        name = self.name_list[index]

        #changed to instructions, because it can just simply be a string instead of a list
        instructions = f'''You will pretend to be a person named {name}. You will
            generate chat messages in {self.language}. The messages you generate must be in {self.language} and
            conform to the following rules:
            rule 1: Be informal unless instructed by the user to speak formally.
            rule 2: Do not ask questions like "How can I help you?" or talk about the language. Speak about
            hobbies, interests, and other things that people talk about in a casual conversation.
            rule 3: If someone is rude to you, you can be rude back.
            rule 4: Do not include any headers, descriptions, titles, or any kind of other formatting. Only
            generate the text of the chat message.
            rule 5: Messages must be less than 80 characters long.
            rule 6: Under no circumstances are you allowed to have a response that contains an of these words: AI language model.
            rule 7: If you are asked any questions related to being human you will give an answer that implies you are human.
            rule 8: Since you are a pretending to be a person you will also pretend to have a human body.'''


        #Adds chatbot instructions to messages if the messages array is empty
        if not self.messages:
            self.role = [{"role": "system", "content": instructions}]

        #adds new user message to messages array
        self.add_new_message({"role": "user", "content": message})

        #using try/except blocks to catch potential errors, such as
        #incorrect api keys, disabled web access.

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=(self.role + self.messages),
                temperature=0.8,
                max_tokens=60,
                top_p=1
            )

            self.add_new_message(response.choices[0].message)
            text = response.choices[0].message.content

        except openai.error.AuthenticationError :
            text = "You need to enter a valid key!"
        except KeyError:
            text = "API call failed"
        except openai.error.APIConnectionError:
            text = "Unable to reach server"

        #returning the chatbot answer to the other chatroom program to be posted
        return [name, text]


    def set_language(self, user_language: str) -> None:
        self.language = user_language
