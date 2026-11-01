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
import re
import ollama
import chromadb
import os
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from ollama import chat

DB_PATH="./book-db"
default = "llama3.2"
embedder = "nomic-embed-text"
model=""
indexer=""
messages = []


tools = [{
    "type": "function",
    "function": {
        "name": "search_book",
        "description": "Search the selected book for passages relevant to a question.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in the book",
                }
            },
            "required": ["query"],
        },
    },
}]



def style(text, *codes):
    if not sys.stdout.isatty() or not sys.stdin.isatty() or os.environ.get("NO_COLOR"):
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"



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
    indexer = input("Please pick a parser model: ").strip()
    if not indexer or indexer == "":
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
        text = pages
    elif suffix == ".epub":
        book = epub.read_epub(str(path))
        sections = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            sections.append(soup.get_text(" ", strip=True))
        text = sections
    elif suffix in {".txt", ".md"}:
        txt = path.read_text(encoding="utf-8")
        paras = re.split(r"\n\s*\n", text.strip())
        largePara = ""
        i = 0
        for para in paras:
            largePara = largePara + para
            i = i + 1
            if i % 5 == 0:
                text.append(largePara)
                largePara = ""
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    return text



def initChroma():
    client = chromadb.PersistentClient(path=DB_PATH)
    ollama_ef = OllamaEmbeddingFunction(
        url="http://localhost:11434",
        model_name=embedder,
    )
    collection = client.get_or_create_collection(name="books-ollama", embedding_function=ollama_ef)
    return client, collection



def insertIntoChroma(filepath, text, client, collection):
    bookName = extractFilename(filepath)
    bookId = random.randint(1, 2147483647)
    chunks = text
    ids = []
    metadatas = []
    batch_size = 32
    for i in range(len(chunks)):
        id = f"{bookId}-{i}"
        metadata = {"book": bookName, "page": i, "chapter": "none"}
        ids.append(id)
        metadatas.append(metadata)
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=chunks[start:end],
            metadatas=metadatas[start:end],
        )
    # saved = collection.get(ids=ids, include=["documents", "metadatas"])
    # matches = (
    #     saved["ids"] == ids
    #     and saved["documents"] == chunks
    #     and saved["metadatas"] == metadatas
    # )
    # print(f"DB write {'OK' if matches else 'FAILED'}: {bookName}")
    # print(chunks[0])
    # print(chunks[1])



def queryChroma(collection, query, book):
    qOb = {
        "query_texts": query,
        "n_results": 5,
        "where": {"book" : book},
        "include":["documents", "metadatas", "distances"]
    }
    results = collection.query(query_texts=qOb["query_texts"], n_results=qOb["n_results"], where=qOb["where"], include=qOb["include"])
    return results



def chatWithLLM(client, collection, book):
    print()
    print(style("  BOOK COMPANION", "1", "36"))
    print(f"  Reading: {style(book, '1')}")
    print("  Ask a question about this book. Press Ctrl+C to exit.")
    while True:
        query = input(f"\n{style('You', '1', '36')} > ")
        msg = {
            "role" : "user",
            "content": query
        }
        messages.append(msg)
        res = chat(
            model=default,
            messages=messages,
            tools=tools
        )
        while res.message.tool_calls:
            messages.append(res.message)
            for tool_call in res.message.tool_calls:
                if tool_call.function.name != "search_book":
                    raise ValueError(f"Unknown tool: {tool_call.function.name}")
                search_query = tool_call.function.arguments["query"]
                results = queryChroma(collection, search_query, book)
                documents = results["documents"][0]
                tool_result = "\n\n".join(documents) if documents else "No matching passages found."
                messages.append({"role":"tool", "content": tool_result})
            res = chat(model=default, messages=messages, tools=tools)
        resText = res.message.content
        resp = {
            "role" : "LLM",
            "content": resText
        }
        messages.append(resp)
        print(f"\n{style('BOOK COMPANION > ', '1', '32')}")
        print(style("─" * 48, "2"))
        print(resText)



def main(filepath):
    #fetchModels()
    dbPath = DB_PATH
    client, collection = initChroma()
    book = extractFilename(filepath)
    text = extractText(filepath)
    insertIntoChroma(filepath, text, client, collection)
    chatWithLLM(client, collection, book)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to book file")
    parser.add_argument("--setup", action="store_true")
    args = parser.parse_args()
    if(args.setup): fetchModels()
    main(args.filepath)

# TODO: visible working state, streamed replies, improved prompt history and answer formatting. 