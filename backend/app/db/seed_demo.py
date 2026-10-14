import asyncio
import logging
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy import select
from backend.app.db.session import AsyncSessionLocal, init_db
from backend.app.models.tenant import Tenant
from backend.app.models.kb import KBDocument, KBChunk
from backend.app.api.endpoints.kb import split_text_into_chunks
from backend.app.services.embedding import generate_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asistline.seed")

DEMO_TENANTS = [
    {
        "id": "apex-logistics",
        "name": "Apex Logistics Support",
        "script_config": {
            "welcome_message": {
                "en": "Thank you for calling Apex Logistics. This call may be recorded for quality and training purposes, and you are speaking with an AI assistant. How can I help you today?",
                "hi": "एपेक्स लॉजिस्टिक्स में कॉल करने के लिए धन्यवाद। गुणवत्ता और प्रशिक्षण के लिए इस कॉल को रिकॉर्ड किया जा सकता है, और आप एक एआई सहायक से बात कर रहे हैं। आज मैं आपकी क्या सहायता कर सकता हूँ?"
            },
            "languages": ["en", "hi"],
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "escalation_triggers": ["angry_sentiment", "repeat_failure", "explicit_request"],
            "verification_required_for": ["order_status", "delivery_change"]
        },
        "escalation_rules": {
            "max_retries_before_escalate": 1,
            "queue_timeout_seconds": 45,
            "fallback_action": "callback_offer"
        },
        "kb": [
            {
                "title": "Shipping and Transit Times",
                "content": (
                    "Apex Logistics offers Standard Ground and Express shipping. "
                    "Standard Ground delivery takes 3 to 5 business days within the continental United States. "
                    "Express Overnight delivery guarantees delivery by 10:30 AM next business day for orders placed before 2:00 PM PST. "
                    "We do not ship to P.O. boxes for oversized cargo."
                )
            },
            {
                "title": "Package Tracking & Verification",
                "content": (
                    "To check real-time package location, customers must provide their 5-digit Order ID and "
                    "the last 4 digits of their registered phone number. "
                    "Once verified, our system provides driver GPS updates, estimated delivery time window, and signature requirements."
                )
            },
            {
                "title": "Damaged or Lost Shipments Policy",
                "content": (
                    "If a package arrives damaged, customers must report it within 48 hours of delivery with photographic evidence. "
                    "Claims for lost in transit packages can be initiated if no carrier scan occurs for 4 consecutive business days. "
                    "Refunds or replacement shipments are processed within 3 business days of claim approval."
                )
            }
        ]
    },
    {
        "id": "pacific-electronics",
        "name": "Pacific Electronics",
        "script_config": {
            "welcome_message": {
                "en": "Thank you for calling Pacific Electronics. This call is recorded for quality assurance and you are speaking with an AI voice agent. How can I assist you with your gear?",
                "hi": "पैसिफिक इलेक्ट्रॉनिक्स में कॉल करने के लिए धन्यवाद। यह कॉल रिकॉर्ड की जाती है। मैं आपकी कैसे सहायता करूँ?"
            },
            "languages": ["en", "hi"],
            "voice_id": "AZnzlk1XvdvUeBnXmlld",
            "escalation_triggers": ["angry_sentiment", "repeat_failure", "explicit_request"],
            "verification_required_for": ["order_status", "warranty_claim", "refund"]
        },
        "escalation_rules": {
            "max_retries_before_escalate": 1,
            "queue_timeout_seconds": 45,
            "fallback_action": "callback_offer"
        },
        "kb": [
            {
                "title": "Return Policy & Restocking Fees",
                "content": (
                    "Electronics may be returned within 30 days of purchase with original receipt and all included accessories. "
                    "Opened items in like-new condition are subject to a 10% restocking fee. "
                    "Defective items within 30 days are exchanged with zero restocking fee."
                )
            },
            {
                "title": "Hardware Manufacturer Warranty",
                "content": (
                    "All Pacific laptops, monitors, and desktops carry a 1-year limited manufacturer warranty covering internal hardware defects. "
                    "Accidental damage, water spills, and cracked screens are not covered under standard warranty but are covered if Pacific Care Plus was purchased."
                )
            },
            {
                "title": "Trade-In and Recycling Program",
                "content": (
                    "Customers can trade in eligible smartphones and tablets for Pacific store credit. "
                    "We also offer free, certified e-waste recycling at all store locations for batteries, cords, and obsolete equipment."
                )
            }
        ]
    },
    {
        "id": "calcoast-health",
        "name": "CalCoast Health",
        "script_config": {
            "welcome_message": {
                "en": "Thank you for contacting CalCoast Health Clinic. This call is recorded for quality and you are speaking with an automated virtual assistant. How can we help you today?",
                "hi": "कैलकोस्ट हेल्थ में कॉल करने के लिए धन्यवाद। यह कॉल रिकॉर्ड की जाती है। आज हम आपकी क्या मदद कर सकते हैं?"
            },
            "languages": ["en", "hi"],
            "voice_id": "EXAVITQu4vr4xnSDxMaL",
            "escalation_triggers": ["urgent_care", "angry_sentiment", "explicit_request"],
            "verification_required_for": ["medical_records", "billing_inquiry"]
        },
        "escalation_rules": {
            "max_retries_before_escalate": 1,
            "queue_timeout_seconds": 30,
            "fallback_action": "callback_offer"
        },
        "kb": [
            {
                "title": "Clinic Hours and Appointments",
                "content": (
                    "CalCoast clinics are open Monday through Friday from 8:00 AM to 6:00 PM PST, and Saturdays from 9:00 AM to 1:00 PM. "
                    "Routine checkups and specialist consultations require an advance appointment. "
                    "Walk-ins are welcomed at our Urgent Care center from 8:00 AM to 8:00 PM daily."
                )
            },
            {
                "title": "Cancellation and Rescheduling",
                "content": (
                    "Appointments must be cancelled or rescheduled at least 24 hours in advance to avoid a $35 late cancellation fee. "
                    "Patients can reschedule online via the patient portal or by speaking to a clinic coordinator."
                )
            },
            {
                "title": "Telehealth and Virtual Visits",
                "content": (
                    "Virtual telehealth appointments are available 7 days a week for non-emergency consultations, prescription refills, and lab reviews. "
                    "Patients connect using a secure smartphone video link sent 15 minutes before the scheduled time."
                )
            }
        ]
    }
]

