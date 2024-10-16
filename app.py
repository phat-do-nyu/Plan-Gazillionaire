import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, Enum, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from typing import Optional
from datetime import date

# Load environment variables from .env
load_dotenv()

# Database Setup
DATABASE_URL = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Initialize FastAPI app
app = FastAPI()

# SQLAlchemy Models
class BetDescription(Base):
    __tablename__ = 'bet_description'
    bet_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    expiration_date = Column(Date, nullable=False)
    website = Column(String(255))
    status = Column(Enum('open', 'closed'))
    is_arbitrage = Column(Enum('yes', 'no'))

class ArbitrageOpportunities(Base):
    __tablename__ = 'arbitrage_opportunities'
    arb_id = Column(Integer, primary_key=True, index=True)
    bet_id1 = Column(Integer, ForeignKey('bet_description.bet_id'))
    bet_id2 = Column(Integer, ForeignKey('bet_description.bet_id'))
    timestamp = Column(Date)
    profit = Column(Numeric)

# Create all tables in the database
Base.metadata.create_all(bind=engine)

# Pydantic Models (for validation and serialization)
class BetDescriptionBase(BaseModel):
    name: str
    expiration_date: date
    website: Optional[str] = None
    status: Optional[str] = None
    is_arbitrage: Optional[str] = None

class BetDescriptionCreate(BetDescriptionBase):
    pass

class BetDescriptionResponse(BetDescriptionBase):
    bet_id: int

    class Config:
        orm_mode = True

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD Operations for Bet Description

@app.get("/api/v1/bets", response_model=list[BetDescriptionResponse])
def get_bets(db: Session = Depends(get_db)):
    bets = db.query(BetDescription).all()
    return bets

@app.get("/api/v1/bets/{bet_id}", response_model=BetDescriptionResponse)
def get_bet(bet_id: int, db: Session = Depends(get_db)):
    bet = db.query(BetDescription).filter(BetDescription.bet_id == bet_id).first()
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    return bet

@app.post("/api/v1/bets", response_model=BetDescriptionResponse)
def create_bet(bet: BetDescriptionCreate, db: Session = Depends(get_db)):
    db_bet = BetDescription(
        name=bet.name,
        expiration_date=bet.expiration_date,
        website=bet.website,
        status=bet.status,
        is_arbitrage=bet.is_arbitrage
    )
    db.add(db_bet)
    db.commit()
    db.refresh(db_bet)
    return db_bet

@app.put("/api/v1/bets/{bet_id}", response_model=BetDescriptionResponse)
def update_bet(bet_id: int, bet: BetDescriptionCreate, db: Session = Depends(get_db)):
    db_bet = db.query(BetDescription).filter(BetDescription.bet_id == bet_id).first()
    if not db_bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    db_bet.name = bet.name
    db_bet.expiration_date = bet.expiration_date
    db_bet.website = bet.website
    db_bet.status = bet.status
    db_bet.is_arbitrage = bet.is_arbitrage
    db.commit()
    return db_bet

@app.delete("/api/v1/bets/{bet_id}", response_model=dict)
def delete_bet(bet_id: int, db: Session = Depends(get_db)):
    db_bet = db.query(BetDescription).filter(BetDescription.bet_id == bet_id).first()
    if not db_bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    db.delete(db_bet)
    db.commit()
    return {"message": "Bet deleted"}

# CRUD Operations for Arbitrage Opportunities

class ArbitrageOpportunitiesBase(BaseModel):
    bet_id1: int
    bet_id2: int
    timestamp: Optional[date] = None
    profit: Optional[float] = None

class ArbitrageOpportunitiesCreate(ArbitrageOpportunitiesBase):
    pass

class ArbitrageOpportunitiesResponse(ArbitrageOpportunitiesBase):
    arb_id: int

    class Config:
        orm_mode = True

@app.get("/api/v1/arbitrage", response_model=list[ArbitrageOpportunitiesResponse])
def get_arbitrage_opportunities(db: Session = Depends(get_db)):
    opportunities = db.query(ArbitrageOpportunities).all()
    return opportunities

@app.get("/api/v1/arbitrage/{arb_id}", response_model=ArbitrageOpportunitiesResponse)
def get_arbitrage_opportunity(arb_id: int, db: Session = Depends(get_db)):
    opportunity = db.query(ArbitrageOpportunities).filter(ArbitrageOpportunities.arb_id == arb_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity

@app.post("/api/v1/arbitrage", response_model=ArbitrageOpportunitiesResponse)
def create_arbitrage_opportunity(opportunity: ArbitrageOpportunitiesCreate, db: Session = Depends(get_db)):
    db_opportunity = ArbitrageOpportunities(
        bet_id1=opportunity.bet_id1,
        bet_id2=opportunity.bet_id2,
        timestamp=opportunity.timestamp,
        profit=opportunity.profit
    )
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity

@app.put("/api/v1/arbitrage/{arb_id}", response_model=ArbitrageOpportunitiesResponse)
def update_arbitrage_opportunity(arb_id: int, opportunity: ArbitrageOpportunitiesCreate, db: Session = Depends(get_db)):
    db_opportunity = db.query(ArbitrageOpportunities).filter(ArbitrageOpportunities.arb_id == arb_id).first()
    if not db_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    db_opportunity.bet_id1 = opportunity.bet_id1
    db_opportunity.bet_id2 = opportunity.bet_id2
    db_opportunity.timestamp = opportunity.timestamp
    db_opportunity.profit = opportunity.profit
    db.commit()
    return db_opportunity

@app.delete("/api/v1/arbitrage/{arb_id}", response_model=dict)
def delete_arbitrage_opportunity(arb_id: int, db: Session = Depends(get_db)):
    db_opportunity = db.query(ArbitrageOpportunities).filter(ArbitrageOpportunities.arb_id == arb_id).first()
    if not db_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    db.delete(db_opportunity)
    db.commit()
    return {"message": "Opportunity deleted"}

# Main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)