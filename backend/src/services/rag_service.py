"""
RAG服务 - 支持关键词检索和向量检索灵活切换
可通过环境变量或配置参数选择检索方式
"""
import os
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from openai import OpenAI

# 加载环境变量
load_dotenv()


class BaseRetriever:
    """检索器基类"""

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """搜索相关文档"""
        raise NotImplementedError


class SimpleKeywordRetriever(BaseRetriever):
    """简单关键词检索器"""

    def __init__(self, chunks: List[Document]):
        self.chunks = chunks

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """基于关键词匹配"""
        scored = []
        query_words = set(query)

        for chunk in self.chunks:
            content_words = set(chunk.page_content)
            matches = len(query_words & content_words)
            if matches > 0:
                scored.append((matches, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]


class VectorRetriever(BaseRetriever):
    """向量检索器（支持多种Embedding）- 支持智谱AI批处理"""

    def __init__(self, chunks: List[Document], embedding_type: str = "zhipu"):
        self.chunks = chunks
        self.embedding_type = embedding_type
        self.vectorstore = self._build_vectorstore()

    def _build_vectorstore(self):
        """构建向量数据库 - 支持批处理"""
        from langchain_community.vectorstores import Chroma

        if self.embedding_type == "zhipu":
            # 智谱AI Embedding（需要批处理）
            embeddings = self._init_zhipu_embedding()
            # 使用批处理构建向量数据库
            vectorstore = self._build_vectorstore_batch(embeddings, batch_size=60)
        elif self.embedding_type == "openai":
            # OpenAI Embedding
            embeddings = self._init_openai_embedding()
            vectorstore = Chroma.from_documents(
                documents=self.chunks,
                embedding=embeddings,
                persist_directory=f"./chroma_db_{self.embedding_type}"
            )
        elif self.embedding_type == "local":
            # 本地Embedding模型
            embeddings = self._init_local_embedding()
            vectorstore = Chroma.from_documents(
                documents=self.chunks,
                embedding=embeddings,
                persist_directory=f"./chroma_db_{self.embedding_type}"
            )
        else:
            raise ValueError(f"Unknown embedding type: {self.embedding_type}")

        return vectorstore

    def _build_vectorstore_batch(self, embeddings, batch_size: int = 30):
        """批处理构建向量数据库（智谱AI payload限制约12KB）"""
        from langchain_community.vectorstores import Chroma

        print(f"[INFO] Building vectorstore with batch processing (batch_size={batch_size}, total_chunks={len(self.chunks)})")

        # 第一批：创建数据库
        first_batch = self.chunks[:batch_size]
        vectorstore = Chroma.from_documents(
            documents=first_batch,
            embedding=embeddings,
            persist_directory=f"./chroma_db_{self.embedding_type}"
        )
        print(f"[INFO] Processed batch 1/{(len(self.chunks)-1)//batch_size + 1} ({len(first_batch)} chunks)")

        # 后续批次：追加到数据库
        for i in range(batch_size, len(self.chunks), batch_size):
            batch = self.chunks[i:i+batch_size]
            vectorstore.add_documents(batch)
            batch_num = i // batch_size + 1
            total_batches = (len(self.chunks)-1) // batch_size + 1
            print(f"[INFO] Processed batch {batch_num}/{total_batches} ({len(batch)} chunks)")

        print(f"[INFO] Vectorstore built successfully with {len(self.chunks)} chunks")
        return vectorstore

    def _init_zhipu_embedding(self):
        """初始化智谱AI Embedding - 使用自定义实现"""
        from .zhipu_embeddings import ZhipuEmbeddings

        api_key = os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError("ZHIPUAI_API_KEY not configured")

        return ZhipuEmbeddings(api_key=api_key)

    def _init_openai_embedding(self):
        """初始化OpenAI Embedding"""
        from langchain_openai import OpenAIEmbeddings

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        return OpenAIEmbeddings(
            openai_api_key=api_key,
            model="text-embedding-3-small"
        )

    def _init_local_embedding(self):
        """初始化本地Embedding模型（需要GPU）"""
        from langchain_huggingface import HuggingFaceEmbeddings

        device = os.getenv("EMBEDDING_DEVICE", "cpu")
        model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")

        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """向量相似度搜索"""
        return self.vectorstore.similarity_search(query, k=k)


class RAGService:
    """RAG服务 - 支持灵活切换检索方式"""

    def __init__(
        self,
        knowledge_base_dir: str = "./test_data",
        retrieval_mode: str = "auto",  # auto, keyword, vector
        embedding_type: str = "zhipu",  # zhipu, openai, local
        chunk_size: int = 500,  # 优化：从400增加到500
        chunk_overlap: int = 80,  # 优化：从50增加到80
    ):
        """
        初始化RAG服务

        Args:
            knowledge_base_dir: 知识库目录（txt文件）
            retrieval_mode: 检索模式
                - auto: 自动选择（有API Key用向量，否则用关键词）
                - keyword: 强制使用关键词检索
                - vector: 强制使用向量检索
            embedding_type: Embedding类型（仅在vector模式下有效）
                - zhipu: 智谱AI Embedding API
                - openai: OpenAI Embedding API
                - local: 本地bge模型（需GPU）
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠大小
        """
        self.knowledge_base_dir = knowledge_base_dir
        self.retrieval_mode = retrieval_mode
        self.embedding_type = embedding_type
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 初始化DeepSeek客户端
        self.llm_client = self._init_llm()

        # 加载知识库
        self.chunks = self._load_knowledge_base()

        # 初始化检索器
        self.retriever = self._init_retriever()

    def _init_llm(self) -> OpenAI:
        """初始化LLM客户端（DeepSeek V4）"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured")

        return OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    def _load_knowledge_base(self) -> List[Document]:
        """加载知识库并分块"""
        documents = []

        # 加载所有txt文件
        kb_path = Path(self.knowledge_base_dir)
        for txt_file in kb_path.glob("*.txt"):
            loader = TextLoader(str(txt_file), encoding="utf-8")
            documents.extend(loader.load())

        # 文本分块
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；"],
        )

        chunks = splitter.split_documents(documents)
        return chunks

    def _init_retriever(self) -> BaseRetriever:
        """初始化检索器"""
        # 自动模式：检测API Key决定使用哪种检索
        if self.retrieval_mode == "auto":
            if self._can_use_vector_search():
                print(f"[INFO] Using vector retrieval ({self.embedding_type})")
                return VectorRetriever(self.chunks, self.embedding_type)
            else:
                print("[INFO] Using keyword retrieval (no Embedding API configured)")
                return SimpleKeywordRetriever(self.chunks)

        # 强制关键词模式
        elif self.retrieval_mode == "keyword":
            print("[INFO] Using keyword retrieval (forced mode)")
            return SimpleKeywordRetriever(self.chunks)

        # 强制向量模式
        elif self.retrieval_mode == "vector":
            print(f"[INFO] Using vector retrieval ({self.embedding_type})")
            return VectorRetriever(self.chunks, self.embedding_type)

        else:
            raise ValueError(f"Unknown retrieval mode: {self.retrieval_mode}")

    def _can_use_vector_search(self) -> bool:
        """检测是否可以使用向量检索"""
        if self.embedding_type == "zhipu":
            return bool(os.getenv("ZHIPUAI_API_KEY"))
        elif self.embedding_type == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif self.embedding_type == "local":
            return True  # 本地模型总是可用（假设已安装）
        return False

    def search(self, query: str, k: int = 5) -> List[Document]:
        """检索相关文档（优化：从3增加到5）"""
        return self.retriever.similarity_search(query, k=k)

    def generate_answer(
        self,
        question: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> dict:
        """
        生成答案（完整RAG流程）

        Returns:
            {
                "answer": "生成的答案",
                "sources": ["来源1", "来源2", ...],
                "tokens": {"input": 100, "output": 200, "total": 300},
                "cost": 0.001,
                "retrieval_mode": "keyword" or "vector"
            }
        """
        # 1. 检索相关文档（优化：使用默认的k=5）
        relevant_docs = self.search(question)

        # 2. 构建上下文
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # 3. 调用LLM生成
        response = self.llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是EDA领域专家。请基于提供的上下文准确回答问题。如果上下文中没有相关信息，请说明。"
                },
                {
                    "role": "user",
                    "content": f"上下文：\n{context}\n\n问题：{question}"
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        answer = response.choices[0].message.content
        usage = response.usage

        # 4. 计算成本
        cost = (usage.prompt_tokens / 1000 * 0.001) + \
               (usage.completion_tokens / 1000 * 0.002)

        # 5. 返回结果
        return {
            "answer": answer,
            "sources": [doc.page_content[:100] + "..." for doc in relevant_docs],
            "tokens": {
                "input": usage.prompt_tokens,
                "output": usage.completion_tokens,
                "total": usage.total_tokens
            },
            "cost": cost,
            "retrieval_mode": "vector" if isinstance(self.retriever, VectorRetriever) else "keyword"
        }

    def generate_lecture(
        self,
        topic: str,
        detail_level: str = "medium",  # simple, medium, detailed
    ) -> dict:
        """
        生成讲义

        Args:
            topic: 讲义主题
            detail_level: 详细程度

        Returns:
            {
                "title": "讲义标题",
                "content": "讲义内容（Markdown格式）",
                "sources": ["参考来源1", ...],
                "tokens": {...},
                "cost": 0.001
            }
        """
        # 1. 检索相关知识
        relevant_docs = self.search(topic, k=5)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # 2. 根据详细程度调整prompt
        level_prompts = {
            "simple": "生成简明扼要的讲义，适合快速了解",
            "medium": "生成中等详细的讲义，包含关键概念和示例",
            "detailed": "生成详细深入的讲义，包含原理、示例和扩展内容"
        }

        # 3. 生成讲义
        response = self.llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"你是EDA领域专家。{level_prompts.get(detail_level, level_prompts['medium'])}。使用Markdown格式。"
                },
                {
                    "role": "user",
                    "content": f"基于以下参考资料，生成关于'{topic}'的讲义：\n\n{context}"
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )

        content = response.choices[0].message.content
        usage = response.usage
        cost = (usage.prompt_tokens / 1000 * 0.001) + \
               (usage.completion_tokens / 1000 * 0.002)

        return {
            "title": topic,
            "content": content,
            "sources": [doc.page_content[:100] + "..." for doc in relevant_docs],
            "tokens": {
                "input": usage.prompt_tokens,
                "output": usage.completion_tokens,
                "total": usage.total_tokens
            },
            "cost": cost
        }


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    import sys
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("="*60)
    print("RAG服务测试 - 可切换检索模式")
    print("="*60)

    # 示例1：自动模式（推荐）
    print("\n【示例1】自动模式")
    print("-"*60)
    rag = RAGService(
        knowledge_base_dir="./test_data",
        retrieval_mode="auto",  # 自动选择
        embedding_type="zhipu"  # 如果有API Key会用
    )

    result = rag.generate_answer("什么是EDA工具？")
    print(f"\n问题: 什么是EDA工具？")
    print(f"检索模式: {result['retrieval_mode']}")
    print(f"\n答案:\n{result['answer']}")
    print(f"\nToken: {result['tokens']}")
    print(f"成本: ¥{result['cost']:.6f}")

    # 示例2：强制使用关键词检索
    print("\n" + "="*60)
    print("【示例2】强制关键词模式")
    print("-"*60)
    rag_keyword = RAGService(
        knowledge_base_dir="./test_data",
        retrieval_mode="keyword"  # 强制关键词
    )

    result2 = rag_keyword.generate_answer("时序分析的作用是什么？")
    print(f"\n问题: 时序分析的作用是什么？")
    print(f"检索模式: {result2['retrieval_mode']}")
    print(f"\n答案:\n{result2['answer']}")

    # 示例3：生成讲义
    print("\n" + "="*60)
    print("【示例3】生成讲义")
    print("-"*60)
    lecture = rag.generate_lecture(
        topic="数字电路设计基础",
        detail_level="medium"
    )
    print(f"\n讲义标题: {lecture['title']}")
    print(f"\n讲义内容:\n{lecture['content'][:500]}...")
    print(f"\n成本: ¥{lecture['cost']:.6f}")

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
