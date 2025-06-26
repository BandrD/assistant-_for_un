import os
import PyPDF2
from docx import Document
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class DocumentProcessor:
    def __init__(self, chroma_path="/data/chroma"):
        try:
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            os.makedirs(chroma_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=chroma_path)
            self.collection = self.client.get_or_create_collection(name="university_docs")
            print("ChromaDB успешно инициализирован")
        except Exception as e:
            print(f"Ошибка инициализации ChromaDB: {e}")
            raise
    def extract_text(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                return ' '.join(page.extract_text() for page in pdf.pages if page.extract_text())
        elif ext == '.docx':
            doc = Document(file_path)
            return ' '.join(paragraph.text for paragraph in doc.paragraphs)
        return ""

    def process_document(self, file_path, source_id, doc_type):
        text = self.extract_text(file_path)
        if not text:
            return

        # Разбиваем на чанки (по 500 символов с перекрытием 50)
        chunk_size, overlap = 500, 50
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]
        
        # Генерируем эмбеддинги
        embeddings = self.model.encode(chunks, show_progress_bar=False)
        
        # Сохраняем в Chroma
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=[{"source_id": source_id, "doc_type": doc_type} for _ in chunks],
            ids=[f"{source_id}_{i}" for i in range(len(chunks))]
        )

if __name__ == "__main__":
    processor = DocumentProcessor()
    # Пример обработки тестового документа
    processor.process_document("data/docs/sample.pdf", "doc1", "schedule")
