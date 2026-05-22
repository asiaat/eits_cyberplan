# **TECHNICAL DESIGN DOCUMENT: E-ITS v2 IMR & Scope Modeling System Architecture**

This architectural blueprint outlines the design, implementation, and database relationships of the E-ITS (Estonian Information Security Standard \- *Eesti infoturbestandard*) v2 system. It covers **Scope Modeling (*Kaitseala modelleerimine*)** and the **Infosec Measures Implementation Plan (IMR \- *Infoturbe meetmete rakenduskava*)**, fully compatible with the database schema defined in 20260521181936\_schema.sql.

## **1\. System Domain Concept & Workflow**

E-ITS is a **business-process-centric standard (*äriprotsessikeskne standard*)**. Security starts at the business level and cascades down to technical systems.

       \[1. Business Process / Äriprotsess\]  
                       |  
                       | Defines  
                       v  
       \[2. Protection Need / Kaitsetarve\] (C-I-A / K-T-K)  
                       |  
                       | Approved by Top Management / CISO (Kinnitatud)  
                       v  
       \[3. Mode of Protection / Turbeviis\] Locked (Põhi-, standard- või tuumikuturve)  
                       |  
         \+-------------+-------------+  
         | (Cascades)                | (Structural Analysis / Struktuuranalüüs)  
         v                           v  
\[Process Modeling\]           \[Asset Association / Varade seostamine\] (process\_assets)  
         |                           |  
         |                           | Inherits Highest Protection Need  
         |                           v  
         |                   \[Asset Modeling / Varade modelleerimine\]  
         |                           |  
         \+-------------+-------------+  
                       |  
                       v  
         \[IMR Generation / IMR-i koostamine\] (imr\_items)  
                       |  
                       v  
         \[Operationalization / Meetmete täitmine\] (PEARO: P \-\> A \-\> E \-\> R / O)  
                       |  
                       v  
         \[Proof of Compliance / Tõendamine\] (evidences & evidence\_links)

### **Core Business Rules & Validations:**

1. **The Lockout Rule (*Lukustusreegel*):** Once the Tenant's Mode of Protection (*turbeviis*) is saved, the Protection Need (*kaitsetarve*) of any associated Business Process (*äriprotsess*) becomes **LOCKED** and cannot be edited. This guarantees that changes to risk levels do not silently invalidate already modeled baseline controls.  
2. **The Modeling Lock (*Modelleerimise lukk*):** No Asset (*sihtobjekt / IT-vara*) or Business Process (*äriprotsess*) can have security modules modeled unless its Protection Need (*kaitsetarve*) is fully evaluated and marked as **Approved (*kinnitatud*)** by the CISO or Management.  
3. **PEARO Status Safeguard (*PEARO-oleku kontroll*):** A measure cannot transition to the **Implemented (*R \- Rakendatud*)** status unless:  
   * implementation\_details (*rakendamise kirjeldus*) contains a comprehensive explanation (minimum of 15 characters).  
   * At least one active Evidence (*asitõend*) file metadata record is linked to the IMR item via the polymorphic evidence\_links table.

## **2\. Database Schema Alignment**

This architecture matches the physical tables present in 20260521181936\_schema.sql.

### **Key Entities & Relations Mapping:**

* **tenants**: Houses the tenant baseline configuration. We store mode\_of\_protection (BASELINE, STANDARD, or CORE) here.  
* **business\_processes**: Contains processes. Protection levels are mapped via protection\_need\_summaries (which references business\_processes.id).  
* **assets**: Houses target objects (*sihtobjektid*).  
* **process\_assets**: The join table implementing the Structural Analysis (*struktuuranalüüs*), linking processes to assets.  
* **imr\_items**: The core execution table. References:  
  * tenant\_id \-\> tenants(id)  
  * measure\_id \-\> eits\_catalog\_measures(id)  
  * responsible\_id \-\> local\_users(id) (points to the assigned officer / *vastutaja*)  
  * created\_by / updated\_by \-\> local\_users(id)  
* **evidences & evidence\_links**: The polymorphic evidence management system. evidence\_links references imr\_items.id as target\_id when target\_type \= 'imr\_item'.

### **SQL Setup for Custom Scope Modeling Mapping Table:**

To assign modules (eits\_catalog\_modules) to processes or assets and auto-generate IMR rows, create the mapped\_modules table:

