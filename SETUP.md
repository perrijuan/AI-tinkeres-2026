# Como rodar o SafraViva localmente

## Pré-requisitos

- Python 3.10 ou superior
- Node.js 18 ou superior e npm

---

## Primeira vez

### Backend

**Ubuntu/Debian**
```bash
sudo apt install python3-venv python3-pip
```

**macOS (Homebrew)**
```bash
brew install python
```

Depois, independente do sistema:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Rodando depois da primeira vez

Abra dois terminais.

**Terminal 1 — Backend**

```bash
cd backend
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uvicorn main:app --reload
```

Disponível em: http://localhost:8000

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

Disponível em: http://localhost:5173
