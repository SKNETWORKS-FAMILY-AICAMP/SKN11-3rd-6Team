"""메인 VectorDB RAG Fine-tuner 클래스"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import pandas as pd
from typing import List, Dict, Any
from tqdm import tqdm
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.schema import Document
import random
import os
import json

from qa_generator import QAGenerator
from config import MODEL_CONFIGS, DEFAULT_CONFIG


class VectorDBRAGFineTuner:
    def __init__(
        self,
        model_name="facebook/opt-125m",
        use_qlora=False,
        max_length=512,
        vectordb_path=None,
        embedding_model="text-embedding-3-small"
    ):
        self.model_name = model_name
        self.use_qlora = use_qlora
        self.max_length = max_length
        self.vectordb_path = vectordb_path
        
        # 임베딩 설정
        if "openai" in embedding_model.lower():
            self.embeddings = OpenAIEmbeddings()
        else:
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        
        # VectorDB 로드
        self.vectordb = self._load_vectordb()
        
        # 모델 타입 결정
        config = MODEL_CONFIGS.get(model_name, DEFAULT_CONFIG)
        self.is_seq2seq = config["is_seq2seq"]
        
        # LoRA 설정
        self.lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=config["targets"],
            bias="none",
            task_type=config["task_type"],
        )
        
        # QLoRA 설정
        self.bnb_config = None
        if use_qlora and torch.cuda.is_available():
            self.bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        
        # QA 생성기
        self.qa_generator = QAGenerator(self.vectordb)
        
        self.model = None
        self.tokenizer = None
    
    def _load_vectordb(self):
        """VectorDB 로드"""
        if self.vectordb_path is None:
            raise ValueError("vectordb_path must be provided")
        
        return Chroma(
            persist_directory=self.vectordb_path,
            embedding_function=self.embeddings
        )
    
    def load_model(self):
        """모델과 토크나이저 로드"""
        print(f"Loading model: {self.model_name}")
        
        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, 
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 모델 로드
        try:
            if self.is_seq2seq:
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    quantization_config=self.bnb_config,
                    device_map="auto" if torch.cuda.is_available() else "cpu",
                    torch_dtype=torch.float32,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=self.bnb_config,
                    device_map="auto" if torch.cuda.is_available() else "cpu",
                    torch_dtype=torch.float32,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            
            if self.use_qlora and self.bnb_config:
                self.model = prepare_model_for_kbit_training(self.model)
            
            # LoRA 적용
            self.model = get_peft_model(self.model, self.lora_config)
            self.model.print_trainable_parameters()
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def generate_qa_pairs(self, num_pairs: int = 1000) -> List[Dict[str, str]]:
        """VectorDB에서 QA 쌍 생성"""
        qa_pairs = []
        
        # 모든 문서 가져오기
        all_docs = self.vectordb._collection.get()['documents']
        all_docs = [Document(page_content=doc) for doc in all_docs]
        
        qa_types = ["factoid", "explanation", "summary"]
        
        for i in tqdm(range(num_pairs), desc="Generating QA pairs"):
            try:
                doc = random.choice(all_docs)
                qa_type = random.choice(qa_types)
                qa_pair = self.qa_generator.generate_qa(doc.page_content, qa_type)
                
                if qa_pair:
                    qa_pairs.append(qa_pair)
                    
            except Exception as e:
                print(f"Error generating QA pair {i}: {e}")
                continue
        
        return qa_pairs
    
    def prepare_dataset(self, qa_pairs: List[Dict[str, str]]):
        """데이터셋 준비"""
        if self.is_seq2seq:
            data = [{
                "input_text": f"Question: {qa['question']}\nContext: {qa['context']}\n",
                "target_text": qa['answer']
            } for qa in qa_pairs]
        else:
            data = [{
                "text": f"Question: {qa['question']}\nContext: {qa['context']}\nAnswer: {qa['answer']}"
            } for qa in qa_pairs]
        
        dataset = Dataset.from_pandas(pd.DataFrame(data))
        
        # 토큰화
        if self.is_seq2seq:
            def tokenize_seq2seq(examples):
                model_inputs = self.tokenizer(
                    examples["input_text"],
                    padding="max_length",
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                )
                
                with self.tokenizer.as_target_tokenizer():
                    labels = self.tokenizer(
                        examples["target_text"],
                        padding="max_length",
                        truncation=True,
                        max_length=self.max_length,
                        return_tensors="pt"
                    )
                
                model_inputs["labels"] = labels["input_ids"]
                return model_inputs
            
            return dataset.map(tokenize_seq2seq, batched=True)
        else:
            def tokenize(examples):
                return self.tokenizer(
                    examples["text"],
                    padding="max_length",
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                )
            
            return dataset.map(tokenize, batched=True)
    
    def train(
        self,
        output_dir: str = "./finetuned-model",
        num_qa_pairs: int = 1000,
        num_epochs: int = 3,
        batch_size: int = 1,
        learning_rate: float = 2e-4,
        validation_split: float = 0.1,
        save_qa_pairs: bool = True
    ):
        """모델 학습"""
        # QA 쌍 생성
        print(f"Generating {num_qa_pairs} QA pairs...")
        qa_pairs = self.generate_qa_pairs(num_qa_pairs)
        
        # QA 쌍 저장
        if save_qa_pairs:
            os.makedirs(output_dir, exist_ok=True)
            pd.DataFrame(qa_pairs).to_csv(f"{output_dir}/qa_pairs.csv", index=False)
            with open(f"{output_dir}/qa_pairs.json", 'w') as f:
                json.dump(qa_pairs, f, indent=2)
        
        # 데이터셋 준비
        dataset = self.prepare_dataset(qa_pairs)
        
        # 학습/검증 분할
        if validation_split > 0:
            split = dataset.train_test_split(test_size=validation_split)
            train_dataset = split["train"]
            eval_dataset = split["test"]
        else:
            train_dataset = dataset
            eval_dataset = None
        
        # 학습 설정
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            logging_steps=10,
            save_steps=100,
            eval_steps=100,
            warmup_steps=50,
            fp16=False,
            save_strategy="steps",
            eval_strategy="steps" if eval_dataset else "no",
            load_best_model_at_end=True if eval_dataset else False,
            optim="adamw_torch",
            report_to="none",
        )
        
        # 트레이너
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False,
            ) if not self.is_seq2seq else None,
        )
        
        # 학습
        print("Starting training...")
        trainer.train()
        
        # 모델 저장
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        print(f"Model saved to {output_dir}")
    
    def generate_with_rag(self, query: str, max_new_tokens: int = 100, k: int = 3):
        """RAG 기반 텍스트 생성"""
        # 관련 문서 검색
        relevant_docs = self.vectordb.similarity_search(query, k=k)
        context = " ".join([doc.page_content[:200] for doc in relevant_docs])
        
        # 프롬프트 구성
        if self.is_seq2seq:
            prompt = f"Question: {query} Context: {context}"
        else:
            prompt = f"Question: {query}\nContext: {context}\nAnswer:"
        
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.max_length)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 답변 부분만 추출
        if "Answer:" in response:
            response = response.split("Answer:")[-1].strip()
        
        return response, relevant_docs