CREATE TABLE public.mapped\_modules (  
    id uuid DEFAULT gen\_random\_uuid() NOT NULL,  
    tenant\_id uuid NOT NULL,  
    module\_id uuid NOT NULL,                    \-- References eits\_catalog\_modules(id)  
    target\_type character varying(50) NOT NULL, \-- 'asset' OR 'business\_process'  
    target\_id uuid NOT NULL,                    \-- References assets(id) OR business\_processes(id)  
    created\_at timestamp with time zone DEFAULT now(),  
    created\_by uuid,  
    CONSTRAINT pk\_mapped\_modules PRIMARY KEY (id),  
    CONSTRAINT fk\_mapped\_mod\_tenant FOREIGN KEY (tenant\_id) REFERENCES public.tenants(id) ON DELETE CASCADE,  
    CONSTRAINT fk\_mapped\_mod\_catalog FOREIGN KEY (module\_id) REFERENCES public.eits\_catalog\_modules(id) ON DELETE CASCADE,  
    CONSTRAINT fk\_mapped\_mod\_creator FOREIGN KEY (created\_by) REFERENCES public.local\_users(id) ON DELETE SET NULL,  
    CONSTRAINT uq\_tenant\_module\_target UNIQUE (tenant\_id, module\_id, target\_type, target\_id)  
);

\-- Index for speedy lookup during mapping & deletion  
CREATE INDEX ix\_mapped\_modules\_lookup ON public.mapped\_modules USING btree (target\_type, target\_id);

\-- Attach mapped\_module\_id as metadata on imr\_items to track which mapping generated which rows  
ALTER TABLE public.imr\_items   
ADD COLUMN IF NOT EXISTS mapped\_module\_id uuid,  
ADD CONSTRAINT fk\_imr\_mapped\_module FOREIGN KEY (mapped\_module\_id) REFERENCES public.mapped\_modules(id) ON DELETE SET NULL;

## **3\. Backend (v2 API) Architecture & Service Logic**

All controllers, validators, and entities must reside strictly under backend/app/api/v2/.

### **A. Modeling Service (backend/app/services/v2/modeling\_service.py)**

This service validates structural preparedness, locks process changes, maps modules, and generates the required IMR baseline lines based on the tenant's Chosen Mode of Protection (*turbeviis*).

import uuid  
from typing import Dict, Any, List  
from sqlalchemy.orm import Session  
from fastapi import HTTPException, status  
from app.models import (  
    Tenant, Asset, BusinessProcess, MappedModule, ImrItem,   
    EitsCatalogMeasure, ProcessAsset, ProtectionNeedSummary  
)

