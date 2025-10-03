from fastapi import Request

from quote_consumer.candle_processor import CandleBuffer


def get_in_memory_storage(request: Request) -> CandleBuffer:
    return request.app.state.in_memory_storage
