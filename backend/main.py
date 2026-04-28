from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Job, RSSSource, RankingRule, User
from schemas import (
    JobCreate,
    JobRead,
    JobUpdate,
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

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

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

