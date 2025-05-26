import json
import random
import time
from typing import List, Dict
from tqdm import tqdm
from collections import defaultdict
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rag import RAG  # Relative import from parent directory
from llm import LLM  # Relative import from parent directory

class QAPairGenerator:
    def __init__(self):
        self.rag = RAG()
        self.llm = LLM(model_name="gpt-3.5-turbo")
        self.stats = defaultdict(int)
        self.start_time = None
        
    async def generate_qa_pairs(self, questions_file: str, output_file: str, max_pairs: int = None):
        """질문 파일을 읽어서 QA 쌍 생성"""
        self.start_time = time.time()
        
        # 질문 로드
        print("📖 Loading questions...")
        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions = data['questions']
        total_questions = len(questions)
        
        if max_pairs:
            questions = random.sample(questions, min(max_pairs, len(questions)))
            print(f"🎲 Randomly selected {len(questions)} questions from {total_questions}")
        
        print(f"🎯 Target: Generate {len(questions)} QA pairs")
        
        # 나라별, 토픽별 통계 준비
        country_topic_stats = defaultdict(lambda: defaultdict(int))
        for q in questions:
            country_topic_stats[q['country']][q['topic']] += 1
        
        # 통계 출력
        print("\n📊 Questions distribution:")
        for country in sorted(country_topic_stats.keys()):
            topics_info = []
            for topic in sorted(country_topic_stats[country].keys()):
                count = country_topic_stats[country][topic]
                topics_info.append(f"{topic}: {count}")
            print(f"  {country}: {', '.join(topics_info)}")
        
        qa_pairs = []
        failed_questions = []
        
        # 전체 진행도 바
        print(f"\n🚀 Starting QA pair generation...")
        overall_pbar = tqdm(total=len(questions), desc="Overall Progress", 
                           position=0, leave=True, 
                           bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
        
        # 현재 처리 중인 정보를 위한 진행도 바
        current_pbar = tqdm(total=1, desc="Current", position=1, leave=False,
                           bar_format='Current: {desc}')
        
        for i, q_data in enumerate(questions):
            country = q_data['country']
            topic = q_data['topic']
            question_id = q_data['id']
            
            # 현재 처리 중인 질문 정보 업데이트
            current_pbar.set_description(f"{country} - {topic}")
            current_pbar.refresh()
            
            if topic == 'immigration':
                topic = 'immigration_regulations'
            elif topic == 'safety':
                topic = 'immigration_safety'
            
            try:
                # RAG로 컨텍스트 검색
                context, references = self.rag.search_with_translation(
                    query=q_data['question'],
                    country=country.lower(),
                    doc_type=topic + "_info"
                )
                
                # LLM으로 답변 생성
                answer = await self.llm.generate_with_translation(
                    query=q_data['question'],
                    context=context,
                    references=references,
                    translate_to_korean=False
                )
                
                qa_pairs.append({
                    "question": q_data['question'],
                    "answer": answer,
                    "context": context[:1000]
                })
                
                self.stats['success'] += 1
                self.stats[f'success_{country}'] += 1
                self.stats[f'success_{topic}'] += 1
                
            except Exception as e:
                failed_questions.append({
                    "question_id": question_id,
                    "country": country,
                    "topic": topic,
                    "question": q_data['question'],
                    "error": str(e)
                })
                
                self.stats['failed'] += 1
                self.stats[f'failed_{country}'] += 1
                self.stats[f'failed_{topic}'] += 1
                
                # 에러가 너무 많이 발생하면 경고
                if self.stats['failed'] > len(questions) * 0.1:  # 10% 이상 실패
                    print(f"\n⚠️  Warning: High failure rate ({self.stats['failed']}/{i+1})")
            
            # 진행도 업데이트
            overall_pbar.update(1)
            
            # 중간 결과 출력 (매 100개마다)
            if (i + 1) % 100 == 0:
                self._print_intermediate_stats(i + 1, len(questions))
            
            # 중간 저장 (매 500개마다)
            if (i + 1) % 500 == 0:
                self._save_intermediate_results(qa_pairs, output_file, i + 1)
        
        # 진행도 바 정리
        current_pbar.close()
        overall_pbar.close()
        
        # 최종 통계 출력
        self._print_final_stats(len(questions), qa_pairs, failed_questions)
        
        return qa_pairs

    def _print_intermediate_stats(self, current: int, total: int):
        """중간 통계 출력"""
        elapsed_time = time.time() - self.start_time
        avg_time_per_pair = elapsed_time / current
        estimated_remaining = avg_time_per_pair * (total - current)
        
        success_rate = (self.stats['success'] / current) * 100
        
        print(f"\n📈 Progress Update ({current}/{total}):")
        print(f"  ✅ Success: {self.stats['success']} ({success_rate:.1f}%)")
        print(f"  ❌ Failed: {self.stats['failed']}")
        print(f"  ⏱️  Avg time per pair: {avg_time_per_pair:.2f}s")
        print(f"  ⏰ Estimated remaining: {estimated_remaining/60:.1f} minutes")

    def _save_intermediate_results(self, qa_pairs: List[Dict], output_file: str, current_count: int):
        """중간 결과 저장"""
        backup_file = f"{output_file}.backup_{current_count}"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        print(f"💾 Intermediate backup saved: {backup_file}")

    def _save_final_results(self, qa_pairs: List[Dict], failed_questions: List[Dict], output_file: str):
        """최종 결과 저장"""
        # QA pairs 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        
        # 실패한 질문들 저장
        if failed_questions:
            failed_file = output_file.replace('.json', '_failed.json')
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_questions, f, ensure_ascii=False, indent=2)
            print(f"❌ Failed questions saved to: {failed_file}")

    def _print_final_stats(self, total_questions: int, qa_pairs: List[Dict], failed_questions: List[Dict]):
        """최종 통계 출력"""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"🎉 QA Pair Generation Completed!")
        print(f"{'='*60}")
        print(f"📊 Final Statistics:")
        print(f"  📝 Total questions processed: {total_questions}")
        print(f"  ✅ Successfully generated: {len(qa_pairs)}")
        print(f"  ❌ Failed: {len(failed_questions)}")
        print(f"  📈 Success rate: {(len(qa_pairs)/total_questions)*100:.1f}%")
        print(f"  ⏱️  Total time: {total_time/60:.1f} minutes")
        print(f"  ⚡ Average time per pair: {total_time/total_questions:.2f}s")
        
        # 나라별 성공률
        print(f"\n🌍 Success rate by country:")
        countries = set([qa['country'] for qa in qa_pairs])
        for country in sorted(countries):
            success_count = sum(1 for qa in qa_pairs if qa['country'] == country)
            failed_count = sum(1 for fq in failed_questions if fq['country'] == country)
            total_country = success_count + failed_count
            success_rate = (success_count / total_country * 100) if total_country > 0 else 0
            print(f"  {country}: {success_count}/{total_country} ({success_rate:.1f}%)")
        
        # 토픽별 성공률
        print(f"\n📋 Success rate by topic:")
        topics = set([qa['topic'] for qa in qa_pairs])
        for topic in sorted(topics):
            success_count = sum(1 for qa in qa_pairs if qa['topic'] == topic)
            failed_count = sum(1 for fq in failed_questions if fq['topic'] == topic)
            total_topic = success_count + failed_count
            success_rate = (success_count / total_topic * 100) if total_topic > 0 else 0
            print(f"  {topic}: {success_count}/{total_topic} ({success_rate:.1f}%)")
        
        # 결과 저장
        self._save_final_results(qa_pairs, failed_questions, "./outputs/qa_pairs.json")
        print(f"\n💾 Results saved to: ./outputs/qa_pairs.json")
        if failed_questions:
            print(f"❌ Failed questions details saved to: ./outputs/qa_pairs_failed.json")