from typing import List, Optional
from datetime import datetime, date
from sqlmodel import select, and_, desc
from app.database import get_session
from app.models import Sneeze, SneezeCreate, SneezeUpdate, SeverityLevel


class SneezeService:
    """Service for sneeze-related operations"""

    @staticmethod
    def create_sneeze(user_id: int, sneeze_data: SneezeCreate) -> Optional[Sneeze]:
        """Create a new sneeze record for a user"""
        with get_session() as session:
            new_sneeze = Sneeze(
                user_id=user_id, severity=sneeze_data.severity, notes=sneeze_data.notes, timestamp=datetime.utcnow()
            )

            session.add(new_sneeze)
            session.commit()
            session.refresh(new_sneeze)
            return new_sneeze

    @staticmethod
    def get_user_sneezes(user_id: int, limit: Optional[int] = None) -> List[Sneeze]:
        """Get all sneezes for a user, ordered by timestamp descending"""
        with get_session() as session:
            query = select(Sneeze).where(Sneeze.user_id == user_id).order_by(desc(Sneeze.timestamp))

            if limit is not None:
                query = query.limit(limit)

            return list(session.exec(query).all())

    @staticmethod
    def get_sneezes_by_month(user_id: int, year: int, month: int) -> List[Sneeze]:
        """Get sneezes for a specific month and year"""
        with get_session() as session:
            # Create start and end dates for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            query = (
                select(Sneeze)
                .where(and_(Sneeze.user_id == user_id, Sneeze.timestamp >= start_date, Sneeze.timestamp < end_date))
                .order_by(desc(Sneeze.timestamp))
            )

            return list(session.exec(query).all())

    @staticmethod
    def get_sneeze_by_id(sneeze_id: int, user_id: int) -> Optional[Sneeze]:
        """Get a specific sneeze by ID, ensuring it belongs to the user"""
        with get_session() as session:
            return session.exec(select(Sneeze).where(and_(Sneeze.id == sneeze_id, Sneeze.user_id == user_id))).first()

    @staticmethod
    def update_sneeze(sneeze_id: int, user_id: int, update_data: SneezeUpdate) -> Optional[Sneeze]:
        """Update a sneeze record"""
        with get_session() as session:
            sneeze = session.exec(select(Sneeze).where(and_(Sneeze.id == sneeze_id, Sneeze.user_id == user_id))).first()

            if sneeze is None:
                return None

            if update_data.severity is not None:
                sneeze.severity = update_data.severity

            if update_data.notes is not None:
                sneeze.notes = update_data.notes

            session.add(sneeze)
            session.commit()
            session.refresh(sneeze)
            return sneeze

    @staticmethod
    def delete_sneeze(sneeze_id: int, user_id: int) -> bool:
        """Delete a sneeze record"""
        with get_session() as session:
            sneeze = session.exec(select(Sneeze).where(and_(Sneeze.id == sneeze_id, Sneeze.user_id == user_id))).first()

            if sneeze is None:
                return False

            session.delete(sneeze)
            session.commit()
            return True

    @staticmethod
    def get_sneeze_stats(user_id: int) -> dict:
        """Get sneeze statistics for a user"""
        with get_session() as session:
            sneezes = session.exec(select(Sneeze).where(Sneeze.user_id == user_id)).all()

            if not sneezes:
                return {
                    "total_count": 0,
                    "severity_counts": {severity: 0 for severity in SeverityLevel},
                    "today_count": 0,
                    "this_month_count": 0,
                }

            total_count = len(sneezes)
            severity_counts = {severity: 0 for severity in SeverityLevel}

            today = date.today()
            today_start = datetime(today.year, today.month, today.day)
            today_count = 0

            month_start = datetime(today.year, today.month, 1)
            month_count = 0

            for sneeze in sneezes:
                severity_counts[sneeze.severity] += 1

                if sneeze.timestamp >= today_start:
                    today_count += 1

                if sneeze.timestamp >= month_start:
                    month_count += 1

            return {
                "total_count": total_count,
                "severity_counts": severity_counts,
                "today_count": today_count,
                "this_month_count": month_count,
            }
