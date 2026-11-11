from datetime import date, datetime
from typing import Optional, Sequence


DEFAULT_EXPIRING_WITHIN_DAYS = 3
DEFAULT_LOW_STOCK_THRESHOLD = 2
DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y")


class InventoryAlertService:
    """Apply expiry and stock alert rules to inventory records."""

    @staticmethod
    def _parse_use_by(value) -> Optional[datetime]:
        if value is None or isinstance(value, datetime):
            return value
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(value, date_format)
            except (TypeError, ValueError):
                continue
        return None

    def get_alerts(
        self,
        records: Sequence[dict],
        today: Optional[date] = None,
        expiring_within_days: int = DEFAULT_EXPIRING_WITHIN_DAYS,
        low_stock_threshold: int = DEFAULT_LOW_STOCK_THRESHOLD,
    ) -> dict:
        """Return date-based expiry and quantity alerts without changing records."""
        today = date.today() if today is None else today
        if isinstance(today, datetime):
            today = today.date()
        if not isinstance(today, date):
            raise TypeError("today must be a date.")
        if (
            type(expiring_within_days) is not int
            or expiring_within_days < 0
            or type(low_stock_threshold) is not int
            or low_stock_threshold < 0
        ):
            raise ValueError("Alert thresholds must be non-negative integers.")

        alerts = {
            "expired": [],
            "expiring_soon": [],
            "low_stock": [],
            "unknown_expiry": [],
        }
        for item_id, record in enumerate(records, start=1):
            item = {
                "id": item_id,
                "record": record,
                "days_remaining": None,
            }
            use_by = self._parse_use_by(record.get("use-by"))
            if use_by is None:
                alerts["unknown_expiry"].append(item)
            else:
                if isinstance(use_by, datetime):
                    use_by = use_by.date()
                days_remaining = (use_by - today).days
                item["days_remaining"] = days_remaining
                if days_remaining < 0:
                    alerts["expired"].append(item)
                elif days_remaining <= expiring_within_days:
                    alerts["expiring_soon"].append(item)

            quantity = record.get("quantity")
            if quantity is not None and quantity <= low_stock_threshold:
                alerts["low_stock"].append(item)
        return alerts
