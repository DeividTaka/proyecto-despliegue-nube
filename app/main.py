import os
import socket
import time
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel

# Configuración de la base de datos desde variables de entorno
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin123@db:5432/orderflow_db"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de tabla en PostgreSQL
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    product = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    handled_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Esperar brevemente si PostgreSQL aún está aceptando conexiones y crear tablas
for _ in range(5):
    try:
        Base.metadata.create_all(bind=engine)
        break
    except Exception:
        time.sleep(2)

# Instancia principal que Uvicorn busca (main:app)
app = FastAPI(title="OrderFlow Cloud", version="1.0.0")

# Dependencia de sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Esquema JSON para API REST
class OrderCreate(BaseModel):
    customer_name: str
    product: str
    amount: float

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "node": socket.gethostname()
    }

@app.get("/api/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.id.desc()).all()
    return {
        "served_by_node": socket.gethostname(),
        "total": len(orders),
        "orders": orders
    }

@app.post("/api/orders")
def create_order_api(order: OrderCreate, db: Session = Depends(get_db)):
    node_id = socket.gethostname()
    db_order = Order(
        customer_name=order.customer_name,
        product=order.product,
        amount=order.amount,
        handled_by=node_id
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.post("/orders/web")
def create_order_web(
    customer_name: str = Form(...),
    product: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    node_id = socket.gethostname()
    db_order = Order(
        customer_name=customer_name,
        product=product,
        amount=amount,
        handled_by=node_id
    )
    db.add(db_order)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/", response_class=HTMLResponse)
def dashboard(db: Session = Depends(get_db)):
    node_id = socket.gethostname()
    orders = db.query(Order).order_by(Order.id.desc()).limit(15).all()

    rows_html = ""
    for o in orders:
        rows_html += f"""
        <tr class="border-b border-slate-700 hover:bg-slate-800/60">
            <td class="py-2.5 px-4 font-mono text-slate-400">#{o.id}</td>
            <td class="py-2.5 px-4 font-medium">{o.customer_name}</td>
            <td class="py-2.5 px-4">{o.product}</td>
            <td class="py-2.5 px-4 text-emerald-400 font-semibold">${o.amount:,.2f}</td>
            <td class="py-2.5 px-4"><span class="bg-slate-700 text-xs font-mono px-2 py-1 rounded">{o.handled_by}</span></td>
        </tr>
        """

    if not rows_html:
        rows_html = """
        <tr>
            <td colspan="5" class="py-6 text-center text-slate-400">Aún no hay pedidos registrados. Crea el primero arriba.</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OrderFlow Cloud — Arquitectura Distribuida</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen font-sans">
        <div class="max-w-4xl mx-auto py-10 px-6">
            <div class="flex flex-wrap items-center justify-between gap-4 bg-slate-800 border border-slate-700 p-6 rounded-xl mb-8 shadow-lg">
                <div>
                    <h1 class="text-2xl font-bold text-white">OrderFlow Cloud</h1>
                    <p class="text-slate-400 text-sm">FastAPI + PostgreSQL + Nginx Load Balancer</p>
                </div>
                <div class="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 px-4 py-2 rounded-lg">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span class="text-sm font-mono">Nodo: <strong>{node_id}</strong></span>
                </div>
            </div>

            <div class="bg-slate-800 border border-slate-700 p-6 rounded-xl mb-8 shadow-lg">
                <h2 class="text-lg font-semibold mb-4">Registrar Nuevo Pedido</h2>
                <form action="/orders/web" method="post" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <input type="text" name="customer_name" placeholder="Cliente (ej. Ana Pérez)" required
                        class="bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm focus:outline-none focus:border-sky-500">
                    <input type="text" name="product" placeholder="Producto (ej. Laptop Pro)" required
                        class="bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm focus:outline-none focus:border-sky-500">
                    <input type="number" step="0.01" name="amount" placeholder="Monto ($)" required
                        class="bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm focus:outline-none focus:border-sky-500">
                    <button type="submit"
                        class="bg-sky-600 hover:bg-sky-500 text-white font-medium rounded-lg px-4 py-2 text-sm transition">
                        Guardar en BD
                    </button>
                </form>
            </div>

            <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-lg">
                <div class="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                    <h2 class="text-lg font-semibold">Pedidos Persistentes en PostgreSQL</h2>
                    <span class="text-xs text-slate-400">Recarga (F5) para probar el balanceo</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-900/60 text-slate-400 uppercase text-xs">
                            <tr>
                                <th class="py-3 px-4">ID</th>
                                <th class="py-3 px-4">Cliente</th>
                                <th class="py-3 px-4">Producto</th>
                                <th class="py-3 px-4">Monto</th>
                                <th class="py-3 px-4">Atendido por</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """