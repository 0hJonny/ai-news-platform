# Download the model before using.
# Check ollama/start.sh


import re
from .GenerationModel import GenerationModel
from .GenerationResponse import GenerationResponse
from models import ArticleAnnotation

class Mistral(GenerationModel):
    def __init__(self):
        super().__init__()
        self.model_name = "mistral"
        self.data = {
            "stream": False,  # Placeholder for stream option
            "options": {
                "temperature": 0.1,  # Placeholder for temperature option
                # "repeat_penalty": 1.05  # Placeholder for repeat_penalty option
            }
        }
    

    def annotate(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        prompt = """
            Article title: {%s}
            Article content: {%s}

            Use my Markdown Formatting template.

            Template:

            ### Main Facts and Events:
            - [List the main facts and events mentioned in the article here]

            ### Key Ideas:
            - [Summarize the key ideas or arguments presented in the article]

            ### Further Interest:
            - [Highlight any information that may spark further interest or requires special attention]

            ### Important Keywords:
            - *Keywords*: [List any important keywords mentioned in the article here]

            ### Highlighted Text:
            - [Insert any highlighted text or quotes from the article here]
            """
        prompt = prompt % (article.title, article.body)

        answer: GenerationResponse = self._generate_text(prompt=prompt, stream=stream, options=options)

        article.annotation = answer.message["content"]
        article.add_neural_network("annotator", self.model_name)
        
        return article

    def trim_text(self, text):
        # Use a regular expression to find the first word and the colon after it
        match = re.search(r'^\s*\w+\s*:', text)
        if match:
            # If a colon is found after the first word, trim the string up to it and strip extra whitespace
            trimmed_text = text[match.end():].strip()
            return trimmed_text
        else:
            # If no colon is found, or it's not after the first word, return the original string
            return text.strip()
        
    def translate(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        prompt = """
            Translate my text: "%s", to %s language. Safe the structure.
            Use template to asnwer.
            Answer template:
            ```
            Translated text:
            [Title: traslate here]
            ```
            """
        prompt = prompt % (article.title, article.language_to_answer_name)

        answer = self._generate_text(prompt=prompt, stream=stream, options=options)

        answer = answer.message["content"]

        print("'%s'" % answer)
        # Parse answer
        answer.replace('```', '')
        match = re.search(r'\[?Title: (.+?)(?:\]|$)', answer)
        if match:
            article.title = match.group(1).strip().replace('"', '')
        else:
            match = re.search(r'(?<=Translated text:\s)(.+)', answer)
            if match:
                article.title = self.trim_text(match.group(1).strip().replace('"', ''))

        print(article.title)


        prompt = """
            Translate article annotation to %s language. Safe the structure. 
            Article annotation: 
            '''
            %s
            '''
            """
            
        if article.annotation is None:
            raise Exception("Annotation is None. Write annotation before translating.")

        prompt = prompt % (article.language_to_answer_name, article.annotation)

        answer = self._generate_text(prompt=prompt, stream=stream, options=options)


        answer = answer.message["content"]
        answer = answer.replace('```', '')

        index = answer.find('###')
        
        if index == None:
            return article

        if index != -1:
            answer = answer[index:]
        article.annotation = answer

        article.add_neural_network("translator", self.model_name)
        
        return article
        
    def categorize(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        prompt = """
            Article:
            '''
            Title: %s
            Content: %s
            '''
            Classify the article to one of the topics: 
            "technology", 
            "crypto", 
            "privacy", 
            "security".
            Use template to asnwer:
            Answer template: "Topic: topic 1"
            """
        prompt = prompt % (article.title, article.body)
        
        answer = self._generate_text(prompt=prompt, stream=stream, options=options)

        words = ["technology", "crypto", "privacy", "security"]

        answer = answer.message["content"].lower()
        print(answer)

        # Check if any of the words are present in the string
        for word in words:
            if word in answer:
                article.theme_name = word
                break
        else:
            article.theme_name = None

        return article
        
    def extract_tags(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        prompt = """
            Article:
            '''
            Title: %s
            Content: %s
            '''
            What is tags of the Article? Tag is representing the main points of the article. 
            Tags should be concise, reflecting one or two words of the main points of the article.
            Answer in format: [tag1, tag2,... tags] like array of tags. 
            Example: Tags must has one or two words of main points of the Article.
            """
        prompt = prompt % (article.title, article.body)
    
        answer: GenerationResponse = self._generate_text(prompt=prompt, stream=stream, options=options)
        print(answer.strip())
        
        # Remove the square brackets from the string
        tags = answer.message["content"].strip("[]")


        # Split the string by comma to get individual tags
        tags_list = tags.split(",")

        # Remove leading and trailing whitespace from each tag
        [article.add_tag(tag.strip().capitalize()) for tag in tags_list]

        return article