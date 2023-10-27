from langchain.retrievers import AmazonKendraRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.llms  import AzureOpenAI
import sys
import os


from dotenv import load_dotenv

load_dotenv()

deployment_name = 'gpt-35-turbo-ronald' #'REPLACE_WITH_YOUR_DEPLOYMENT_NAME' #This will correspond to the custom name you chose for your deployment when you deployed a model. 


os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-05-15"
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_KEY")

MAX_HISTORY_LENGTH = 5

def build_chain():
  region = os.environ["AWS_REGION"]
  kendra_index_id = os.environ["KENDRA_INDEX_ID"]

  llm = AzureOpenAI(batch_size=5, temperature=0, max_tokens=300, deployment_name=deployment_name)
      
  retriever = AmazonKendraRetriever(
                index_id=kendra_index_id, 
                region_name=region, 
                attribute_filter={
                    "EqualsTo": {      
                        "Key": "_language_code",
                        "Value": {
                            "StringValue": "nl"
                            }
                        }
                    })

  prompt_template = """
Het volgende is een vriendelijk gesprek tussen een mens en een AI.
De AI is spraakzaam en geeft veel specifieke details vanuit zijn context.
Als de AI het antwoord op een vraag niet weet, zegt hij eerlijk dat hij het niet weet.
{context}
Instructie: Geef op basis van de bovenstaande documenten een gedetailleerd antwoord op de vraag: {question}. Antwoord "weet ik niet" als het niet in het document aanwezig is.
Oplossing:
"""
  PROMPT = PromptTemplate(
      template=prompt_template, input_variables=["context", "question"]
  )

  condense_qa_template = """
Gegeven het volgende gesprek en een vervolgvraag, herschrijf de vervolgvraag zodat het een op zichzelf staande vraag wordt.

Chatgeschiedenis:
{chat_history}
Vervolginvoer: {question}
Op zichzelf staande vraag:
"""
  standalone_question_prompt = PromptTemplate.from_template(condense_qa_template)

  qa = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=retriever, 
        condense_question_prompt=standalone_question_prompt, 
        return_source_documents=True, 
        combine_docs_chain_kwargs={"prompt":PROMPT})
  return qa

def run_chain(chain, prompt: str, history=[]):
  return chain({"question": prompt, "chat_history": history})


if __name__ == "__main__":
  class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

  qa = build_chain()
  chat_history = []
  print(bcolors.OKBLUE + "Hello! How can I help you?" + bcolors.ENDC)
  print(bcolors.OKCYAN + "Ask a question, start a New search: or CTRL-D to exit." + bcolors.ENDC)
  print(">", end=" ", flush=True)
  for query in sys.stdin:
    if (query.strip().lower().startswith("new search:")):
      query = query.strip().lower().replace("new search:","")
      chat_history = []
    elif (len(chat_history) == MAX_HISTORY_LENGTH):
      chat_history.pop(0)
    result = run_chain(qa, query, chat_history)
    chat_history.append((query, result["answer"]))
    print(bcolors.OKGREEN + result['answer'] + bcolors.ENDC)
    if 'source_documents' in result:
      print(bcolors.OKGREEN + 'Sources:')
      for d in result['source_documents']:
        print(d.metadata['source'])
    print(bcolors.ENDC)
    print(bcolors.OKCYAN + "Ask a question, start a New search: or CTRL-D to exit." + bcolors.ENDC)
    print(">", end=" ", flush=True)
  print(bcolors.OKBLUE + "Bye" + bcolors.ENDC)
