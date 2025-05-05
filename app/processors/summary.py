from transformers import BartForConditionalGeneration, BartTokenizer
import torch


class BartSummarizer:
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """Инициализация модели BART для суммаризации"""
        self.tokenizer = BartTokenizer.from_pretrained(model_name)
        self.model = BartForConditionalGeneration.from_pretrained(model_name)
        
        # Проверка на доступность GPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
    
    def summarize(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """
        Суммаризация текста с помощью модели BART
        
        text: исходный текст
        max_length: максимальная длина суммаризации
        min_length: минимальная длина суммаризации
        """
        # Токенизируем текст
        inputs = self.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
        inputs = inputs.to(self.device)
        
        # Генерируем суммаризацию
        summary_ids = self.model.generate(
            inputs["input_ids"],
            num_beams=4,
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            early_stopping=True
        )
        
        # Декодируем токены обратно в текст
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        return summary