class ModelingService:  
    @staticmethod  
    def validate\_target\_ready(db: Session, tenant\_id: uuid.UUID, target\_type: str, target\_id: uuid.UUID) \-\> bool:  
        """  
        E-ITS Business Rule: Verify that target is approved for security modeling.  
        """  
        if target\_type \== "business\_process":  
            \# Verify the business process has an approved protection need  
            summary \= db.query(ProtectionNeedSummary).filter(  
                ProtectionNeedSummary.business\_process\_id \== target\_id,  
                ProtectionNeedSummary.tenant\_id \== tenant\_id  
            ).first()  
            if not summary or not summary.approved\_by:  
                raise HTTPException(  
                    status\_code=status.HTTP\_400\_BAD\_REQUEST,  
                    detail="Tõrge: Äriprotsessi ei saa modelleerida, sest selle kaitsetarve on veel kinnitamata."  
                )  
          
        elif target\_type \== "asset":  
            \# Structural Analysis Check: Must be linked to at least one process  
            relations \= db.query(ProcessAsset).filter(  
                ProcessAsset.asset\_id \== target\_id,   
                ProcessAsset.tenant\_id \== tenant\_id  
            ).all()  
            if not relations:  
                raise HTTPException(  
                    status\_code=status.HTTP\_400\_BAD\_REQUEST,  
                    detail="Tõrge: Seda vara ei saa modelleerida, sest see on seostamata ühegi äriprotsessiga (Struktuuranalüüs teostamata)."  
                )  
              
            \# Verify that all linked processes are approved  
            for rel in relations:  
                summary \= db.query(ProtectionNeedSummary).filter(  
                    ProtectionNeedSummary.business\_process\_id \== rel.business\_process\_id,  
                    ProtectionNeedSummary.tenant\_id \== tenant\_id  
                ).first()  
                if not summary or not summary.approved\_by:  
                    raise HTTPException(  
                        status\_code=status.HTTP\_400\_BAD\_REQUEST,  
                        detail=f"Tõrge: Seotud äriprotsessi '{rel.business\_process.name}' kaitsetarve on kinnitamata."  
                    )  
        return True

    @staticmethod  
    def map\_module(  
        db: Session,   
        tenant\_id: uuid.UUID,   
        user\_id: uuid.UUID,  
        module\_id: uuid.UUID,   
        target\_type: str,   
        target\_id: uuid.UUID  
    ) \-\> Dict\[str, Any\]:  
        """  
        Performs baseline modeling mapping and auto-populates imr\_items matching the Tenant's Mode of Protection.  
        """  
        \# Validate target preparedness  
        ModelingService.validate\_target\_ready(db, tenant\_id, target\_type, target\_id)

        \# Check for pre-existing mapping  
        existing \= db.query(MappedModule).filter(  
            MappedModule.tenant\_id \== tenant\_id,  
            MappedModule.module\_id \== module\_id,  
            MappedModule.target\_type \== target\_type,  
            MappedModule.target\_id \== target\_id  
        ).first()  
        if existing:  
            raise HTTPException(status\_code=400, detail="See moodul on sellele objektile juba lisatud.")

        \# Create the mapping  
        mapping \= MappedModule(  
            tenant\_id=tenant\_id,  
            module\_id=module\_id,  
            target\_type=target\_type,  
            target\_id=target\_id,  
            created\_by=user\_id  
        )  
        db.add(mapping)  
        db.flush()

        \# Query Tenant Security Profile  
        tenant \= db.query(Tenant).filter(Tenant.id \== tenant\_id).first()  
        mode \= tenant.mode\_of\_protection if tenant else "BASELINE"

        \# Fetch catalog measures  
        catalog\_measures \= db.query(EitsCatalogMeasure).filter(EitsCatalogMeasure.module\_id \== module\_id).all()  
        generated\_count \= 0

        for measure in catalog\_measures:  
            \# Filter according to mode of protection  
            \# BASELINE \-\> only BASE measures  
            \# STANDARD/CORE \-\> BASE and STANDARD measures  
            should\_apply \= False  
            if mode \== "BASELINE" and measure.level \== "BASE":  
                should\_apply \= True  
            elif mode in \["STANDARD", "CORE"\] and measure.level in \["BASE", "STANDARD"\]:  
                should\_apply \= True

            if should\_apply:  
                \# Build unique IMR item if not duplicate  
                existing\_imr \= db.query(ImrItem).filter(  
                    ImrItem.tenant\_id \== tenant\_id,  
                    ImrItem.measure\_id \== measure.id,  
                    ImrItem.asset\_id \== (target\_id if target\_type \== "asset" else None),  
                    ImrItem.business\_process\_id \== (target\_id if target\_type \== "business\_process" else None)  
                ).first()

                if not existing\_imr:  
                    imr\_item \= ImrItem(  
                        tenant\_id=tenant\_id,  
                        measure\_id=measure.id,  
                        mapped\_module\_id=mapping.id,  
                        asset\_id=target\_id if target\_type \== "asset" else None,  
                        business\_process\_id=target\_id if target\_type \== "business\_process" else None,  
                        status="P",  \# Default to Planned (Kavandatud)  
                        priority="P2",  
                        created\_by=user\_id,  
                        updated\_by=user\_id  
                    )  
                    db.add(imr\_item)  
                    generated\_count \+= 1

        db.commit()  
        return {  
            "message": "Moodul edukalt modelleeritud ja IMR-i kirjed genereeritud.",  
            "mapped\_module\_id": mapping.id,  
            "generated\_measures\_count": generated\_count  
        }

### **B. IMR Compilation Service (backend/app/services/v2/imr\_service.py)**

This service manages transitions through the PEARO statuses, locking protection need modifications when a mode of protection is active, and handling S3 evidence files.

import uuid  
import datetime  
from typing import Dict, Any  
from sqlalchemy.orm import Session  
from fastapi import HTTPException, status  
from app.models import ImrItem, EvidenceLink, LocalUser, Tenant, ProtectionNeedSummary

