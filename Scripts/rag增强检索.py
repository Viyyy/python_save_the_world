import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import pandas as pd
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
import datetime
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
)


BASE_DIR = "vectorstore"
QUESTION_KW = "question"
MAX_TOKENS = 1e6 # max_completion_tokens

# region common
def get_embeddings():
    """
    获取Embedding模型
    """
    return OpenAIEmbeddings(
        api_key=os.getenv("EMBEDDING_API_KEY"),
    )


def get_llm():
    """
    获取OpenAI语言模型
    """
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        max_completion_tokens=MAX_TOKENS,
        temperature=0.5,
    )


# endregion


# region Chroma
def create_db_from_df(file_path: str):
    """
    从excel或csv文件中读取数据，并创建chroma数据库
    - param file_path: 文件路径
    """
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("文件格式不支持")

    if len(df) == 0:
        raise ValueError("数据为空")

    texts = []
    cols = df.columns.tolist()

    for i, row in df.iterrows():
        text = ""
        for col in cols:
            text += f"{col}: {row[col]}\n"
        texts.append(text)

    vectorstore = Chroma.from_texts(
        texts=texts,
        embedding=get_embeddings(),
        persist_directory=f"./{BASE_DIR}/df_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    return vectorstore


def create_db_from_pdf(file_path: str):
    """
    从pdf文件中读取数据，并创建chroma数据库
    - param file_path: 文件路径
    """
    pdf_loader = PyMuPDFLoader(file_path)
    docs = pdf_loader.load_and_split()

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        persist_directory=f"./{BASE_DIR}/pdf_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    return vectorstore


def load_chroma_db(db_dir: str):
    """
    从文件夹中加载chroma数据库
    - param db_dir: 数据库文件夹路径
    """

    vectorstore = Chroma(persist_directory=db_dir, embedding_function=get_embeddings())

    return vectorstore


def load_all_chroma_db(base_dir: str = BASE_DIR):
    """
    从根目录中加载所有chroma数据库
    - param base_dir: 根目录
    """

    db_dirs = [
        os.path.join(base_dir, db_dir)
        for db_dir in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, db_dir))
    ]

    dbs = []
    for db_dir in db_dirs:
        try:
            db = load_chroma_db(db_dir)
            dbs.append(db)
        except:
            print(f"加载{db_dir}失败")
    return dbs


def combine_dbs_to_retriver(dbs: list[Chroma]):
    """
    组合多个Chroma数据库，返回Retriever
    """
    retrievers = [db.as_retriever() for db in dbs]

    combined_retriever = RunnableParallel(
        context=lambda x: [
            doc for retriever in retrievers for doc in retriever.invoke(x[QUESTION_KW])
        ]
    )
    return combined_retriever


# endregion


# region RAG
def format_context(context: dict):
    """
    格式化context
    """
    docs: list = context.get("context", None)
    if docs is None:
        raise ValueError("context中没有文档")
    return "\n\n".join(doc.page_content for doc in docs)


def get_prompt():
    '''
    获取提示词
    '''
    return ChatPromptTemplate(
        input_variables=["context", "question"],
        input_types={},
        partial_variables={},
        messages=[
            HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=["context", "question"],
                    input_types={},
                    partial_variables={},
                    template="""
                        human

                        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.

                        Question: {question} 

                        Context: {context} 

                        Answer:
                """,
                ),
                additional_kwargs={},
            )
        ],
    )


def get_rag_chain(
    retriever,
    llm=None,
    prompt=None,
    question_kw=QUESTION_KW,
    format_func=format_context,
):
    """
    获取RAG模型
    - param retriever: 向量数据库
    - param llm: 语言模型，为空时使用get_llm()获取
    - param prompt: 初始提示，为空时使用rlm/rag-prompt
    - param question_kw: 问题关键字，默认为'question'
    - param format_func: 格式化context的函数
    """
    if prompt is None:
        # prompt = hub.pull("rlm/rag-prompt")
        prompt = get_prompt()
    if llm is None:
        llm = get_llm()

    rag_chain = (
        {"context": retriever | format_func, question_kw: RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(question, rag_chain, question_kw=QUESTION_KW):
    """
    提问并获取答案
    - param question: 问题
    - param rag_chain: RAG模型
    - param question_kw: 问题关键字，默认为'question'
    """
    answer = rag_chain.invoke({question_kw: question})
    return answer

# endregion
