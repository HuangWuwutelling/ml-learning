from langgraph.checkpoint.memory import MemorySaver

_memory = None

def get_memory() -> MemorySaver:
    global _memory
    if _memory is None:
        _memory = MemorySaver()
    return _memory