class ImrService:  
    @staticmethod  
    def update\_imr\_item(  
        db: Session,   
        tenant\_id: uuid.UUID,   
        user\_id: uuid.UUID,  
        imr\_item\_id: uuid.UUID,   
        update\_data: Dict\[str, Any\]  
    ) \-\> Dict\[str, Any\]:  
        """  
        Updates an IMR item's implementation parameters. Enforces S3 evidence attachment constraints on Implemented (R) state.  
        """  
        item \= db.query(ImrItem).filter(ImrItem.id \== imr\_item\_id, ImrItem.tenant\_id \== tenant\_id).first()  
        if not item:  
            raise HTTPException(status\_code=404, detail="Seda rakenduskava meedet ei leitud.")

        new\_status \= update\_data.get("status")  
        if new\_status \== "R":  
            details \= update\_data.get("implementation\_details", item.implementation\_details)  
            if not details or len(details.strip()) \< 15:  
                raise HTTPException(  
                    status\_code=status.HTTP\_400\_BAD\_REQUEST,  
                    detail="Tõrge: Meedet ei saa märkida rakendatuks (R) ilma piisava teostuskirjelduseta (minimaalselt 15 tähemärki)."  
                )

            \# Polymorphic verification check against evidence\_links  
            has\_proof \= db.query(EvidenceLink).filter(  
                EvidenceLink.target\_id \== item.id,  
                EvidenceLink.target\_type \== "imr\_item",  
                EvidenceLink.tenant\_id \== tenant\_id  
            ).count() \> 0

            if not has\_proof:  
                raise HTTPException(  
                    status\_code=status.HTTP\_400\_BAD\_REQUEST,  
                    detail="Tõrge: Rakendatud (R) meede nõuab vähemalt ühe digitaalse asitõendi (tõendusmaterjali) linkimist."  
                )

        \# Apply updates  
        for key, value in update\_data.items():  
            if hasattr(item, key):  
                setattr(item, key, value)

        item.updated\_by \= user\_id  
        item.updated\_at \= datetime.datetime.utcnow()  
        db.commit()

        return {  
            "message": "Rakenduskava meede edukalt uuendatud.",  
            "imr\_item\_id": item.id,  
            "status": item.status  
        }

    @staticmethod  
    def update\_process\_protection\_need(  
        db: Session,   
        tenant\_id: uuid.UUID,   
        process\_id: uuid.UUID,   
        new\_levels: Dict\[str, str\]  
    ) \-\> Dict\[str, Any\]:  
        """  
        E-ITS Business Rule: Once a tenant has chosen and saved a Mode of Protection,  
        the protection need level for any Business Process becomes strictly immutable.  
        """  
        tenant \= db.query(Tenant).filter(Tenant.id \== tenant\_id).first()  
          
        \# Lock check  
        if tenant and tenant.mode\_of\_protection is not None:  
            raise HTTPException(  
                status\_code=status.HTTP\_400\_BAD\_REQUEST,  
                detail="Kaitsetarvet ei saa muuta, sest turbeviis (põhi-, standard- või tuumikuturve) on juba valitud ja lukustatud."  
            )

        summary \= db.query(ProtectionNeedSummary).filter(  
            ProtectionNeedSummary.business\_process\_id \== process\_id,  
            ProtectionNeedSummary.tenant\_id \== tenant\_id  
        ).first()

        if not summary:  
            raise HTTPException(status\_code=404, detail="Kaitsetarbe kokkuvõtet ei leitud.")

        summary.confidentiality\_need \= new\_levels.get("confidentiality", summary.confidentiality\_need)  
        summary.integrity\_need \= new\_levels.get("integrity", summary.integrity\_need)  
        summary.availability\_need \= new\_levels.get("availability", summary.availability\_need)  
        db.commit()

        return {"message": "Äriprotsessi kaitsetarve edukalt uuendatud."}

## **4\. API v2 Endpoint Definitions (backend/app/api/v2/endpoints/imr.py)**

All API routes utilize strict Dependency Injection for database sessions and verified authorization context blocks.

from fastapi import APIRouter, Depends, Query, status  
from sqlalchemy.orm import Session  
import uuid  
\# Import your verified security dependencies: get\_db, get\_current\_active\_user

router \= APIRouter(prefix="/imr", tags=\["E-ITS Rakenduskava (IMR)"\])

@router.patch("/items/{item\_id}", status\_code=200)  
def update\_imr\_measure(  
    item\_id: uuid.UUID,  
    status: str \= None,  
    responsible\_id: uuid.UUID \= None,  
    due\_date: str \= None,  
    implementation\_details: str \= None,  
    verification\_method: str \= None,  
    db: Session \= Depends(get\_db),  
    current\_user \= Depends(get\_current\_active\_user)  
):  
    """  
    Updates the operational details, responsibility and status of an active IMR measure.  
    """  
    update\_payload \= {}  
    if status: update\_payload\["status"\] \= status  
    if responsible\_id: update\_payload\["responsible\_id"\] \= responsible\_id  
    if due\_date: update\_payload\["due\_date"\] \= due\_date  
    if implementation\_details: update\_payload\["implementation\_details"\] \= implementation\_details  
    if verification\_method: update\_payload\["verification\_method"\] \= verification\_method

    return ImrService.update\_imr\_item(  
        db=db,  
        tenant\_id=current\_user.tenant\_id,  
        user\_id=current\_user.id,  
        imr\_item\_id=item\_id,  
        update\_data=update\_payload  
    )

@router.patch("/business-process/{process\_id}/protection-need", status\_code=200)  
def change\_process\_needs(  
    process\_id: uuid.UUID,  
    confidentiality: str,  
    integrity: str,  
    availability: str,  
    db: Session \= Depends(get\_db),  
    current\_user \= Depends(get\_current\_active\_user)  
):  
    """  
    Saves new protection levels (C-I-A) for a process. Rejects with HTTP 400 if Mode of Protection is locked.  
    """  
    return ImrService.update\_process\_protection\_need(  
        db=db,  
        tenant\_id=current\_user.tenant\_id,  
        process\_id=process\_id,  
        new\_levels={  
            "confidentiality": confidentiality,  
            "integrity": integrity,  
            "availability": availability  
        }  
    )

