import argparse
import asyncio
from question_generator import QuestionGenerator
from qa_pair_generator import QAPairGenerator, generate_qa_pairs_from_file
from model_trainer import ModelTrainer

async def main():
    parser = argparse.ArgumentParser(description='Fine-tuning pipeline')
    parser.add_argument('--step', choices=['questions', 'qa_pairs', 'train', 'all'], 
                       default='all', help='Which step to run')
    parser.add_argument('--questions_per_topic', type=int, default=1000,
                       help='Number of questions per country per topic')
    parser.add_argument('--max_qa_pairs', type=int, default=None,
                       help='Maximum number of QA pairs to generate')
    parser.add_argument('--model_name', type=str, default='facebook/opt-125m',
                       help='Model name for fine-tuning')
    parser.add_argument('--use_qlora', action='store_true',
                       help='Use QLoRA for training')
    parser.add_argument('--output_dir', type=str, default='./outputs',
                       help='Output directory')
    parser.add_argument('--concurrency_limit', type=int, default=8,
                       help='Maximum concurrent API calls')
    parser.add_argument('--batch_size', type=int, default=50,
                       help='Batch size for processing questions')
    args = parser.parse_args()
    
    if args.step in ['questions', 'all']:
        print("=== Generating Questions ===")
        generator = QuestionGenerator()
        questions = generator.generate_questions(args.questions_per_topic)
        questions_file = f"{args.output_dir}/questions.json"
        generator.save_questions(questions, questions_file)
        print(f"Generated {len(questions)} questions")
    
    if args.step in ['qa_pairs', 'all']:
        print("=== Generating QA Pairs ===")
        try:
            # 직접 객체 생성 방법
            qa_generator = QAPairGenerator(
                concurrency_limit=args.concurrency_limit,
                batch_size=args.batch_size
            )
            
            questions_file = f"{args.output_dir}/questions.json"
            qa_pairs_file = f"{args.output_dir}/qa_pairs.json"
            qa_pairs = await qa_generator.generate_qa_pairs(questions_file, qa_pairs_file, args.max_qa_pairs)
            print(f"Generated {len(qa_pairs)} QA pairs")
        except Exception as e:
            print(f"Error in QA pair generation: {e}")
            import traceback
            traceback.print_exc()
    
    # if args.step in ['train', 'all']:
    #     print("=== Training Model ===")
    #     trainer = ModelTrainer(args.model_name, args.use_qlora)
    #     trainer.load_model()
        
    #     qa_pairs_file = f"{args.output_dir}/qa_pairs.json"
    #     model_output_dir = f"{args.output_dir}/finetuned_model"
    #     trainer.train(qa_pairs_file, model_output_dir)
    
    print("Pipeline completed!")

if __name__ == "__main__":
    asyncio.run(main())