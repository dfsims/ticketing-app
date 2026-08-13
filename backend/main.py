import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from contextlib import asynccontextmanager

# Import database and models
from backend.db import db
from backend.models import TicketCreate, TicketUpdate, TicketResponse, MessageCreate, MessageResponse

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- Application Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup: Initialize database connection
    logger.info("Initializing database connection...")
    try:
        await db.initialize()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Continue without database - app will still serve static content
    
    yield
    
    # Shutdown: Close database connection
    logger.info("Closing database connection...")
    await db.close()

app = FastAPI(title="Ticketing System App", lifespan=lifespan)

# --- API Routes ---
@app.get("/api/hello")
async def hello():
    logger.info("Accessed /api/hello")
    return {"message": "Hello from FastAPI!"}

@app.get("/api/health")
async def health_check():
    logger.info("Health check at /api/health")
    return {"status": "healthy"}

@app.get("/api/data")
async def get_data():
    logger.info("Data requested at /api/data")
    data = [{"x": x, "y": 2 ** x} for x in range(30)]
    return {
        "data": data,
        "title": "Hello world!",
        "x_title": "Apps",
        "y_title": "Fun with data"
    }

# --- Ticket API Routes ---
@app.post("/api/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(ticket: TicketCreate):
    """Create a new ticket"""
    logger.info(f"Creating new ticket: {ticket.title}")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = """
    INSERT INTO tickets (title, status, created_by)
    VALUES ($1, $2, $3)
    RETURNING ticket_id, title, status, created_by, created_at
    """
    
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            query,
            ticket.title,
            'open',
            ticket.created_by
        )
        
        return dict(row)

@app.get("/api/tickets", response_model=List[TicketResponse])
async def list_tickets(status: str = None):
    """List all tickets with optional status filter"""
    logger.info(f"Listing tickets (status={status})")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    
    if status:
        params.append(status)
        query += f" AND status = ${len(params)}"
    
    query += " ORDER BY created_at DESC"
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int):
    """Get a specific ticket by ID"""
    logger.info(f"Retrieving ticket {ticket_id}")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = "SELECT * FROM tickets WHERE ticket_id = $1"
    
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(query, ticket_id)
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        return dict(row)

@app.patch("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(ticket_id: int, ticket_update: TicketUpdate):
    """Update a ticket"""
    logger.info(f"Updating ticket {ticket_id}")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Build dynamic update query based on provided fields
    update_fields = []
    params = []
    param_count = 1
    
    if ticket_update.title is not None:
        update_fields.append(f"title = ${param_count}")
        params.append(ticket_update.title)
        param_count += 1
    
    if ticket_update.status is not None:
        update_fields.append(f"status = ${param_count}")
        params.append(ticket_update.status)
        param_count += 1
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Add ticket_id as last parameter
    params.append(ticket_id)
    
    query = f"""
    UPDATE tickets 
    SET {', '.join(update_fields)}
    WHERE ticket_id = ${param_count}
    RETURNING ticket_id, title, status, created_by, created_at
    """
    
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(query, *params)
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        return dict(row)

@app.delete("/api/tickets/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: int):
    """Delete a ticket"""
    logger.info(f"Deleting ticket {ticket_id}")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = "DELETE FROM tickets WHERE ticket_id = $1 RETURNING ticket_id"
    
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(query, ticket_id)
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

@app.get("/api/tickets/stats/summary")
async def get_ticket_stats():
    """Get ticket statistics summary"""
    logger.info("Retrieving ticket statistics")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = """
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'open') as open,
        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
        COUNT(*) FILTER (WHERE status = 'resolved') as resolved,
        COUNT(*) FILTER (WHERE status = 'closed') as closed
    FROM tickets
    """
    
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(query)
        return dict(row)

# --- Message API Routes ---
@app.post("/api/tickets/{ticket_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(ticket_id: int, message: MessageCreate):
    """Add a message to a ticket"""
    logger.info(f"Adding message to ticket {ticket_id}")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Verify ticket exists
    async with db.pool.acquire() as conn:
        ticket_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM tickets WHERE ticket_id = $1)",
            ticket_id
        )
        
        if not ticket_exists:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        query = """
        INSERT INTO ticket_messages (ticket_id, message_text, author)
        VALUES ($1, $2, $3)
        RETURNING message_id, ticket_id, message_text, author, created_at
        """
        
        row = await conn.fetchrow(query, ticket_id, message.message, message.author)
        return dict(row)

@app.get("/api/tickets/{ticket_id}/messages", response_model=List[MessageResponse])
async def get_ticket_messages(ticket_id: int):
    """Get all messages for a ticket"""
    logger.info(f"Retrieving messages for ticket {ticket_id}")
    
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = """
    SELECT message_id, ticket_id, message_text, author, created_at 
    FROM ticket_messages 
    WHERE ticket_id = $1 
    ORDER BY created_at ASC
    """
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(query, ticket_id)
        return [dict(row) for row in rows]

# --- Static Files Setup ---
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# --- Catch-all for React Routes ---
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    index_html = os.path.join(static_dir, "index.html")
    if os.path.exists(index_html):
        logger.info(f"Serving React frontend for path: /{full_path}")
        return FileResponse(index_html)
    logger.error("Frontend not built. index.html missing.")
    raise HTTPException(
        status_code=404,
        detail="Frontend not built. Please run 'npm run build' first."
    )