## **5\. Integration Test Specifications (Pytest)**

These integration test pipelines must verify tenant database isolation and enforce E-ITS specific state locks.

\# test\_imr\_v2\_service.py  
import pytest  
import uuid  
from sqlalchemy.orm import Session  
from fastapi import HTTPException  
from app.models import ImrItem, Tenant, ProtectionNeedSummary, BusinessProcess

def test\_imr\_implemented\_status\_rejection\_without\_evidence(db\_session: Session):  
    """  
    Ensure status transition to Implemented (R) fails without linked S3 evidences.  
    """  
    tenant\_id \= uuid.uuid4()  
    user\_id \= uuid.uuid4()  
    imr\_item\_id \= uuid.uuid4()

    item \= ImrItem(  
        id=imr\_item\_id,  
        tenant\_id=tenant\_id,  
        measure\_id=uuid.uuid4(),  
        status="P",  
        implementation\_details=""  
    )  
    db\_session.add(item)  
    db\_session.commit()

    \# Attempt transition without details and evidence links  
    with pytest.raises(HTTPException) as exc\_info:  
        ImrService.update\_imr\_item(  
            db=db\_session,  
            tenant\_id=tenant\_id,  
            user\_id=user\_id,  
            imr\_item\_id=imr\_item\_id,  
            update\_data={"status": "R", "implementation\_details": "Täidetud"}  
        )

    assert exc\_info.value.status\_code \== 400  
    assert "piisava teostuskirjelduseta" in exc\_info.value.detail

def test\_lockout\_prevents\_protection\_need\_modification(db\_session: Session):  
    """  
    Verify that Business Process protection needs are locked if Tenant.mode\_of\_protection is configured.  
    """  
    tenant\_id \= uuid.uuid4()  
    process\_id \= uuid.uuid4()

    \# Lock tenant by choosing STANDARD mode of protection  
    tenant \= Tenant(id=tenant\_id, mode\_of\_protection="STANDARD")  
    process \= BusinessProcess(id=process\_id, tenant\_id=tenant\_id, name="Test")  
    summary \= ProtectionNeedSummary(  
        business\_process\_id=process\_id,  
        tenant\_id=tenant\_id,  
        confidentiality\_need="NORMAL",  
        integrity\_need="NORMAL",  
        availability\_need="NORMAL"  
    )

    db\_session.add\_all(\[tenant, process, summary\])  
    db\_session.commit()

    \# Expecting failure on change attempts due to active lock  
    with pytest.raises(HTTPException) as exc\_info:  
        ImrService.update\_process\_protection\_need(  
            db=db\_session,  
            tenant\_id=tenant\_id,  
            process\_id=process\_id,  
            new\_levels={"confidentiality": "HIGH", "integrity": "HIGH", "availability": "HIGH"}  
        )

    assert exc\_info.value.status\_code \== 400  
    assert "Kaitsetarvet ei saa muuta" in exc\_info.value.detail

## **6\. Front-End Component Mockup (React & Tailwind CSS)**

Use this complete component layout inside the client view to represent interactive IMR execution states, S3 file uploading simulated pathways, and protection lockout warnings.

import React, { useState } from 'react';

interface ImrItem {  
  id: string;  
  code: string;  
  name: string;  
  status: 'P' | 'A' | 'E' | 'R' | 'O';  
  responsibleName: string;  
  dueDate: string;  
  details: string;  
  hasEvidence: boolean;  
}

interface BusinessProcess {  
  id: string;  
  name: string;  
  confidentiality: string;  
  integrity: string;  
  availability: string;  
}

