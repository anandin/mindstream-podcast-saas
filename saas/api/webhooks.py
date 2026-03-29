"""
Webhook registration and management for CastAPI developers.

Endpoints (all require JWT or API-key auth via get_current_user):
  POST   /api/v1/webhooks          Register a new webhook endpoint
  GET    /api/v1/webhooks          List webhooks for the current user
  DELETE /api/v1/webhooks/{id}     Remove a webhook
  GET    /api/v1/webhooks/{id}/deliveries  Delivery history

Supported events:
  episode.queued   — job added to queue
  episode.ready    — audio generated successfully
  episode.failed   — generation failed
  memo.ready       — Memo.fm upload processed
  memo.failed      — Memo.fm processing failed

Payload (POST to your URL):
  {
    "event": "episode.ready",
    "timestamp": "2026-01-01T00:00:00Z",
    "data": { ... event-specific fields ... }
  }

Signature (X-Mindstream-Signature header):
  HMAC-SHA256(secret, raw_body_bytes).hex()
  Verify with: hmac.compare_digest(computed, header_value)
"""
from __future__ import annotations

import hmac
import hashlib
import json
import os
import secrets
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl, field_validator
from sqlalchemy.orm import Session

from saas.api.main import get_db, get_current_user
from saas.db.models import Webhook, WebhookDelivery, User

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

SUPPORTED_EVENTS = {
    "episode.queued",
    "episode.ready",
    "episode.failed",
    "memo.ready",
    "memo.failed",
}


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class WebhookCreate(BaseModel):
    url: str
    events: List[str]

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("https://", "http://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: List[str]) -> List[str]:
        bad = set(v) - SUPPORTED_EVENTS
        if bad:
            raise ValueError(f"Unknown events: {bad}. Supported: {SUPPORTED_EVENTS}")
        return v


class WebhookOut(BaseModel):
    id: int
    url: str
    events: List[str]
    is_active: bool
    failure_count: int
    last_triggered_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class DeliveryOut(BaseModel):
    id: int
    event: str
    attempt: int
    success: bool
    status_code: Optional[int]
    delivered_at: str

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=WebhookOut, status_code=201)
async def register_webhook(
    body: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new webhook endpoint."""
    secret = secrets.token_hex(32)
    webhook = Webhook(
        user_id=current_user.id,
        url=body.url,
        secret=secret,
        events=body.events,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    # Return the secret only once at creation time
    result = _to_out(webhook)
    result["secret"] = secret  # included only here
    return result


@router.get("", response_model=List[WebhookOut])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all webhooks registered by the current user."""
    webhooks = db.query(Webhook).filter(Webhook.user_id == current_user.id).all()
    return [_to_out(w) for w in webhooks]


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete (deactivate) a webhook."""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id, Webhook.user_id == current_user.id
    ).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(webhook)
    db.commit()


@router.get("/{webhook_id}/deliveries", response_model=List[DeliveryOut])
async def list_deliveries(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent delivery attempts for a webhook."""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id, Webhook.user_id == current_user.id
    ).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    deliveries = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": d.id,
            "event": d.event,
            "attempt": d.attempt,
            "success": d.success,
            "status_code": d.status_code,
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else "",
        }
        for d in deliveries
    ]


# ── Delivery logic ────────────────────────────────────────────────────────────

def _to_out(w: Webhook) -> dict:
    return {
        "id": w.id,
        "url": w.url,
        "events": w.events or [],
        "is_active": w.is_active,
        "failure_count": w.failure_count or 0,
        "last_triggered_at": w.last_triggered_at.isoformat() if w.last_triggered_at else None,
        "created_at": w.created_at.isoformat() if w.created_at else "",
    }


def sign_payload(secret: str, body_bytes: bytes) -> str:
    """Compute HMAC-SHA256 signature for webhook body."""
    return hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()


def deliver_webhook_sync(
    db: Session,
    webhook: Webhook,
    event: str,
    data: dict,
    attempt: int = 1,
) -> bool:
    """
    Deliver a single webhook event synchronously (called from the job runner).
    Records delivery attempt in WebhookDelivery table.
    Returns True on success.
    """
    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    body_bytes = json.dumps(payload).encode()
    signature = sign_payload(webhook.secret, body_bytes)

    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event=event,
        payload=payload,
        attempt=attempt,
        success=False,
    )

    try:
        req = urllib.request.Request(
            webhook.url,
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Mindstream-Signature": signature,
                "X-Mindstream-Event": event,
                "User-Agent": "Mindstream-Webhooks/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            response_body = resp.read(500).decode(errors="replace")

        delivery.status_code = status_code
        delivery.response_body = response_body
        delivery.success = 200 <= status_code < 300

    except Exception as exc:
        delivery.status_code = None
        delivery.response_body = str(exc)
        delivery.success = False

    db.add(delivery)

    # Update webhook state
    webhook.last_triggered_at = datetime.now(timezone.utc)
    if delivery.success:
        webhook.failure_count = 0
    else:
        webhook.failure_count = (webhook.failure_count or 0) + 1
        if webhook.failure_count >= 5:
            webhook.is_active = False  # auto-disable after 5 consecutive failures

    db.commit()
    return delivery.success


def fire_event(db: Session, user_id: int, event: str, data: dict) -> None:
    """
    Enqueue webhook delivery jobs for all active webhooks subscribed to `event`.
    Called from episode/memo status update code.
    """
    from saas.jobs.runner import enqueue_job

    webhooks = db.query(Webhook).filter(
        Webhook.user_id == user_id,
        Webhook.is_active == True,  # noqa: E712
    ).all()

    for webhook in webhooks:
        subscribed = webhook.events or []
        if event in subscribed or "*" in subscribed:
            enqueue_job(
                db=db,
                job_type="deliver_webhook",
                payload={
                    "webhook_id": webhook.id,
                    "event": event,
                    "data": data,
                    "attempt": 1,
                },
            )