async def seed_all():
    await init_db()
    async with AsyncSessionLocal() as db:
        for t_data in DEMO_TENANTS:
            # Check if tenant exists
            t_res = await db.execute(select(Tenant).where(Tenant.id == t_data["id"]))
            tenant = t_res.scalar_one_or_none()
            if not tenant:
                logger.info(f"Seeding tenant: {t_data['name']}")
                tenant = Tenant(
                    id=t_data["id"],
                    name=t_data["name"],
                    script_config=t_data["script_config"],
                    escalation_rules=t_data["escalation_rules"],
                )
                db.add(tenant)
                await db.flush()
            else:
                logger.info(f"Tenant {t_data['name']} already exists.")

            # Seed KB documents
            for doc_data in t_data["kb"]:
                d_res = await db.execute(
                    select(KBDocument).where(
                        KBDocument.tenant_id == tenant.id,
                        KBDocument.title == doc_data["title"]
                    )
                )
                doc = d_res.scalar_one_or_none()
                if not doc:
                    logger.info(f"  Ingesting KB doc: {doc_data['title']}")
                    doc = KBDocument(
                        tenant_id=tenant.id,
                        title=doc_data["title"],
                        content=doc_data["content"]
                    )
                    db.add(doc)
                    await db.flush()

                    chunks = split_text_into_chunks(doc_data["content"])
                    for idx, chunk_text in enumerate(chunks):
                        emb = await generate_embedding(chunk_text)
                        chunk = KBChunk(
                            document_id=doc.id,
                            tenant_id=tenant.id,
                            chunk_text=chunk_text,
                            chunk_index=idx,
                            embedding=emb
                        )
                        db.add(chunk)

        await db.commit()
    logger.info("Demo seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_all())
