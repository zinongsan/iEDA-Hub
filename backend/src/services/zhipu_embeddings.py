"""
智谱AI Embedding 自定义实现
用于解决LangChain兼容性问题
"""
import os
import requests
from typing import List
from langchain_core.embeddings import Embeddings


class ZhipuEmbeddings(Embeddings):
    """智谱AI Embedding 自定义实现"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPUAI_API_KEY not configured")

        self.api_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        self.model = "embedding-2"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文档（智谱AI payload限制约12KB）"""
        all_embeddings = []

        # 智谱AI限制：总payload约12-15KB
        # 配合chunk_size=500，每个文本最多500字符
        max_length = 500  # 优化：从400增加到500
        truncated_texts = []
        for text in texts:
            if len(text) > max_length:
                truncated_texts.append(text[:max_length])
            else:
                truncated_texts.append(text)

        # 分批处理，每批最多30条
        batch_size = 30
        for i in range(0, len(truncated_texts), batch_size):
            batch_texts = truncated_texts[i:i+batch_size]
            batch_embeddings = self._call_api(batch_texts)
            all_embeddings.extend(batch_embeddings)

            if len(truncated_texts) > batch_size:
                print(f"[DEBUG] Embedded batch {i//batch_size + 1}/{(len(truncated_texts)-1)//batch_size + 1} ({len(batch_texts)} texts)")

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        embeddings = self._call_api([text])
        return embeddings[0]

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """调用智谱AI Embedding API"""
        import json

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

        # 智谱AI Embedding API的标准格式
        payload = {
            "model": self.model,
            "input": texts
        }

        print(f"[DEBUG] Calling Zhipu API with {len(texts)} texts")

        try:
            # 手动序列化JSON，确保中文正确编码
            json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')

            response = requests.post(
                self.api_url,
                headers=headers,
                data=json_data,  # 使用data而不是json参数
                timeout=30
            )

            # 打印详细错误信息用于调试
            print(f"[DEBUG] Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"[DEBUG] Response: {response.text}")

            response.raise_for_status()

            data = response.json()
            print(f"[DEBUG] Successfully got {len(data.get('data', []))} embeddings")

            # 提取embedding向量
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings

        except requests.exceptions.HTTPError as e:
            error_msg = f"智谱AI API调用失败: {e.response.text}"
            print(f"[ERROR] {error_msg}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"智谱AI API调用异常: {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise ValueError(error_msg)


# 测试函数
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("测试智谱AI Embedding...")
    embeddings = ZhipuEmbeddings()

    # 测试单个文本
    print("\n测试1：单个文本")
    result = embeddings.embed_query("什么是EDA工具？")
    print(f"向量维度: {len(result)}")
    print(f"向量前5个值: {result[:5]}")

    # 测试批量文本（少于64条）
    print("\n测试2：批量文本（10条）")
    texts = [f"测试文本{i}" for i in range(10)]
    results = embeddings.embed_documents(texts)
    print(f"成功嵌入 {len(results)} 条文本")

    # 测试批量文本（超过64条）
    print("\n测试3：批量文本（100条）")
    texts = [f"测试文本{i}" for i in range(100)]
    results = embeddings.embed_documents(texts)
    print(f"成功嵌入 {len(results)} 条文本")

    print("\n✅ 所有测试通过！")
