"""Pydantic v2 domain models for estate-intake."""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum

# Configure all models to forbid extra fields
class BaseConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

# Enums as Literals
Condition = Literal[
    "For Parts or Not Working",
    "Acceptable", 
    "Good",
    "Very Good",
    "Excellent", 
    "Open Box",
    "New (Other)",
    "New"
]

CategoryHint = Literal[
    "vehicle",
    "trading_card", 
    "book",
    "apparel",
    "electronics",
    "generic"
]

Strategy = Literal["quick", "fair", "max"]

# Core Models
class Media(BaseConfigModel):
    source: Literal["file", "url", "data_url"]
    path: Optional[str] = None
    url: Optional[str] = None
    data_url: Optional[str] = None
    alt: Optional[str] = None

class Measurements(BaseConfigModel):
    length_in: Optional[float] = None
    width_in: Optional[float] = None
    height_in: Optional[float] = None
    weight_oz: Optional[float] = None

class Pricing(BaseConfigModel):
    ask_price_usd: Optional[float] = None
    floor_price_usd: Optional[float] = None
    auction: bool = False
    auction_days: int = 7
    best_offer: bool = True

class Shipping(BaseConfigModel):
    policy_id: Optional[str] = None
    service_hint: Optional[str] = None
    handling_days: int = 1

# Category Specifics
class VehicleSpecifics(BaseConfigModel):
    vin: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None
    body_type: Optional[str] = None
    mileage: Optional[int] = None
    transmission: Optional[str] = None
    drivetrain: Optional[str] = None
    fuel_type: Optional[str] = None
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    title_status: Optional[str] = None

class TradingCardSpecifics(BaseConfigModel):
    sport: Optional[str] = None
    year: Optional[int] = None
    set_name: Optional[str] = None
    player: Optional[str] = None
    card_number: Optional[str] = None
    parallel_or_variant: Optional[str] = None
    grade: Optional[str] = None
    grader: Optional[str] = None
    rookie: Optional[bool] = None
    autograph: Optional[bool] = None
    memorabilia: Optional[bool] = None

class BookSpecifics(BaseConfigModel):
    author: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[int] = None
    edition: Optional[str] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    format: Optional[str] = None
    language: Optional[str] = None
    series: Optional[str] = None
    code_or_mpn: Optional[str] = None

class ApparelSpecifics(BaseConfigModel):
    brand: Optional[str] = None
    gender: Optional[str] = None
    size: Optional[str] = None
    size_type: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    style: Optional[str] = None

class ElectronicsSpecifics(BaseConfigModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    mpn: Optional[str] = None
    storage_capacity: Optional[str] = None
    color: Optional[str] = None

class GenericSpecifics(BaseConfigModel):
    aspects: Dict[str, Union[str, int, float, bool]] = {}

# Main Item Model
class Item(BaseConfigModel):
    # Identity
    sku: str
    title: str
    subtitle: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    category_hint: CategoryHint
    
    # Condition
    condition_grade: Condition
    condition_notes: Optional[str] = None
    
    # Media
    photos: List[Media] = []
    measurements: Optional[Measurements] = None
    
    # Attributes
    attributes: Dict[str, Union[str, int, float, bool]] = {}
    
    # Category specifics
    vehicle: Optional[VehicleSpecifics] = None
    card: Optional[TradingCardSpecifics] = None
    book: Optional[BookSpecifics] = None
    apparel: Optional[ApparelSpecifics] = None
    electronics: Optional[ElectronicsSpecifics] = None
    generic: Optional[GenericSpecifics] = None
    
    # Listing metadata
    pricing: Optional[Pricing] = None
    shipping: Optional[Shipping] = None
    item_specifics: Dict[str, List[str]] = {}
    
    # Lot support
    is_lot: bool = False
    lot_children: List["Item"] = []

class LotMetadata(BaseConfigModel):
    lot_id: str
    list_strategy: Literal["individual", "lot", "mixed"]
    location_zip: Optional[str] = None
    notes: Optional[str] = None

class IntakeBundle(BaseConfigModel):
    case_id: str
    lot_metadata: LotMetadata
    items: List[Item] = []

# Comps & Reports
class CompStats(BaseConfigModel):
    sold_count: int
    active_count: int
    sell_through_pct: float
    median_sold: float
    p10_sold: float
    p90_sold: float
    avg_dom_days: float

class StrategyQuote(BaseConfigModel):
    strategy: Strategy
    ask_price: float
    est_dom_days: int
    fee_pct: float
    est_fees: float
    est_shipping_cost: float
    est_net_proceeds: float

class ItemReport(BaseConfigModel):
    sku: str
    title: str
    category_hint: CategoryHint
    condition_grade: Condition
    comp: CompStats
    quotes: List[StrategyQuote]
    recommendation: Strategy
    notes: Optional[str] = None

class EstateRollup(BaseConfigModel):
    totals: Dict[str, Any]  # {quick: {gross, net, avg_dom}, fair: {...}, max: {...}}
    items: List[ItemReport]
