from __future__ import annotations

from collections.abc import Sequence
import re
import uuid
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Job, RSSSource, RankingRule, User
from schemas import (
    JobCreate,
    JobRead,
    JobUpdate,
    ProfileRead,
    ProfileUpdate,
    RSSSourceCreate,
    RSSSourceRead,
    RSSSourceUpdate,
    RankingRuleCreate,
    RankingRuleRead,
    RankingRuleUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)
from services.rss_service import fetch_and_rank_jobs


class RSSFetchRequest(BaseModel):
    user_id: int
    rss_source_id: Optional[int] = None
    url: Optional[str] = None
    limit: int = Field(default=25, ge=1, le=200)


def create_app() -> FastAPI:
    app = FastAPI(title="ResumeTracker API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        _ensure_sqlite_schema()
        Base.metadata.create_all(bind=engine)

    def _ensure_sqlite_schema() -> None:
        import os
        import sqlite3

        db_path = os.path.join(os.path.dirname(__file__), "jobs.db")
        if not os.path.exists(db_path):
            return

        required: dict[str, set[str]] = {
            "users": {"id", "email", "profile_summary", "profile_updated_at"},
            "ranking_rules": {"id", "user_id", "attribute", "condition", "match_value", "weight"},
        }

        try:
            conn = sqlite3.connect(db_path)
            try:
                for table, cols in required.items():
                    cur = conn.execute(f"PRAGMA table_info({table})")
                    present = {row[1] for row in cur.fetchall()}
                    if not cols.issubset(present):
                        conn.close()
                        os.remove(db_path)
                        return
            finally:
                conn.close()
        except Exception:
            return

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
    def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        obj = User(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def _extract_profile_fields(text: str) -> dict[str, Optional[str]]:
        raw = (text or "").strip()
        if not raw:
            return {"full_name": None, "email": None, "phone": None}

        email_match = re.search(r"([A-Za-z0-9._%+]+@[A-Za-z0-9.]+\.[A-Za-z]{2,})", raw)
        phone_match = re.search(r"(\+?1\s*)?(\(?\d{3}\)?[\s.]?)\d{3}[\s.]?\d{4}", raw)

        first_line = raw.splitlines()[0].strip() if raw.splitlines() else ""
        name_guess = first_line if 2 <= len(first_line.split()) <= 5 and len(first_line) <= 64 else None

        phone = None
        try:
            phone = phone_match.group(0).strip() if phone_match else None
        except Exception:
            phone = None

        return {
            "full_name": name_guess,
            "email": email_match.group(1).strip() if email_match else None,
            "phone": phone,
        }

    def _read_resume_text(file: UploadFile) -> str:
        import io

        filename = (file.filename or "").lower()
        data = file.file.read()
        if not data:
            return ""

        if filename.endswith(".txt"):
            try:
                return data.decode("utf-8", errors="ignore")
            except Exception:
                return ""

        if filename.endswith(".pdf"):
            try:
                from pypdf import PdfReader

                reader = PdfReader(io.BytesIO(data))
                parts: list[str] = []
                for page in reader.pages:
                    t = page.extract_text() or ""
                    if t:
                        parts.append(t)
                return "\n".join(parts)
            except Exception:
                return ""

        if filename.endswith(".docx"):
            try:
                import docx

                doc = docx.Document(io.BytesIO(data))
                parts = [p.text for p in doc.paragraphs if p.text]
                return "\n".join(parts)
            except Exception:
                return ""

        return ""

    @app.get("/users", response_model=list[UserRead])
    def list_users(db: Session = Depends(get_db)) -> Sequence[User]:
        return db.query(User).order_by(User.id.asc()).all()

    @app.get("/users/{user_id}", response_model=UserRead)
    def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
        obj = db.get(User, user_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return obj

    @app.put("/users/{user_id}", response_model=UserRead)
    def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
        obj = db.get(User, user_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        update = payload.model_dump(exclude_unset=True)
        if "email" in update:
            existing = db.query(User).filter(User.email == update["email"]).first()
            if existing is not None and existing.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        for k, v in update.items():
            setattr(obj, k, v)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def _build_profile_summary(*, user: User, resume_text: Optional[str]) -> str:
        lines: list[str] = []

        def add(label: str, value: Optional[str]) -> None:
            v = (value or "").strip()
            if v:
                lines.append(f"{label}: {v}")

        add("Name", user.full_name)
        add("Email", user.email)
        add("Phone", user.phone)
        add("Location", user.location)
        add("Headline", user.headline)
        add("LinkedIn", user.linkedin_url)
        add("Portfolio", user.portfolio_url)
        add("GitHub", user.github_url)
        add("Resume", user.resume_url)

        text = (resume_text or "").strip()
        if text:
            lines.append("")
            lines.append("Resume text")
            snippet = text[:1500].strip()
            lines.append(snippet)

        return "\n".join(lines).strip() or "No profile data saved"

    @app.post("/users/{user_id}/profile", response_model=ProfileRead)
    def update_profile(user_id: int, payload: ProfileUpdate, db: Session = Depends(get_db)) -> ProfileRead:
        from datetime import datetime

        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        update = payload.model_dump(exclude_unset=True)
        resume_text = update.pop("resume_text", None)

        if "email" in update and update["email"] is not None:
            existing = db.query(User).filter(User.email == update["email"]).first()
            if existing is not None and existing.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        for k, v in update.items():
            setattr(user, k, v)

        user.profile_summary = _build_profile_summary(user=user, resume_text=resume_text)
        user.profile_updated_at = datetime.utcnow()

        db.add(user)
        db.commit()
        db.refresh(user)

        if not user.profile_updated_at:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")

        return ProfileRead(
            user_id=user.id,
            profile_summary=str(user.profile_summary or ""),
            profile_updated_at=user.profile_updated_at,
        )

    @app.post("/profile_from_resume", response_model=ProfileRead)
    def profile_from_resume(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ProfileRead:
        from datetime import datetime

        resume_text = _read_resume_text(file)
        fields = _extract_profile_fields(resume_text)

        generated_email = fields.get("email") or f"user{uuid.uuid4().hex}@example.com"
        existing = db.query(User).filter(User.email == generated_email).first()
        if existing is None:
            user = User(email=generated_email)
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user = existing

        if fields.get("full_name"):
            user.full_name = fields["full_name"]
        if fields.get("phone"):
            user.phone = fields["phone"]

        user.resume_url = file.filename
        user.profile_summary = _build_profile_summary(user=user, resume_text=resume_text)
        user.profile_updated_at = datetime.utcnow()

        db.add(user)
        db.commit()
        db.refresh(user)

        if not user.profile_updated_at:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")

        return ProfileRead(
            user_id=user.id,
            profile_summary=str(user.profile_summary or ""),
            profile_updated_at=user.profile_updated_at,
        )

    @app.get("/users/{user_id}/profile", response_model=ProfileRead)
    def view_profile(user_id: int, db: Session = Depends(get_db)) -> ProfileRead:
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not user.profile_summary or not user.profile_updated_at:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not set")

        return ProfileRead(
            user_id=user.id,
            profile_summary=str(user.profile_summary),
            profile_updated_at=user.profile_updated_at,
        )

    @app.get("/job_attributes")
    def job_attributes() -> list[dict[str, str]]:
        return [
            {"value": "title", "label": "Title"},
            {"value": "company", "label": "Company"},
            {"value": "description", "label": "Role requirement"},
        ]

    class ReplaceRulesRequest(BaseModel):
        user_id: int
        rules: list[RankingRuleCreate]

    @app.post("/ranking_rules/replace", response_model=list[RankingRuleRead])
    def replace_ranking_rules(payload: ReplaceRulesRequest, db: Session = Depends(get_db)) -> Sequence[RankingRule]:
        user = db.get(User, payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist")

        db.query(RankingRule).filter(RankingRule.user_id == payload.user_id).delete()
        created: list[RankingRule] = []
        for rule in payload.rules:
            obj = RankingRule(**rule.model_dump())
            db.add(obj)
            created.append(obj)

        db.commit()
        for obj in created:
            db.refresh(obj)
        return created

    @app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_user(user_id: int, db: Session = Depends(get_db)) -> Response:
        obj = db.get(User, user_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        db.delete(obj)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/ranking_rules", response_model=RankingRuleRead, status_code=status.HTTP_201_CREATED)
    def create_ranking_rule(payload: RankingRuleCreate, db: Session = Depends(get_db)) -> RankingRule:
        user = db.get(User, payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist")
        obj = RankingRule(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @app.get("/ranking_rules", response_model=list[RankingRuleRead])
    def list_ranking_rules(db: Session = Depends(get_db)) -> Sequence[RankingRule]:
        return db.query(RankingRule).order_by(RankingRule.id.asc()).all()

    @app.get("/ranking_rules/{rule_id}", response_model=RankingRuleRead)
    def get_ranking_rule(rule_id: int, db: Session = Depends(get_db)) -> RankingRule:
        obj = db.get(RankingRule, rule_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ranking rule not found")
        return obj

    @app.put("/ranking_rules/{rule_id}", response_model=RankingRuleRead)
    def update_ranking_rule(
        rule_id: int,
        payload: RankingRuleUpdate,
        db: Session = Depends(get_db),
    ) -> RankingRule:
        obj = db.get(RankingRule, rule_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ranking rule not found")
        update = payload.model_dump(exclude_unset=True)
        for k, v in update.items():
            setattr(obj, k, v)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @app.delete("/ranking_rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_ranking_rule(rule_id: int, db: Session = Depends(get_db)) -> Response:
        obj = db.get(RankingRule, rule_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ranking rule not found")
        db.delete(obj)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/rss_sources", response_model=RSSSourceRead, status_code=status.HTTP_201_CREATED)
    def create_rss_source(payload: RSSSourceCreate, db: Session = Depends(get_db)) -> RSSSource:
        user = db.get(User, payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist")
        obj = RSSSource(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @app.get("/rss_sources", response_model=list[RSSSourceRead])
    def list_rss_sources(db: Session = Depends(get_db)) -> Sequence[RSSSource]:
        return db.query(RSSSource).order_by(RSSSource.id.asc()).all()

    @app.get("/rss_sources/{source_id}", response_model=RSSSourceRead)
    def get_rss_source(source_id: int, db: Session = Depends(get_db)) -> RSSSource:
        obj = db.get(RSSSource, source_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found")
        return obj

    @app.put("/rss_sources/{source_id}", response_model=RSSSourceRead)
    def update_rss_source(
        source_id: int,
        payload: RSSSourceUpdate,
        db: Session = Depends(get_db),
    ) -> RSSSource:
        obj = db.get(RSSSource, source_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found")
        update = payload.model_dump(exclude_unset=True)
        for k, v in update.items():
            setattr(obj, k, v)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @app.delete("/rss_sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_rss_source(source_id: int, db: Session = Depends(get_db)) -> Response:
        obj = db.get(RSSSource, source_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found")
        db.delete(obj)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/rss/fetch", response_model=list[JobRead], status_code=status.HTTP_201_CREATED)
    def fetch_rss(payload: RSSFetchRequest, db: Session = Depends(get_db)) -> Sequence[Job]:
        rss_url = payload.url
        rss_source_id = payload.rss_source_id

        if rss_url is None and rss_source_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL or RSS source id is required")

        if rss_url is None and rss_source_id is not None:
            src = db.get(RSSSource, rss_source_id)
            if src is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found")
            if src.user_id != payload.user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RSS source does not match user")
            rss_url = src.url

        created = fetch_and_rank_jobs(
            db,
            user_id=payload.user_id,
            rss_url=str(rss_url),
            rss_source_id=rss_source_id,
            limit=payload.limit,
        )
        return created

    @app.post("/jobs", response_model=JobRead, status_code=status.HTTP_201_CREATED)
    def create_job(payload: JobCreate, db: Session = Depends(get_db)) -> Job:
        user = db.get(User, payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not exist")
        if payload.rss_source_id is not None:
            rss_source = db.get(RSSSource, payload.rss_source_id)
            if rss_source is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RSS source does not exist")
        if payload.ranking_rule_id is not None:
            ranking_rule = db.get(RankingRule, payload.ranking_rule_id)
            if ranking_rule is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ranking rule does not exist")
        obj = Job(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @app.get("/jobs", response_model=list[JobRead])
    def list_jobs(db: Session = Depends(get_db)) -> Sequence[Job]:
        return db.query(Job).order_by(Job.id.asc()).all()

    @app.get("/jobs/{job_id}", response_model=JobRead)
    def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
        obj = db.get(Job, job_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return obj

    @app.put("/jobs/{job_id}", response_model=JobRead)
    def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db)) -> Job:
        obj = db.get(Job, job_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        update = payload.model_dump(exclude_unset=True)
        if "rss_source_id" in update and update["rss_source_id"] is not None:
            rss_source = db.get(RSSSource, update["rss_source_id"])
            if rss_source is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RSS source does not exist")
        if "ranking_rule_id" in update and update["ranking_rule_id"] is not None:
            ranking_rule = db.get(RankingRule, update["ranking_rule_id"])
            if ranking_rule is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ranking rule does not exist")
        for k, v in update.items():
            setattr(obj, k, v)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @app.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_job(job_id: int, db: Session = Depends(get_db)) -> Response:
        obj = db.get(Job, job_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        db.delete(obj)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()

