from domain.models import Article


class FakeSource:
    def __init__(self, n):
        self.n = n

    def articles(self):
        return [Article(f"Art. {i}", f"Art. {i}. Texto {i}.") for i in range(1, self.n + 1)]


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(texts)
        return [[0.0]] * len(texts)


class FakeChat:
    def __init__(self):
        self.prompts = []

    def complete(self, system, user):
        return "termos jurídicos"

    def stream(self, system, user):
        self.prompts.append(user)
        yield "resposta"


class FakeStore:
    def __init__(self):
        self.saved = None

    def exists(self):
        return self.saved is not None

    def all(self):
        return self.saved[0]

    def save(self, articles, vectors):
        self.saved = articles, vectors

    def search(self, vector, k):
        return self.saved[0][:k]


class FakeLog:
    def __init__(self):
        self.records = []

    def record(self, question, answer, sources):
        self.records.append((question, answer, sources))
