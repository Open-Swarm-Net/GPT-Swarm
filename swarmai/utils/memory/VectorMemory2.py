import threading
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from pathlib import Path
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain

def synchronized_mem(method):
    def wrapper(self, *args, **kwargs):
        with self.lock:
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                print(f"Failed to execute {method.__name__}: {e}")
    return wrapper

class VectorMemory:
    """Simple vector memory implementation using langchain and Chroma"""

    def __init__(self, loc=None, chunk_size=1000, chunk_overlap_frac=0.1, *args, **kwargs):
        if loc is None:
            loc = "./tmp/vector_memory"
        self.loc = Path(loc)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_size*chunk_overlap_frac
        self.embeddings = OpenAIEmbeddings()
        self.count = 0
        self.lock = threading.Lock()

        self.db = self._init_db()
        self.qa = self._init_retriever()

    def _init_db(self):
        texts = ["init"] # TODO find how to initialize Chroma without any text
        chroma_db = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            persist_directory=str(self.loc),
        )
        self.count = chroma_db._collection.count()
        return chroma_db
    
    def _init_retriever(self):
        model = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
        qa_chain = load_qa_chain(model, chain_type="stuff")
        retriever = self.db.as_retriever(search_type="mmr", search_kwargs={"k":10})
        qa = RetrievalQA(combine_documents_chain=qa_chain, retriever=retriever)
        return qa
    
    @synchronized_mem
    def add_entry(self, entry: str):
        """Add an entry to the internal memory.
        """
        text_splitter = CharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, separator=" ")
        texts = text_splitter.split_text(entry)

        self.db.add_texts(texts)
        self.count += self.db._collection.count()
        self.db.persist()
        return True
    
    @synchronized_mem
    def search_memory(self, query: str, k=10, type="mmr", distance_threshold=0.5):
        """Searching the vector memory for similar entries
        
        Args:
            - query (str): the query to search for
            - k (int): the number of results to return
            - type (str): the type of search to perform: "cos" or "mmr"
            - distance_threshold (float): the similarity threshold to use for the search. Results with distance > similarity_threshold will be dropped.

        Returns:
            - texts (list[str]): a list of the top k results
        """
        self.count = self.db._collection.count()
        if k > self.count:
            k = self.count - 1
        if k <= 0:
            return None

        if type == "mmr":
            texts = self.db.max_marginal_relevance_search(query=query, k=k, fetch_k = min(20,self.count))
            texts = [text.page_content for text in texts]
        elif type == "cos":
            texts = self.db.similarity_search_with_score(query=query, k=k)
            texts = [text[0].page_content for text in texts if text[-1] < distance_threshold]

        return texts
    
    @synchronized_mem
    def ask_question(self, question: str):
        """Ask a question to the vector memory
        
        Args:
            - question (str): the question to ask

        Returns:
            - answer (str): the answer to the question
        """
        answer = self.qa.run(question)
        return answer
