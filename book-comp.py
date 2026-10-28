import subprocess
import shutil
import sys

def fetchModels():
    ollama_path = shutil.which("ollama")
    default = "llama3.2"
    embedder = "nomic-embed-text"
    result = ""
    if not ollama_path:
        print("Ollama not found, please install it first")
        sys.exit()
    # fetching model to read
    model = input("Please pick an open source model: ").strip()
    if not model:
        print("Using default model")
        model = default
    result = subprocess.run(["ollama", "pull", model])
    if not result:
        print("Unable to pull model.")
        sys.exit()
    # fetching parser model
    indexer = input("Please pick a parser model: ").strip()
    if not indexer or model == default:
        print("Using default embedder")
        indexer = embedder
    result = subprocess.run(["ollama", "pull", embedder])
    if not result:
        print("Unable to pull indexer.")
        sys.exit()
    return result


def main():
    fetchModels()

main()

