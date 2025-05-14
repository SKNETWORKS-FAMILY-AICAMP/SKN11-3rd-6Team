"""VectorDB RAG Fine-tuner 사용 예제"""

from finetuner import VectorDBRAGFineTuner


def basic_example():
    """기본 사용 예제"""
    # RAG 파인튜너 초기화
    finetuner = VectorDBRAGFineTuner(
        model_name="facebook/opt-125m",
        use_qlora=False,
        vectordb_path="./chroma_db",
        embedding_model="text-embedding-3-small"
    )
    
    # 모델 로드
    finetuner.load_model()
    
    # 학습 실행
    finetuner.train(
        output_dir="./rag-finetuned-model",
        num_qa_pairs=500,
        num_epochs=3,
        batch_size=1,
        save_qa_pairs=True
    )
    
    # 테스트 생성
    query = "What is machine learning?"
    response, docs = finetuner.generate_with_rag(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print(f"Retrieved docs: {len(docs)}")


def advanced_example():
    """고급 사용 예제 - 다른 모델 사용"""
    # T5 모델 사용
    finetuner = VectorDBRAGFineTuner(
        model_name="google/flan-t5-small",
        use_qlora=False,
        vectordb_path="./chroma_db",
        embedding_model="text-embedding-3-small",
        max_length=256
    )
    
    finetuner.load_model()
    
    # 더 적은 데이터로 빠른 학습
    finetuner.train(
        output_dir="./t5-rag-finetuned",
        num_qa_pairs=100,
        num_epochs=1,
        batch_size=2,
        learning_rate=5e-5,
        save_qa_pairs=True
    )
    
    # 여러 쿼리 테스트
    queries = [
        "What is deep learning?",
        "Explain neural networks",
        "How does backpropagation work?"
    ]
    
    for query in queries:
        response, docs = finetuner.generate_with_rag(query, max_new_tokens=150)
        print(f"\nQuery: {query}")
        print(f"Response: {response}")
        print(f"Used {len(docs)} documents for context")


def inference_only_example():
    """이미 학습된 모델로 추론만 하는 예제"""
    # 기존 학습된 모델 로드
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from langchain.vectorstores import Chroma
    from langchain.embeddings import OpenAIEmbeddings
    
    # 모델과 토크나이저 로드
    model_path = "./rag-finetuned-model"
    model = AutoModelForCausalLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # VectorDB 로드
    embeddings = OpenAIEmbeddings()
    vectordb = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    
    # 쿼리 실행
    query = "What are transformers in machine learning?"
    relevant_docs = vectordb.similarity_search(query, k=3)
    context = " ".join([doc.page_content[:200] for doc in relevant_docs])
    
    prompt = f"Question: {query}\nContext: {context}\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "Answer:" in response:
        response = response.split("Answer:")[-1].strip()
    
    print(f"Query: {query}")
    print(f"Response: {response}")


if __name__ == "__main__":
    # 원하는 예제 실행
    basic_example()
    # advanced_example()
    # inference_only_example()