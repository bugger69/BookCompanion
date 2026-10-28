import subprocess
import shutil
import sys
import argparse

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
    filename = filepath
    # Add processing logic to this
    return filename


def main(filepath):
    bookfile = extractFilename(filepath)
    dbPath = f"./{bookfile}"
    print(dbPath)
    #fetchModels()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to book file")
    args = parser.parse_args()
    main(args.filepath)

