from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from vectorstore import get_vectorstore

def load_docs(folder: str = "knowledge"):
    docs = []
    for p in Path(folder).glob("**/*"):
        if p.suffix.lower() in {".md", ".txt"}:
            docs.append(Document(
                page_content=p.read_text(encoding="utf-8"),
                metadata={"source": str(p)},
            ))
    return docs

def main():
    raw = load_docs()
    print(f"读到 {len(raw)} 篇文档")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,      # 每块约 800 字符
        chunk_overlap=100,   # 块间重叠,避免把一句话切断
    )
    chunks = splitter.split_documents(raw)
    print(f"切成 {len(chunks)} 个 chunk")

    vs = get_vectorstore()
    vs.add_documents(chunks)   # 自动落盘,不用再 .persist()
    print("灌库完成 → ./chroma_db")

if __name__ == "__main__":
    main()