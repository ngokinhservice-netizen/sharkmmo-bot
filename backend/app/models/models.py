import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean,
    DateTime, Text, JSON, ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    balance = Column(Float, default=0.0, nullable=False)
    total_spent = Column(Float, default=0.0, nullable=False)
    total_orders = Column(Integer, default=0, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)  # "user" or "admin"
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("PaymentTransaction", back_populates="user", cascade="all, delete-orphan")


class ProductCache(Base):
    __tablename__ = "products_cache"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image = Column(String(500), nullable=True)
    emoji = Column(String(100), nullable=True)
    product_type = Column(String(50), nullable=False)  # account, slot, upgrade_account
    category = Column(String(100), default="Khác", index=True, nullable=False)
    brand_slug = Column(String(50), index=True, nullable=True)
    
    # Pricing info
    source_price = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="VND", nullable=False)
    calculated_price = Column(Float, default=0.0, nullable=False)
    custom_price = Column(Float, nullable=True)  # Direct override price if set by admin
    custom_markup_type = Column(String(20), nullable=True)  # "percent" or "fixed"
    custom_markup_value = Column(Float, nullable=True)

    # Availability & Stock
    available_qty = Column(Integer, nullable=True)
    sold_qty = Column(Integer, default=0, nullable=False)
    promotions = Column(JSON, nullable=True)
    purchase_requirements = Column(JSON, nullable=True)

    # Flags
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String(50), index=True, nullable=False)  # "global", "category", "product"
    target_name = Column(String(255), index=True, nullable=False)  # "ALL", category name, or product_id
    markup_type = Column(String(20), default="percent", nullable=False)  # "percent" or "fixed"
    markup_value = Column(Float, default=20.0, nullable=False)  # e.g. 20 (%) or 10000 (VND)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    round_to = Column(Integer, default=1000, nullable=False)  # Rounding step
    priority = Column(Integer, default=0, nullable=False)  # Higher priority applied first
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    product_id = Column(String(100), index=True, nullable=False)
    product_name = Column(String(255), nullable=False)
    product_type = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    
    # Financials
    source_price = Column(Float, nullable=False)  # Source price per unit at purchase
    sell_price = Column(Float, nullable=False)    # Total charged selling price
    profit = Column(Float, default=0.0, nullable=False)  # sell_price - (source_price * quantity)
    
    # Inputs required for specific types
    customer_email = Column(String(255), nullable=True)
    customer_accounts = Column(JSON, nullable=True)
    slot_months = Column(Integer, nullable=True)

    # Status: pending, processing, completed, failed, refunded
    status = Column(String(50), default="pending", index=True, nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    canboso_order_code = Column(String(100), nullable=True)
    delivery_data = Column(JSON, nullable=True)  # accounts list with user, password, etc.
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="orders")
    payments = relationship("PaymentTransaction", back_populates="order")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_code = Column(String(64), unique=True, index=True, nullable=False)  # e.g. NAP123456
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="vietqr", nullable=False)  # vietqr, sepay, manual
    bank_code = Column(String(20), default="MB", nullable=False)
    account_number = Column(String(50), nullable=False)
    transfer_content = Column(String(100), unique=True, index=True, nullable=False)  # e.g. SHARK NAP 123456
    
    # Status: pending, completed, rejected, expired
    status = Column(String(50), default="pending", index=True, nullable=False)
    gateway_tx_id = Column(String(100), nullable=True, index=True)
    gateway_data = Column(JSON, nullable=True)
    confirmed_by = Column(String(100), nullable=True)  # webhook, admin_username
    
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    is_secret = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(BigInteger, nullable=True, index=True)
    admin_name = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
