# Backend Implementation Guide: E-ITS Assets & Target Objects (Sihtobjektid)

## 1. Domain Knowledge: E-ITS Methodology
Before implementing the logic, understand the difference between Assets (Varad) and Target Objects (Sihtobjektid) in the E-ITS/IT-Grundschutz framework.

* **Assets (Varad):** Anything valuable to the organization (hardware, software, data, processes). A single Dell laptop is an asset.
* **Target Objects (Sihtobjektid):** An architectural abstraction layer. We do not apply security measures to 50 individual laptops. We group them into a single Target Object (e.g., "All Windows Laptops") to optimize administrative overhead.
* **Modeling (Modelleerimine):** The Target Object is then mapped to an E-ITS Module (e.g., `SYS.2.1`). Through this mapping, the security measures are inherited by the Target Object and, by extension, all assets within that group.

## 2. Critical Database Architecture
**DO NOT create a separate `target_objects` table.** The existing `assets` table handles both individual assets and grouped target objects via internal logic. If an asset represents a Target Object group, `is_grouped` is set to `true`, and `quantity` reflects the number of items.

### Required SQLAlchemy ORM Models (Reference)
Implement your backend models mirroring this structure to ensure cascading and relationships work correctly:

```python
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

class Asset(Base):
    __tablename__ = 'assets'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    
    # Target Object grouping fields
    is_grouped = Column(Boolean, default=False)
    quantity = Column(Integer, default=1)
    group_name = Column(String)
    
    # Relationship to modeling
    module_mappings = relationship("AssetModuleMapping", back_populates="asset", cascade="all, delete-orphan")

class AssetModuleMapping(Base):
    __tablename__ = 'asset_module_mappings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'))
    module_id = Column(UUID(as_uuid=True), ForeignKey('eits_modules.id', ondelete='CASCADE'))
    
    # Back-references
    asset = relationship("Asset", back_populates="module_mappings")
    # Link to generated implementation items
    imr_items = relationship("ImrItem", back_populates="mapping", cascade="all, delete-orphan")