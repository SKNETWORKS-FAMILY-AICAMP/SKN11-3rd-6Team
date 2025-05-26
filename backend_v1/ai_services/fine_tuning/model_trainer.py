import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TrainingArguments, 
    Trainer, DataCollatorForLanguageModeling, BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import pandas as pd
import json

class ModelTrainer:
    def __init__(self, model_name: str = "microsoft/phi-2", use_qlora: bool = False):
        self.model_name = model_name
        self.use_qlora = use_qlora
        self.model = None
        self.tokenizer = None
        
        # LoRA 설정
        self.lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj"],
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # QLoRA 설정
        self.bnb_config = None
        if use_qlora and torch.cuda.is_available():
            self.bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True
            )

    def load_model(self):
        """모델과 토크나이저 로드"""
        print(f"Loading model: {self.model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=self.bnb_config,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        if self.use_qlora:
            self.model = prepare_model_for_kbit_training(self.model)
        
        self.model = get_peft_model(self.model, self.lora_config)
        self.model.print_trainable_parameters()

    def prepare_dataset(self, qa_pairs_file: str):
        """QA 쌍을 학습용 데이터셋으로 변환"""
        with open(qa_pairs_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
        
        # 프롬프트 형식으로 변환
        texts = []
        for qa in qa_pairs:
            text = f"Question: {qa['question']}\nContext: {qa['context']}\nAnswer: {qa['answer']}"
            texts.append({"text": text})
        
        dataset = Dataset.from_pandas(pd.DataFrame(texts))
        
        def tokenize(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                padding="max_length",
                max_length=512,
                return_tensors="pt"
            )
        
        return dataset.map(tokenize, batched=True)

    def train(self, qa_pairs_file: str, output_dir: str, num_epochs: int = 3, batch_size: int = 1):
        """모델 학습"""
        dataset = self.prepare_dataset(qa_pairs_file)
        
        # 학습/검증 분할
        split = dataset.train_test_split(test_size=0.1)
        train_dataset = split["train"]
        eval_dataset = split["test"]
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            logging_steps=10,
            save_steps=100,
            eval_steps=100,
            warmup_steps=50,
            save_strategy="steps",
            eval_strategy="steps",
            load_best_model_at_end=True,
            report_to="none"
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
        )
        
        print("Starting training...")
        trainer.train()
        
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        print(f"Model saved to {output_dir}")
