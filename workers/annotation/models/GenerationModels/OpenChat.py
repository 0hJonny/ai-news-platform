from .GenerationModel import GenerationModel
from .GenerationResponse import GenerationResponse
from models import ArticleAnnotation

class OpenChat(GenerationModel):
    def __init__(self):
        super().__init__()
        self.model_name = "openchat"
        self.data = {
            "stream": False,  # Placeholder for stream option
            "options": {
                "temperature": 0.8,  # Placeholder for temperature option
                "top_p": 0.9
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
        
        answer = answer.message["content"]

        index = answer.find('###')

        if index != -1:
            answer = answer[index:]
        article.annotation = answer
        
        article.neural_networks["annotator"] = self.model_name
        
        return article

        
    def translate(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        prompt = """
            Translate article title to %s language. Safe the structure.
            Article title is "%s"
            """
        prompt = prompt % (article.language_to_answer_name, article.title)

        answer = self._generate_text(prompt=prompt, stream=stream, options=options)

        article.title = answer.message["content"]

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

        article.annotation = answer.message["content"]

        article.neural_networks["translator"] = self.model_name
        
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
            Write only one the topic!.
            """
        prompt = prompt % (article.title, article.body)
        
        answer = self._generate_text(prompt=prompt, stream=stream, options=options)
        
        article.theme_name = answer.message["content"].lower().replace('*', '').replace(' ', '').replace('\n', '')

        ## TODO CHECK FOR THEMES CLASSIFY
        
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

        tag_list = answer.message["content"].replace("[", "").replace("]", "").replace("'", "").replace(' ', '').split(',')
        [article.add_tag(tag.capitalize()) for tag in tag_list]

        return article
