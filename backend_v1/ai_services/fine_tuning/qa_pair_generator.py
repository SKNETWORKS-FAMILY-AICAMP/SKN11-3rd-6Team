import json
import random
import time
import asyncio
from typing import List, Dict, Tuple
from tqdm import tqdm
from collections import defaultdict
import sys
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import aiofiles

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rag import RAG
from llm import LLM

@dataclass
class QAResult:
    question: str
    answer: str = None
    context: str = None
    error: str = None

class QAPairGenerator:
    def __init__(self, concurrency_limit: int = 10, batch_size: int = 50):
        self.rag = RAG()
        self.llm = LLM(model_name="gpt-3.5-turbo")
        self.stats = defaultdict(int)
        self.start_time = None
        self.concurrency_limit = concurrency_limit
        self.batch_size = batch_size
        
        # 세마포어로 동시 실행 제한
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        
        # 결과 캐시 (같은 질문 반복 방지)
        self.cache = {}
        
    async def generate_qa_pairs(self, questions_file: str, output_file: str, max_pairs: int = None):
        """병렬 처리로 QA 쌍 생성"""
        self.start_time = time.time()
        
        # 질문 로드 (비동기)
        print("📖 Loading questions...")
        questions = await self._load_questions_async(questions_file)
        
        total_questions = len(questions)
        
        if max_pairs:
            questions = random.sample(questions, min(max_pairs, len(questions)))
            print(f"🎲 Randomly selected {len(questions)} questions from {total_questions}")
        
        print(f"🎯 Target: Generate {len(questions)} QA pairs")
        print(f"⚡ Concurrency limit: {self.concurrency_limit}")
        print(f"📦 Batch size: {self.batch_size}")
        
        # 배치별 병렬 처리
        qa_pairs = []
        
        # 배치로 나누기
        batches = [questions[i:i + self.batch_size] 
                  for i in range(0, len(questions), self.batch_size)]
        
        print(f"🔄 Processing {len(batches)} batches...")
        
        # 전체 진행도
        total_pbar = tqdm(total=len(questions), desc="Total Progress")
        
        for batch_idx, batch in enumerate(batches):
            print(f"\n🚀 Processing batch {batch_idx + 1}/{len(batches)}")
            
            # 배치 내 병렬 처리
            batch_results = await self._process_batch_parallel(batch)
            
            # 결과 분류
            for result in batch_results:
                if result.error:
                    # 실패한 질문은 간단히 로깅만
                    self.stats['failed'] += 1
                    print(f"❌ Failed: {result.error}")
                else:
                    qa_pairs.append({
                        "question": result.question,
                        "answer": result.answer,
                        "context": result.context[:1000] if result.context else ""
                    })
                    self.stats['success'] += 1
                
                total_pbar.update(1)
            
                # 배치별 중간 저장
            if (batch_idx + 1) % 5 == 0:  # 5배치마다
                await self._save_intermediate_async(qa_pairs, output_file, batch_idx + 1)
                self._print_progress_stats(len(qa_pairs) + self.stats['failed'], len(questions))
        
        total_pbar.close()
        
        # 최종 결과 저장 및 통계
        await self._save_final_results_async(qa_pairs, output_file)
        self._print_final_stats(len(questions), qa_pairs)
        
        return qa_pairs
    
    async def _load_questions_async(self, questions_file: str) -> List[Dict]:
        """비동기로 질문 파일 로드"""
        async with aiofiles.open(questions_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            return data['questions']
    
    async def _process_batch_parallel(self, batch: List[Dict]) -> List[QAResult]:
        """배치를 병렬로 처리"""
        tasks = [self._process_single_question(q_data) for q_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(QAResult(
                    question=batch[i]['question'],
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_single_question(self, q_data: Dict) -> QAResult:
        """단일 질문 처리 (세마포어로 동시 실행 제한)"""
        async with self.semaphore:
            try:
                country = q_data['country'].lower()
                topic = q_data['topic']
                question = q_data['question']
                
                if topic == 'immigration':
                    topic = 'immigration_regulations'
                elif topic == 'safety':
                    topic = 'immigration_safety'
                    
                # 캐시 확인
                cache_key = f"{country}_{topic}_{hash(question)}"
                if cache_key in self.cache:
                    cached_result = self.cache[cache_key]
                    return QAResult(
                        question=question,
                        answer=cached_result['answer'],
                        context=cached_result['context']
                    )
                
                # RAG 검색
                context, references = await self._search_context_async(
                    question, country, topic + "_info"
                )
                
                # LLM 답변 생성
                answer = await self.llm.generate_with_translation(
                    query=question,
                    context=context,
                    references=references,
                    translate_to_korean=False
                )
                
                # 캐시에 저장
                self.cache[cache_key] = {
                    'answer': answer,
                    'context': context
                }
                
                return QAResult(
                    question=question,
                    answer=answer,
                    context=context
                )
                
            except Exception as e:
                return QAResult(
                    question=q_data['question'],
                    error=str(e)
                )
    
    async def _search_context_async(self, question: str, country: str, topic: str) -> Tuple[str, List]:
        """RAG 검색 (비동기 래퍼)"""
        # RAG.search_with_translation이 동기라면 ThreadPoolExecutor 사용
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=5) as executor:
            future = executor.submit(
                self.rag.search_with_translation,
                query=question,
                country=country,
                doc_type=topic
            )
            return await loop.run_in_executor(None, lambda: future.result())
    
    async def _save_intermediate_async(self, qa_pairs: List[Dict], output_file: str, batch_num: int):
        """비동기 중간 저장"""
        backup_file = f"{output_file}.backup_batch_{batch_num}"
        async with aiofiles.open(backup_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(qa_pairs, ensure_ascii=False, indent=2))
        print(f"💾 Backup saved: batch {batch_num}")
    
    async def _save_final_results_async(self, qa_pairs: List[Dict], output_file: str):
        """비동기 최종 결과 저장"""
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(qa_pairs, ensure_ascii=False, indent=2))
    
    def _print_progress_stats(self, current: int, total: int):
        """진행 상황 통계"""
        elapsed_time = time.time() - self.start_time
        if current > 0:
            avg_time_per_pair = elapsed_time / current
            estimated_remaining = avg_time_per_pair * (total - current)
            success_rate = (self.stats['success'] / current) * 100
            
            print(f"📈 Progress: {current}/{total}")
            print(f"✅ Success rate: {success_rate:.1f}%")
            print(f"⏱️ Avg time: {avg_time_per_pair:.2f}s/pair")
            print(f"⏰ ETA: {estimated_remaining/60:.1f} min")
    
    def _print_final_stats(self, total_questions: int, qa_pairs: List[Dict]):
        """최종 통계"""
        total_time = time.time() - self.start_time
        failed_count = self.stats['failed']
        
        print(f"\n{'='*60}")
        print(f"🎉 QA Pair Generation Completed!")
        print(f"{'='*60}")
        print(f"📊 Final Statistics:")
        print(f"  📝 Total processed: {total_questions}")
        print(f"  ✅ Generated: {len(qa_pairs)}")
        print(f"  ❌ Failed: {failed_count}")
        print(f"  📈 Success rate: {(len(qa_pairs)/total_questions)*100:.1f}%")
        print(f"  ⏱️ Total time: {total_time/60:.1f} minutes")
        print(f"  ⚡ Avg time per pair: {total_time/total_questions:.2f}s")
        print(f"  🚀 Throughput: {total_questions*60/total_time:.1f} pairs/minute")


# 추가 최적화: 커넥션 풀링을 위한 LLM 클래스 확장
class OptimizedLLM(LLM):
    def __init__(self, model_name: str = "gpt-3.5-turbo", max_connections: int = 10):
        super().__init__(model_name)
        self.max_connections = max_connections
        # OpenAI 클라이언트의 커넥션 풀 설정 (실제 구현은 LLM 클래스에 따라 다름)
    
    async def batch_generate(self, requests: List[Dict]) -> List[str]:
        """배치 요청 처리"""
        tasks = [
            self.generate_with_translation(**req) 
            for req in requests
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 사용 예시
# main.py에서 호출하기 위한 편의 함수들
def create_qa_generator(concurrency_limit: int = 8, batch_size: int = 100) -> 'QAPairGenerator':
    """QA Generator 인스턴스 생성"""
    return QAPairGenerator(concurrency_limit=concurrency_limit, batch_size=batch_size)

async def generate_qa_pairs_from_file(
    questions_file: str, 
    output_file: str, 
    max_pairs: int = None,
    concurrency_limit: int = 8,
    batch_size: int = 100
) -> List[Dict]:
    """파일에서 질문을 읽어 QA 쌍 생성 (main.py에서 호출용)"""
    generator = QAPairGenerator(
        concurrency_limit=concurrency_limit,
        batch_size=batch_size
    )
    
    return await generator.generate_qa_pairs(
        questions_file=questions_file,
        output_file=output_file,
        max_pairs=max_pairs
    )

# 사용 예시 및 테스트용
async def main():
    # 기본 설정
    generator = QAPairGenerator(
        concurrency_limit=8,  # 동시 실행 수 (API 제한에 맞게 조정)
        batch_size=100        # 배치 크기
    )
    
    qa_pairs = await generator.generate_qa_pairs(
        questions_file="questions.json",
        output_file="outputs/qa_pairs.json",
        max_pairs=1000
    )
    
    print(f"Generated {len(qa_pairs)} QA pairs")

if __name__ == "__main__":
    asyncio.run(main())