"""Model configurations and settings"""

from peft import TaskType


MODEL_CONFIGS = {
    "google/flan-t5-small": {
        "targets": ["q", "v"],
        "task_type": TaskType.SEQ_2_SEQ_LM,
        "is_seq2seq": True
    },
    "google/flan-t5-base": {
        "targets": ["q", "v"],
        "task_type": TaskType.SEQ_2_SEQ_LM,
        "is_seq2seq": True
    },
    "microsoft/phi-2": {
        "targets": ["Wqkv", "fc1", "fc2"],
        "task_type": TaskType.CAUSAL_LM,
        "is_seq2seq": False
    },
    "facebook/opt-125m": {
        "targets": ["q_proj", "v_proj"],
        "task_type": TaskType.CAUSAL_LM,
        "is_seq2seq": False
    },
    "facebook/opt-350m": {
        "targets": ["q_proj", "v_proj"],
        "task_type": TaskType.CAUSAL_LM,
        "is_seq2seq": False
    },
    "EleutherAI/pythia-70m": {
        "targets": ["query_key_value"],
        "task_type": TaskType.CAUSAL_LM,
        "is_seq2seq": False
    },
    "EleutherAI/pythia-160m": {
        "targets": ["query_key_value"],
        "task_type": TaskType.CAUSAL_LM,
        "is_seq2seq": False
    }
}

DEFAULT_CONFIG = {
    "targets": ["q_proj", "v_proj"],
    "task_type": TaskType.CAUSAL_LM,
    "is_seq2seq": False
}