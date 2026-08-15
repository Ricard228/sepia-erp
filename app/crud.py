"""Fabrique de routeurs CRUD génériques + utilitaires de (dé)sérialisation."""
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuditLog, Project, User
from .security import can_edit, current_user

READONLY_FIELDS = {"id", "created_at", "updated_at"}


# ---------------------------------------------------------------------------
# Sérialisation
# ---------------------------------------------------------------------------
def serialize(obj, extra: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convertit une instance SQLAlchemy en dict JSON-compatible."""
    if obj is None:
        return {}
    data: Dict[str, Any] = {}
    for column in sa_inspect(obj.__class__).columns:
        value = getattr(obj, column.key)
        if isinstance(value, (datetime,)):
            value = value.isoformat(timespec="seconds")
        elif isinstance(value, date):
            value = value.isoformat()
        data[column.key] = value
    for name in extra or []:
        try:
            data[name] = getattr(obj, name)
        except Exception:
            data[name] = None
    return data


def serialize_many(items, extra: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    return [serialize(item, extra) for item in items]


# ---------------------------------------------------------------------------
# Désérialisation / coercition
# ---------------------------------------------------------------------------
def _coerce(column, value):
    try:
        py_type = column.type.python_type
    except NotImplementedError:  # colonnes JSON : valeur transmise telle quelle
        return value
    if value is None:
        return None
    if isinstance(value, str) and not value.strip() and py_type is not str:
        return None
    if py_type is date and isinstance(value, str):
        return date.fromisoformat(value[:10])
    if py_type is datetime and isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", ""))
    if py_type is bool:
        if isinstance(value, str):
            return value.lower() in ("1", "true", "oui", "yes", "on")
        return bool(value)
    if py_type is int and isinstance(value, str):
        return int(float(value))
    if py_type is float and isinstance(value, str):
        return float(value.replace(",", ".").replace(" ", ""))
    return value


def apply_payload(obj, payload: Dict[str, Any], model: Type) -> None:
    """Applique un dict sur l'instance, en ignorant les champs inconnus/protégés."""
    columns = {c.key: c for c in sa_inspect(model).columns}
    for key, value in (payload or {}).items():
        if key in READONLY_FIELDS or key not in columns:
            continue
        try:
            setattr(obj, key, _coerce(columns[key], value))
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=f"Valeur invalide pour « {key} » : {exc}")


def log_action(db: Session, user: User, action: str, entity: str, entity_id: int,
               project_id: Optional[int] = None, detail: str = "") -> None:
    db.add(AuditLog(user_email=user.email, action=action, entity=entity,
                    entity_id=entity_id, project_id=project_id, detail=detail[:500]))


def ensure_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return project


# ---------------------------------------------------------------------------
# Routeur CRUD générique
# ---------------------------------------------------------------------------
def make_crud_router(model: Type, prefix: str, tag: str, *,
                     project_scoped: bool = True,
                     order_by: Optional[str] = None,
                     computed: Optional[List[str]] = None,
                     search_fields: Optional[List[str]] = None) -> APIRouter:
    """Génère les 5 opérations CRUD standard pour une entité du modèle."""
    router = APIRouter(prefix=prefix, tags=[tag])
    computed = computed or []
    entity_name = model.__name__

    @router.get("")
    def list_items(project_id: Optional[int] = Query(None),
                   q: Optional[str] = Query(None),
                   parent_field: Optional[str] = Query(None),
                   parent_id: Optional[int] = Query(None),
                   limit: int = Query(2000, le=10000),
                   db: Session = Depends(get_db),
                   user: User = Depends(current_user)):
        query = db.query(model)
        if project_scoped and project_id:
            query = query.filter(model.project_id == project_id)
        if parent_field and parent_id and hasattr(model, parent_field):
            query = query.filter(getattr(model, parent_field) == parent_id)
        if q and search_fields:
            from sqlalchemy import or_
            pattern = f"%{q}%"
            query = query.filter(or_(*[getattr(model, f).ilike(pattern) for f in search_fields]))
        if order_by and hasattr(model, order_by):
            query = query.order_by(getattr(model, order_by))
        return serialize_many(query.limit(limit).all(), computed)

    @router.get("/{item_id}")
    def get_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{entity_name} introuvable.")
        return serialize(obj, computed)

    @router.post("", status_code=201)
    def create_item(payload: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(can_edit)):
        obj = model()
        apply_payload(obj, payload, model)
        if project_scoped and not getattr(obj, "project_id", None):
            raise HTTPException(status_code=422, detail="Le champ project_id est obligatoire.")
        db.add(obj)
        db.flush()
        log_action(db, user, "CREATE", entity_name, obj.id, getattr(obj, "project_id", None))
        db.commit()
        db.refresh(obj)
        return serialize(obj, computed)

    @router.put("/{item_id}")
    def update_item(item_id: int, payload: Dict[str, Any],
                    db: Session = Depends(get_db), user: User = Depends(can_edit)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{entity_name} introuvable.")
        apply_payload(obj, payload, model)
        log_action(db, user, "UPDATE", entity_name, obj.id, getattr(obj, "project_id", None))
        db.commit()
        db.refresh(obj)
        return serialize(obj, computed)

    @router.delete("/{item_id}")
    def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(can_edit)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{entity_name} introuvable.")
        project_id = getattr(obj, "project_id", None)
        db.delete(obj)
        log_action(db, user, "DELETE", entity_name, item_id, project_id)
        db.commit()
        return {"deleted": item_id}

    @router.post("/bulk", status_code=201)
    def bulk_create(payload: List[Dict[str, Any]],
                    db: Session = Depends(get_db), user: User = Depends(can_edit)):
        created = []
        for row in payload:
            obj = model()
            apply_payload(obj, row, model)
            db.add(obj)
            created.append(obj)
        db.flush()
        log_action(db, user, "BULK_CREATE", entity_name, 0,
                   getattr(created[0], "project_id", None) if created else None,
                   f"{len(created)} enregistrements")
        db.commit()
        return serialize_many(created, computed)

    return router