export default function App() {  
  // Configurable state simulating backend response variables  
  const \[modeOfProtection, setModeOfProtection\] \= useState\<string | null\>('STANDARD'); 

  const \[processes, setProcesses\] \= useState\<BusinessProcess\[\]\>(\[  
    { id: 'bp-1', name: 'Üldarstiabi osutamine (Põhitegevus)', confidentiality: 'HIGH', integrity: 'HIGH', availability: 'HIGH' },  
    { id: 'bp-2', name: 'Palgaarvestuse teostamine (Tugitegevus)', confidentiality: 'NORMAL', integrity: 'NORMAL', availability: 'NORMAL' }  
  \]);

  const \[imrItems, setImrItems\] \= useState\<ImrItem\[\]\>(\[  
    { id: '1', code: 'ISMS.1.M1', name: 'Turbehalduse üldvastutuse võtmine', status: 'R', responsibleName: 'Jaanika Tamm (Tegevjuht)', dueDate: '2026-06-01', details: 'Juhtkond kinnitas vastutusalad juhatuse otsusega nr 14.', hasEvidence: true },  
    { id: '2', code: 'CON.3.M5', name: 'Regulaarne andmevarundus', status: 'E', responsibleName: 'Peeter Kask (IT-Spetsialist)', dueDate: '2026-08-10', details: 'Automiseerime kord ööpäevas toimuvat varundust MinIO hoidlasse.', hasEvidence: false },  
    { id: '3', code: 'SYS.1.1.M2', name: 'Süsteemide uuendamise reeglid', status: 'P', responsibleName: '', dueDate: '', details: '', hasEvidence: false }  
  \]);

  const \[selectedItem, setSelectedItem\] \= useState\<ImrItem | null\>(null);  
  const \[responsibleInput, setResponsibleInput\] \= useState('');  
  const \[dueDateInput, setDueDateInput\] \= useState('');  
  const \[detailsInput, setDetailsInput\] \= useState('');  
  const \[statusInput, setStatusInput\] \= useState\<'P' | 'A' | 'E' | 'R' | 'O'\>('P');  
  const \[evidenceAttached, setEvidenceAttached\] \= useState(false);  
  const \[notification, setNotification\] \= useState\<{ msg: string; type: 'success' | 'error' } | null\>(null);

  const triggerNotification \= (msg: string, type: 'success' | 'error') \=\> {  
    setNotification({ msg, type });  
    setTimeout(() \=\> setNotification(null), 5500);  
  };

  const handleEditItem \= (item: ImrItem) \=\> {  
    setSelectedItem(item);  
    setResponsibleInput(item.responsibleName);  
    setDueDateInput(item.dueDate);  
    setDetailsInput(item.details);  
    setStatusInput(item.status);  
    setEvidenceAttached(item.hasEvidence);  
  };

  const handleSaveItem \= () \=\> {  
    if (\!selectedItem) return;

    // Enforce PEARO Implemented status validations  
    if (statusInput \=== 'R') {  
      if (detailsInput.trim().length \< 15\) {  
        triggerNotification('Tõrge: Rakendatud (R) staatus nõuab kirjeldust (min 15 tähemärki)\!', 'error');  
        return;  
      }  
      if (\!evidenceAttached) {  
        triggerNotification('Tõrge: Rakendatud (R) staatus nõuab seotud asitõendit\!', 'error');  
        return;  
      }  
    }

    const updated \= imrItems.map(item \=\> {  
      if (item.id \=== selectedItem.id) {  
        return {  
          ...item,  
          responsibleName: responsibleInput,  
          dueDate: dueDateInput,  
          details: detailsInput,  
          status: statusInput,  
          hasEvidence: evidenceAttached  
        };  
      }  
      return item;  
    });

    setImrItems(updated);  
    setSelectedItem(null);  
    triggerNotification('Meetme andmed salvestatud ja seosed kontrollitud.', 'success');  
  };

  const handleTryEditProtection \= (processName: string) \=\> {  
    if (modeOfProtection) {  
      triggerNotification(  
        \`LUKUSTATUD: Äriprotsessi '${processName}' kaitsetarvet ei saa muuta, sest turbeviis (${modeOfProtection}) on valitud\!\`,   
        'error'  
      );  
    } else {  
      triggerNotification(\`Kaitsetarbe muutmise aken avatud protsessile: ${processName}\`, 'success');  
    }  
  };

  return (  
    \<div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8 font-sans"\>  
      \<div className="max-w-4xl mx-auto"\>  
          
        {/\* Main Dashboard Header \*/}  
        \<div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6"\>  
          \<div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"\>  
            \<div\>  
              \<h1 className="text-2xl font-bold text-slate-900"\>Infoturbe meetmete rakenduskava (IMR) koostamine\</h1\>  
              \<p className="text-xs text-slate-500 mt-1"\>Skoobi modelleerimisel loodud meetmete elutsükkel ja täitmine\</p\>  
            \</div\>  
            \<div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-right"\>  
              \<span className="text-xxs font-bold text-slate-400 uppercase tracking-wide block"\>Valitud turbeviis\</span\>  
              \<span className={\`text-xs font-bold px-2 py-0.5 rounded inline-block mt-1 ${  
                modeOfProtection ? 'bg-indigo-100 text-indigo-800' : 'bg-amber-100 text-amber-800'  
              }\`}\>  
                {modeOfProtection ? \`LUKUSTATUD: ${modeOfProtection}\` : 'Määramata (Vaba muutmiseks)'}  
              \</span\>  
            \</div\>  
          \</div\>  
        \</div\>

        {/\* Global Notifications Panel \*/}  
        {notification && (  
          \<div className={\`p-4 rounded-lg mb-6 border text-sm font-semibold transition-all ${  
            notification.type \=== 'success'   
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'   
              : 'bg-rose-50 text-rose-800 border-rose-200'  
          }\`}\>  
            {notification.msg}  
          \</div\>  
        )}

        {/\* Business Process Lockout Monitoring Grid \*/}  
        \<div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6"\>  
          \<div className="flex justify-between items-center mb-4"\>  
            \<h2 className="text-md font-bold text-slate-800"\>Äriprotsesside kaitsetarbed & Seisund\</h2\>  
            {modeOfProtection && (  
              \<span className="text-xs text-rose-600 font-bold flex items-center gap-1 bg-rose-50 px-2 py-0.5 rounded border border-rose-100"\>  
                🔒 Lukustatud  
              \</span\>  
            )}  
          \</div\>  
            
          \<div className="grid grid-cols-1 sm:grid-cols-2 gap-4"\>  
            {processes.map(p \=\> (  
              \<div key={p.id} className="p-4 rounded-lg bg-slate-50 border border-slate-150 flex flex-col justify-between"\>  
                \<div\>  
                  \<h3 className="font-bold text-slate-900 text-sm"\>{p.name}\</h3\>  
                  \<div className="mt-2 flex gap-1.5"\>  
                    \<span className="text-xxs font-semibold bg-white border px-1.5 py-0.5 rounded text-slate-500"\>K: {p.confidentiality}\</span\>  
                    \<span className="text-xxs font-semibold bg-white border px-1.5 py-0.5 rounded text-slate-500"\>T: {p.integrity}\</span\>  
                    \<span className="text-xxs font-semibold bg-white border px-1.5 py-0.5 rounded text-slate-500"\>K: {p.availability}\</span\>  
                  \</div\>  
                \</div\>  
                \<button  
                  onClick={() \=\> handleTryEditProtection(p.name)}  
                  className={\`mt-4 w-full text-center text-xs font-bold py-1.5 rounded transition-all ${  
                    modeOfProtection   
                      ? 'bg-slate-200 text-slate-400 cursor-not-allowed'   
                      : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'  
                  }\`}  
                \>  
                  {modeOfProtection ? '🔒 Muutmine lukustatud' : 'Muuda kaitsetarvet'}  
                \</button\>  
              \</div\>  
            ))}  
          \</div\>  
        \</div\>

        {/\* IMR Table View \*/}  
        \<div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-6"\>  
          \<div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50"\>  
            \<h3 className="text-md font-bold text-slate-800"\>Rakenduskava aktiivsed meetmed ({imrItems.length})\</h3\>  
          \</div\>  
          \<table className="w-full text-left border-collapse text-sm"\>  
            \<thead className="bg-slate-50/75 border-b border-slate-200 text-xxs font-bold text-slate-500 uppercase tracking-wider"\>  
              \<tr\>  
                \<th className="p-4"\>Kood\</th\>  
                \<th className="p-4"\>Meede\</th\>  
                \<th className="p-4"\>Olek\</th\>  
                \<th className="p-4"\>Vastutaja\</th\>  
                \<th className="p-4"\>Tähtaeg\</th\>  
                \<th className="p-4 text-right"\>Tegevus\</th\>  
              \</tr\>  
            \</thead\>  
            \<tbody className="divide-y divide-slate-150"\>  
              {imrItems.map(item \=\> (  
                \<tr key={item.id} className="hover:bg-slate-50/50 transition-colors"\>  
                  \<td className="p-4 font-bold text-blue-800"\>{item.code}\</td\>  
                  \<td className="p-4 max-w-xs truncate font-medium text-slate-900"\>{item.name}\</td\>  
                  \<td className="p-4"\>  
                    \<span className={\`px-2 py-0.5 rounded-full text-xxs font-bold ${  
                      item.status \=== 'R' ? 'bg-emerald-100 text-emerald-800' :  
                      item.status \=== 'E' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'  
                    }\`}\>  
                      {item.status}  
                    \</span\>  
                  \</td\>  
                  \<td className="p-4 text-xs text-slate-600"\>{item.responsibleName || 'Määramata'}\</td\>  
                  \<td className="p-4 text-xs text-slate-600"\>{item.dueDate || 'Määramata'}\</td\>  
                  \<td className="p-4 text-right"\>  
                    \<button  
                      onClick={() \=\> handleEditItem(item)}  
                      className="text-xs text-indigo-600 hover:text-indigo-950 font-bold hover:underline"  
                    \>  
                      Täida meedet  
                    \</button\>  
                  \</td\>  
                \</tr\>  
              ))}  
            \</tbody\>  
          \</table\>  
        \</div\>

        {/\* Selected Measure Detail Editing Area \*/}  
        {selectedItem && (  
          \<div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200"\>  
            \<div className="flex justify-between items-start mb-4 border-b border-slate-100 pb-3"\>  
              \<div\>  
                \<h2 className="text-lg font-bold text-slate-900"\>  
                  Meetme andmete täitmine: \<span className="text-blue-800"\>{selectedItem.code}\</span\>  
                \</h2\>  
                \<p className="text-xs text-slate-500 mt-0.5"\>{selectedItem.name}\</p\>  
              \</div\>  
              \<button onClick={() \=\> setSelectedItem(null)} className="text-slate-400 hover:text-slate-600 text-lg"\>×\</button\>  
            \</div\>

            \<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4"\>  
              \<div\>  
                \<label className="block text-xxs font-bold text-slate-500 uppercase tracking-wider mb-2"\>Vastutaja (\*local\_users\*)\</label\>  
                \<input  
                  type="text"  
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"  
                  value={responsibleInput}  
                  onChange={(e) \=\> setResponsibleInput(e.target.value)}  
                  placeholder="nt Juhatuse esimees"  
                /\>  
              \</div\>  
              \<div\>  
                \<label className="block text-xxs font-bold text-slate-500 uppercase tracking-wider mb-2"\>Tähtaeg\</label\>  
                \<input  
                  type="date"  
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"  
                  value={dueDateInput}  
                  onChange={(e) \=\> setDueDateInput(e.target.value)}  
                /\>  
              \</div\>  
            \</div\>

            \<div className="mb-4"\>  
              \<label className="block text-xxs font-bold text-slate-500 uppercase tracking-wider mb-2"\>PEARO Rakendusstaatus\</label\>  
              \<select  
                className="w-full border border-slate-200 rounded-lg p-2.5 text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"  
                value={statusInput}  
                onChange={(e) \=\> setStatusInput(e.target.value as any)}  
              \>  
                \<option value="P"\>P \- Kavandatud (Planned)\</option\>  
                \<option value="A"\>A \- Määratud (Assigned)\</option\>  
                \<option value="E"\>E \- Rakendamisel (In Progress)\</option\>  
                \<option value="R"\>R \- Rakendatud (Implemented)\</option\>  
                \<option value="O"\>O \- Väljast tellitud (Outsourced)\</option\>  
              \</select\>  
            \</div\>

            \<div className="mb-4"\>  
              \<label className="block text-xxs font-bold text-slate-500 uppercase tracking-wider mb-2"\>Rakendamise üksikasjalik kirjeldus (\*details\*)\</label\>  
              \<textarea  
                className="w-full border border-slate-200 rounded-lg p-2.5 text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 h-24 resize-none"  
                value={detailsInput}  
                onChange={(e) \=\> setDetailsInput(e.target.value)}  
                placeholder="Kirjelda tegevused, mis tõendavad meetme toimimist..."  
              /\>  
            \</div\>

            \<div className="mb-6 p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center gap-3"\>  
              \<input  
                type="checkbox"  
                id="evidence\_check"  
                checked={evidenceAttached}  
                onChange={(e) \=\> setEvidenceAttached(e.target.checked)}  
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"  
              /\>  
              \<label htmlFor="evidence\_check" className="text-xs font-semibold text-slate-700 select-none"\>  
                📎 Digitaalne asitõend on seostatud (Faili info asub S3-s, link andmebaasis)  
              \</label\>  
            \</div\>

            \<div className="flex justify-end gap-3 border-t border-slate-100 pt-4"\>  
              \<button  
                onClick={() \=\> setSelectedItem(null)}  
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs py-2 px-4 rounded-lg transition-colors"  
              \>  
                Tühista  
              \</button\>  
              \<button  
                onClick={handleSaveItem}  
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs py-2 px-4 rounded-lg transition-colors"  
              \>  
                Salvesta meetme andmed  
              \</button\>  
            \</div\>  
          \</div\>  
        )}

      \</div\>  
    \</div\>  
  );  
}

## **7\. Operational Implementation Checklist for the Coding Agent**

Follow this systematic step-by-step pathway to deploy the v2 IMR and Modeling components safely:

### **Step 1: Execute SQL Migration**

Apply the public.mapped\_modules table creation script via Alembic. Ensure alembic\_version matches the status on the target environment.

### **Step 2: Implement Validations on ProtectionNeedSummary**

In the service class managing protection needs, intercept update payloads and assert that the related Tenant does not have a defined mode\_of\_protection value yet. Raise HTTPException 400 with a localized error message (*Tõrge...*) if locked.

### **Step 3: Write Polymorphic Evidence Linking Controller**

Configure endpoint POST /api/v2/evidences/link to accept target\_id (representing the imr\_item\_id) and target\_type ('imr\_item'). Validate S3 file metadata parameters before creating the database row.

### **Step 4: Write Baseline modeling generation tasks**

Implement the catalog compiler inside ModelingService.map\_module. Dynamically fetch measures based on the tenant's chosen mode\_of\_protection (supporting BASELINE filters vs standard modes).

### **Step 5: Run Automated Verification Tests**

Run Pytest targets on your continuous integration environment. Assert that no cross-tenant leaking is possible and check the lockout parameters.