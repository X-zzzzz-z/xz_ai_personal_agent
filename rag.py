#负责准备文本向量模型
from sentence_transformers import SentenceTransformer
##这个变量作为配置常量使用，程序运行过程中通常不修改。
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(MODEL_NAME)

#定义一个生成嵌入函数，text希望是str； encode：编码，转换  
#单条文本向量化：把用户问题转换成一个向量。
def create_embedding(text: str):
    vector = model.encode(text)
    return vector


#批量文本向量化：把所有候选笔记片段一次性转换成多个向量。    
def create_embeddings(texts: list[str]):
    vectors = model.encode(texts)
    return vectors


#semantic：语义   search：搜索    query：搜索框里输入的内容   texts：被搜索的全部笔记片段
#语义搜索
def semantic_search(
    query: str,                                        
    texts: list[str],                                   
    top_k: int = 2                                      #默认返回相似度最高的两项
):
    if not isinstance(query,str) or not query.strip():
        raise ValueError("query必须是非空字符串")

    if not isinstance(texts,list) or not texts:
        raise ValueError("texts必须是非空列表")

    if not isinstance(top_k,int) or  top_k <= 0:
        raise ValueError("top_k必须是正整数")

    if top_k > len(texts):
        raise ValueError("top_k不能大于texts的数量")
    
    query_vector = create_embedding(query)              #用户问题->一个问题向量
    text_vectors = create_embeddings(texts)             #全部候选文字->多个候选文字向量

#scores:分数；  similarity：相似度； 
    scores = model.similarity(
        query_vector,
        text_vectors
    )[0]

#indices：索引  top_indices：分数来自哪里
    top_scores, top_indices = scores.topk(top_k)

    results = []

#zip：配对
    for score, index in zip(top_scores, top_indices):
        results.append({
            "index": index.item(),                  #原始候选的位置
            "text": texts[index.item()],            #原始文字
            "score": score.item()                   #相似度分数
        })

    return results

#heading: 标题
if __name__ == "__main__":
    texts = [
        "FileNotFoundError表示要读取的文件不存在。",
        "JSONDecodeError表示JSON文件内容无法正确解析。",
        "Tool Calling允许Agent调用外部工具。"
    ]

    results = semantic_search(
        query="JSON文件为什么无法读取",
        texts=texts,
        top_k=2
    )

    for result in results:
        print(result)