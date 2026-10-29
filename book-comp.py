import subprocess
import shutil
import sys
import argparse
import random
import ebooklib
from pathlib import Path
from pypdf import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup
import ollama
import chromadb

DB_PATH="./book-db"
default = "llama3.2"
embedder = "nomic-embed-text"
model=""
indexer=""

def fetchModels():
    ollama_path = shutil.which("ollama")
    result = ""
    if not ollama_path:
        print("Ollama not found, please install it first")
        sys.exit()
    # fetching model to read
    model = input("Please pick an open source model: ").strip()
    if not model:
        print("Using default model........")
        model = default
    result = subprocess.run(["ollama", "pull", model])
    if not result:
        print("Unable to pull model.")
        sys.exit()
    # fetching parser model
    if not model == default:
        indexer = input("Please pick a parser model: ").strip()
    if not indexer or model == default:
        print("Using default embedder.........")
        indexer = embedder
    result = subprocess.run(["ollama", "pull", embedder])
    if not result:
        print("Unable to pull indexer.")
        sys.exit()
    return result

def extractFilename(filepath):
    path = Path(filepath)
    filename = path.name
    return filename

def extractText(filepath):
    path = Path(filepath)
    suffix = path.suffix.lower()
    text = []
    if suffix == ".pdf":
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            txt = page.extract_text()
            pages.append(txt)
        text = "\n\n".join(pages)
    elif suffix == ".epub":
        book = epub.read_epub(str(path))
        sections = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            sections.append(soup.get_text(" ", strip=True))
            text = "\n\n".join(sections)
    elif suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    return text


def initChroma():
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name="books")
    return client, collection


def insertIntoChroma(filepath, text, client, collection):
    bookName = extractFilename(filepath)
    bookId = random.randint(1, 2147483647)
    chunks = [text]
    ids = []
    metadatas = []
    for i in range(len(chunks)):
        id = f"{bookId}-{i}"
        metadata = {"book": bookName, "chunk": i}
        ids.append(id)
        metadatas.append(metadata)
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    # saved = collection.get(ids=ids, include=["documents", "metadatas"])
    # matches = (
    #     saved["ids"] == ids
    #     and saved["documents"] == chunks
    #     and saved["metadatas"] == metadatas
    # )
    # print(f"DB write {'OK' if matches else 'FAILED'}: {bookName}")
    # print(chunks[0])


def main(filepath):
    #fetchModels()
    dbPath = DB_PATH
    client, collection = initChroma()
    text = extractText(filepath)
    insertIntoChroma(filepath, text, client, collection)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to book file")
    args = parser.parse_args()
    main(args.filepath)

