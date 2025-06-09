import hashlib
import asyncio
import torch
from transformers import BartForConditionalGeneration, BartTokenizer
from app.utils.redis_client import redis

class BartSummarizer:
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """Инициализация модели BART для суммаризации"""
        self.tokenizer = BartTokenizer.from_pretrained(model_name)
        self.model = BartForConditionalGeneration.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    async def summarize(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30
    ) -> str:
        """
        Асинхронная суммаризация с кэшированием в Redis.
        """
        # Формируем ключ по SHA256 хэшу текста
        key = "summ:" + hashlib.sha256(text.encode()).hexdigest()

        # 1) Проверяем в кэше
        if redis:
            cached = await redis.get(key)
            if cached:
                return cached

        # 2) Генерируем суммаризацию в отдельном потоке,
        # чтобы не блокировать event loop
        summary = await asyncio.get_event_loop().run_in_executor(
            None,
            self._generate_summary,
            text,
            max_length,
            min_length
        )

        # 3) Сохраняем результат в Redis с TTL = 1 час
        if redis:
            await redis.set(key, summary, ex=3600)

        return summary

    def _generate_summary(
        self,
        text: str,
        max_length: int,
        min_length: int
    ) -> str:
        # Токенизация и генерация (синхронная часть)
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=1024,
            truncation=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        summary_ids = self.model.generate(
            inputs["input_ids"],
            num_beams=4,
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            early_stopping=True
        )
        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
