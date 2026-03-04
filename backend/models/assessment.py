"""
Assessment SQLAlchemy model
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Date, ARRAY, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    status = Column(String(50), default="active")  # active, completed, archived
    workspace_path = Column(String(512))
    container_name = Column(String(255), nullable=True)  # Container where workspace was created

    # State of Work
    client_name = Column(String(255))
    scope = Column(Text)
    limitations = Column(Text)
    objectives = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)

    # Basic Information
    target_domains = Column(ARRAY(Text))
    ip_scopes = Column(ARRAY(Text))
    credentials = Column(Text)
    access_info = Column(Text)
    category = Column(String(100))  # API, Website, External Infra, etc.
    environment = Column(String(50), default="non_specifie")  # production, dev, non_specifie

    # Environment Setup
    environment_notes = Column(Text)

    # Stealth & Evasion Configuration
    stealth_profile = Column(String(50), default="normal")  # ghost, careful, normal, aggressive
    proxy_config = Column(Text)  # e.g. "socks5://127.0.0.1:9050"
    custom_user_agent = Column(Text)
    scan_delay = Column(String(50))  # e.g. "500ms", "2s", "1-5s"
    max_rate = Column(Integer)  # max requests/sec
    decoy_ips = Column(Text)  # comma-separated or "RND:10"
    source_port = Column(Integer)  # e.g. 53, 80
    nmap_timing = Column(String(10))  # T0-T5 override
    fragmentation = Column(Boolean, default=False)
    randomize_hosts = Column(Boolean, default=False)
    extra_nmap_evasion = Column(Text)  # additional nmap flags
    nikto_evasion = Column(String(50))  # nikto -evasion codes
    nikto_tuning = Column(String(50))  # nikto -Tuning codes

    # Folder Management (optional organization)
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)

    # Relationships
    folder = relationship("Folder", back_populates="assessments")
    sections = relationship("AssessmentSection", back_populates="assessment", cascade="all, delete-orphan")
    cards = relationship("Card", back_populates="assessment", cascade="all, delete-orphan")
    recon_data = relationship("ReconData", back_populates="assessment", cascade="all, delete-orphan")
    command_history = relationship("CommandHistory", back_populates="assessment", cascade="all, delete-orphan")
    custom_tables = relationship("CustomTable", back_populates="assessment", cascade="all, delete-orphan")
    credentials_list = relationship("Credential", back_populates="assessment", cascade="all, delete-orphan")
    pending_commands = relationship("PendingCommand", back_populates="assessment", cascade="all, delete-orphan")

