from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

_IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LIMIT_MODES = {"HARD_LIMIT", "RESERVABLE_LIMIT", "OBSERVATION_ONLY"}
_ROOT_AUTHORITY_TYPES = {
    "OWNER_APPROVED_RESOURCE_AUTHORITY",
    "AUTONOMY_ENVELOPE",
    "OTHER_DURABLE_RESOURCE_AUTHORITY",
}
_PARENT_AUTHORITY_TYPE = "PARENT_RESOURCE_GRANT"
_FINALIZATION_PURPOSES = {
    "RESULT_RECONCILIATION",
    "DURABLE_PARTIAL_OUTPUT",
    "FINAL_ACCOUNTING",
    "CONTROL_HANDOFF",
}
_MODE_NARROWING = {
    "HARD_LIMIT": {"HARD_LIMIT", "RESERVABLE_LIMIT", "OBSERVATION_ONLY"},
    "RESERVABLE_LIMIT": {"RESERVABLE_LIMIT", "OBSERVATION_ONLY"},
    "OBSERVATION_ONLY": {"OBSERVATION_ONLY"},
}
_SCOPE_EVIDENCE_KEYS = {"child_scope_ref", "parent_scope_ref", "evidence_ref"}


class ResourceLedgerError(Exception):
    """Base error for bounded resource-ledger operations."""


class InvalidGrant(ResourceLedgerError):
    pass


class AuthorityViolation(ResourceLedgerError):
    pass


class InsufficientCapacity(ResourceLedgerError):
    pass


class IdempotencyConflict(ResourceLedgerError):
    pass


class InvalidReservationTransition(ResourceLedgerError):
    pass


class GrantExpired(ResourceLedgerError):
    pass


def _coeff_exp(value: Decimal) -> tuple[int, int]:
    """Return exact integer coefficient/exponent, independent of Decimal context."""
    if not value.is_finite():
        raise ResourceLedgerError("non-finite Decimal is not valid authority state")
    sign, digits, exponent = value.as_tuple()
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign:
        coefficient = -coefficient
    if coefficient == 0:
        return 0, 0
    while coefficient % 10 == 0:
        coefficient //= 10
        exponent += 1
    return coefficient, exponent


def _decimal_from_coeff_exp(coefficient: int, exponent: int) -> Decimal:
    if coefficient == 0:
        return Decimal("0")
    sign = 1 if coefficient < 0 else 0
    digits = tuple(int(ch) for ch in str(abs(coefficient)))
    return Decimal((sign, digits, exponent))


def _exact_sum(values: list[Decimal] | tuple[Decimal, ...]) -> Decimal:
    pairs = [_coeff_exp(v) for v in values]
    if not pairs:
        return Decimal("0")
    common_exp = min(exp for _, exp in pairs)
    total = sum(coeff * (10 ** (exp - common_exp)) for coeff, exp in pairs)
    return _decimal_from_coeff_exp(total, common_exp)


def _exact_subtract(first: Decimal, *rest: Decimal) -> Decimal:
    pairs = [_coeff_exp(first)] + [(-c, e) for c, e in map(_coeff_exp, rest)]
    common_exp = min(exp for _, exp in pairs)
    total = sum(coeff * (10 ** (exp - common_exp)) for coeff, exp in pairs)
    return _decimal_from_coeff_exp(total, common_exp)


def _exact_compare(left: Decimal, right: Decimal) -> int:
    lc, le = _coeff_exp(left)
    rc, rexp = _coeff_exp(right)
    common_exp = min(le, rexp)
    li = lc * (10 ** (le - common_exp))
    ri = rc * (10 ** (rexp - common_exp))
    return (li > ri) - (li < ri)


class ResourceLedger:
    """Transactional shared-file implementation of frozen RESOURCE_GRANT authority."""

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = 5000) -> None:
        raw = str(database_path)
        lowered = raw.lower()
        if raw == ":memory:" or ":memory:" in lowered or (
            lowered.startswith("file:") and "mode=memory" in lowered
        ):
            raise ResourceLedgerError(
                "authoritative resource ledger requires one shared on-disk SQLite file"
            )
        if not raw.strip():
            raise ResourceLedgerError("database path must be non-empty")
        if isinstance(busy_timeout_ms, bool) or not isinstance(busy_timeout_ms, int) or busy_timeout_ms <= 0:
            raise ResourceLedgerError("busy_timeout_ms must be a positive integer")
        self.database_path = raw
        self.busy_timeout_ms = busy_timeout_ms
        self._uri = lowered.startswith("file:")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
            uri=self._uri,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        return conn

    def initialize(self) -> None:
        if not self._uri:
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS grants (
                    grant_id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    grant_json TEXT NOT NULL,
                    parent_grant_id TEXT NULL REFERENCES grants(grant_id),
                    authority_type TEXT NOT NULL,
                    scope_ref TEXT NOT NULL,
                    candidate_ref TEXT NULL,
                    route_ref TEXT NULL,
                    attempt_limit INTEGER NULL,
                    valid_until TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS grant_resource_classes (
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id) ON DELETE CASCADE,
                    resource_class TEXT NOT NULL,
                    PRIMARY KEY (grant_id, resource_class)
                );

                CREATE TABLE IF NOT EXISTS grant_limits (
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id) ON DELETE CASCADE,
                    resource_class TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    limit_mode TEXT NOT NULL,
                    ordinary_limit TEXT NULL,
                    finalization_reserve TEXT NULL,
                    PRIMARY KEY (grant_id, resource_class, dimension)
                );

                CREATE TABLE IF NOT EXISTS grant_finalization_purposes (
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id) ON DELETE CASCADE,
                    purpose TEXT NOT NULL,
                    PRIMARY KEY (grant_id, purpose)
                );

                CREATE TABLE IF NOT EXISTS grant_scope_relation_evidence (
                    child_grant_id TEXT PRIMARY KEY REFERENCES grants(grant_id) ON DELETE CASCADE,
                    child_scope_ref TEXT NOT NULL,
                    parent_scope_ref TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id TEXT PRIMARY KEY,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    resource_class TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    pool TEXT NOT NULL,
                    purpose TEXT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NULL,
                    status TEXT NOT NULL,
                    committed_quantity TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS reservation_allocations (
                    reservation_id TEXT NOT NULL REFERENCES reservations(reservation_id) ON DELETE CASCADE,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    resource_class TEXT NOT NULL,
                    dimension TEXT NOT NULL,
                    pool TEXT NOT NULL,
                    reserved TEXT NOT NULL,
                    committed TEXT NOT NULL,
                    PRIMARY KEY (reservation_id, grant_id)
                );

                CREATE TABLE IF NOT EXISTS attempt_claims (
                    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    operation_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (grant_id, operation_id)
                );

                CREATE TABLE IF NOT EXISTS attempt_allocations (
                    claim_id INTEGER NOT NULL REFERENCES attempt_claims(claim_id) ON DELETE CASCADE,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id),
                    PRIMARY KEY (claim_id, grant_id)
                );

                CREATE TABLE IF NOT EXISTS idempotency_operations (
                    idempotency_key TEXT PRIMARY KEY,
                    operation_kind TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    result_json TEXT NOT NULL
                );
                """
            )
        finally:
            conn.close()

    @staticmethod
    def _require_text(value: Any, field: str, *, nullable: bool = False) -> str | None:
        if value is None and nullable:
            return None
        if not isinstance(value, str) or not value:
            raise InvalidGrant(f"{field} must be a non-empty string" + (" or null" if nullable else ""))
        return value

    @staticmethod
    def _require_exact_keys(value: Any, expected: set[str], field: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise InvalidGrant(f"{field} must be an object")
        keys = set(value)
        if keys != expected:
            missing = sorted(expected - keys)
            extra = sorted(keys - expected)
            raise InvalidGrant(f"{field} fields invalid: missing={missing}, extra={extra}")
        return value

    @staticmethod
    def _decimal(value: Any, field: str, *, allow_zero: bool = True) -> Decimal:
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
            raise ResourceLedgerError(f"{field} must be a finite non-negative decimal quantity")
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ResourceLedgerError(f"{field} must be a finite non-negative decimal quantity") from None
        if not result.is_finite() or _exact_compare(result, Decimal("0")) < 0 or (
            not allow_zero and _exact_compare(result, Decimal("0")) == 0
        ):
            comparator = "positive" if not allow_zero else "non-negative"
            raise ResourceLedgerError(f"{field} must be finite and {comparator}")
        return result

    @classmethod
    def _grant_decimal(cls, value: Any, field: str) -> Decimal:
        if isinstance(value, str):
            raise InvalidGrant(f"{field} must be a JSON numeric value, not a string")
        try:
            return cls._decimal(value, field)
        except ResourceLedgerError as exc:
            raise InvalidGrant(str(exc)) from None

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        coefficient, exponent = _coeff_exp(value)
        if coefficient == 0:
            return "0"
        negative = coefficient < 0
        digits = str(abs(coefficient))
        if exponent >= 0:
            text = digits + ("0" * exponent)
        else:
            split = len(digits) + exponent
            if split > 0:
                text = digits[:split] + "." + digits[split:]
            else:
                text = "0." + ("0" * (-split)) + digits
        return ("-" if negative else "") + text

    @staticmethod
    def _parse_datetime(value: Any, field: str, *, nullable: bool = False) -> datetime | None:
        if value is None and nullable:
            return None
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str) and value:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ResourceLedgerError(f"{field} must be a valid timezone-aware datetime") from None
        else:
            raise ResourceLedgerError(f"{field} must be a valid timezone-aware datetime")
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ResourceLedgerError(f"{field} must be timezone-aware")
        return dt.astimezone(timezone.utc)

    @classmethod
    def _grant_datetime(cls, value: Any, field: str) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidGrant(f"{field} must be a date-time string or null")
        try:
            return cls._parse_datetime(value, field)
        except ResourceLedgerError as exc:
            raise InvalidGrant(str(exc)) from None

    @staticmethod
    def _datetime_text(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

    @classmethod
    def _now(cls, value: datetime | str | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        parsed = cls._parse_datetime(value, "now")
        if parsed is None:
            raise ResourceLedgerError("now must be a timezone-aware datetime")
        return parsed

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def _fingerprint(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_json(value).encode("utf-8")).hexdigest()

    @classmethod
    def _validate_grant(cls, grant: Any) -> tuple[dict[str, Any], str]:
        required = {
            "artifact_type", "artifact_id", "produced_by_role", "assignment_id", "input_state_ref",
            "status", "provenance", "related_artifacts", "issued_by", "authority_source",
            "parent_grant_ref", "scope", "limits", "attempt_limit", "valid_until", "finalization_policy",
        }
        obj = cls._require_exact_keys(grant, required, "RESOURCE_GRANT")
        if obj["artifact_type"] != "RESOURCE_GRANT":
            raise InvalidGrant("artifact_type must be RESOURCE_GRANT")
        grant_id = cls._require_text(obj["artifact_id"], "artifact_id")
        if obj["status"] != "AUTHORIZED":
            raise InvalidGrant("status must be AUTHORIZED")
        if obj["issued_by"] != "control-director" or obj["produced_by_role"] != "control-director":
            raise InvalidGrant("RESOURCE_GRANT must be issued and produced by control-director")
        for nullable_name in ("assignment_id", "input_state_ref", "parent_grant_ref"):
            cls._require_text(obj[nullable_name], nullable_name, nullable=True)

        provenance = obj["provenance"]
        if not isinstance(provenance, list) or not provenance:
            raise InvalidGrant("provenance must be a non-empty array")
        if any(not isinstance(x, str) or not x for x in provenance) or len(set(provenance)) != len(provenance):
            raise InvalidGrant("provenance must contain unique non-empty strings")
        related = obj["related_artifacts"]
        if not isinstance(related, list):
            raise InvalidGrant("related_artifacts must be an array")
        if any(not isinstance(x, str) or not x for x in related) or len(set(related)) != len(related):
            raise InvalidGrant("related_artifacts must contain unique non-empty strings")

        authority = cls._require_exact_keys(
            obj["authority_source"], {"authority_type", "authority_ref"}, "authority_source"
        )
        authority_type = authority["authority_type"]
        if authority_type not in _ROOT_AUTHORITY_TYPES | {_PARENT_AUTHORITY_TYPE}:
            raise InvalidGrant("authority_source.authority_type is not recognized")
        cls._require_text(authority["authority_ref"], "authority_source.authority_ref")
        parent_ref = obj["parent_grant_ref"]
        if authority_type == _PARENT_AUTHORITY_TYPE:
            if not isinstance(parent_ref, str) or not parent_ref:
                raise InvalidGrant("PARENT_RESOURCE_GRANT requires parent_grant_ref")
            if authority["authority_ref"] != parent_ref:
                raise InvalidGrant("parent authority_ref must identify parent_grant_ref")
        elif parent_ref is not None:
            raise InvalidGrant("non-parent authority_source requires parent_grant_ref = null")

        scope = cls._require_exact_keys(
            obj["scope"], {"scope_ref", "candidate_ref", "route_ref", "resource_classes"}, "scope"
        )
        cls._require_text(scope["scope_ref"], "scope.scope_ref")
        cls._require_text(scope["candidate_ref"], "scope.candidate_ref", nullable=True)
        cls._require_text(scope["route_ref"], "scope.route_ref", nullable=True)
        classes = scope["resource_classes"]
        if not isinstance(classes, list) or not classes:
            raise InvalidGrant("scope.resource_classes must be non-empty")
        if any(not isinstance(x, str) or _IDENTIFIER.fullmatch(x) is None for x in classes):
            raise InvalidGrant("resource_classes must use canonical identifiers")
        if len(set(classes)) != len(classes):
            raise InvalidGrant("resource_classes must be unique")

        limits = obj["limits"]
        if not isinstance(limits, list) or not limits:
            raise InvalidGrant("limits must be non-empty")
        normalized_limits: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str]] = set()
        for index, raw in enumerate(limits):
            limit = cls._require_exact_keys(
                raw,
                {"resource_class", "dimension", "limit_mode", "ordinary_limit", "finalization_reserve"},
                f"limits[{index}]",
            )
            resource_class = limit["resource_class"]
            dimension = limit["dimension"]
            if not isinstance(resource_class, str) or _IDENTIFIER.fullmatch(resource_class) is None:
                raise InvalidGrant("limit resource_class must be a canonical identifier")
            if resource_class not in classes:
                raise InvalidGrant("limit resource_class must belong to grant scope")
            if not isinstance(dimension, str) or _IDENTIFIER.fullmatch(dimension) is None:
                raise InvalidGrant("limit dimension must be a canonical identifier")
            key = (resource_class, dimension)
            if key in seen_keys:
                raise InvalidGrant("duplicate (resource_class, dimension) limit")
            seen_keys.add(key)
            mode = limit["limit_mode"]
            if mode not in _LIMIT_MODES:
                raise InvalidGrant("limit_mode is not recognized")
            if mode == "OBSERVATION_ONLY":
                if limit["ordinary_limit"] is not None or limit["finalization_reserve"] is not None:
                    raise InvalidGrant("OBSERVATION_ONLY requires null capacities")
                ordinary_text = final_text = None
            else:
                ordinary = cls._grant_decimal(limit["ordinary_limit"], f"limits[{index}].ordinary_limit")
                final = cls._grant_decimal(limit["finalization_reserve"], f"limits[{index}].finalization_reserve")
                ordinary_text = cls._decimal_text(ordinary)
                final_text = cls._decimal_text(final)
            normalized_limits.append({
                "resource_class": resource_class,
                "dimension": dimension,
                "limit_mode": mode,
                "ordinary_limit": ordinary_text,
                "finalization_reserve": final_text,
            })

        attempt_limit = obj["attempt_limit"]
        if attempt_limit is not None and (
            isinstance(attempt_limit, bool) or not isinstance(attempt_limit, int) or attempt_limit < 1
        ):
            raise InvalidGrant("attempt_limit must be null or an integer >= 1")
        valid_until = cls._grant_datetime(obj["valid_until"], "valid_until")

        policy = cls._require_exact_keys(
            obj["finalization_policy"], {"protected", "allowed_purposes"}, "finalization_policy"
        )
        if policy["protected"] is not True:
            raise InvalidGrant("finalization_policy.protected must be true")
        purposes = policy["allowed_purposes"]
        if not isinstance(purposes, list) or not purposes:
            raise InvalidGrant("finalization_policy.allowed_purposes must be non-empty")
        if any(x not in _FINALIZATION_PURPOSES for x in purposes) or len(set(purposes)) != len(purposes):
            raise InvalidGrant("finalization_policy.allowed_purposes is invalid")

        normalized = {
            "artifact_type": "RESOURCE_GRANT",
            "artifact_id": grant_id,
            "produced_by_role": "control-director",
            "assignment_id": obj["assignment_id"],
            "input_state_ref": obj["input_state_ref"],
            "status": "AUTHORIZED",
            "provenance": sorted(provenance),
            "related_artifacts": sorted(related),
            "issued_by": "control-director",
            "authority_source": {
                "authority_type": authority_type,
                "authority_ref": authority["authority_ref"],
            },
            "parent_grant_ref": parent_ref,
            "scope": {
                "scope_ref": scope["scope_ref"],
                "candidate_ref": scope["candidate_ref"],
                "route_ref": scope["route_ref"],
                "resource_classes": sorted(classes),
            },
            "limits": sorted(normalized_limits, key=lambda x: (x["resource_class"], x["dimension"])),
            "attempt_limit": attempt_limit,
            "valid_until": cls._datetime_text(valid_until) if valid_until else None,
            "finalization_policy": {
                "protected": True,
                "allowed_purposes": sorted(purposes),
            },
        }
        return normalized, cls._fingerprint(normalized)

    @staticmethod
    def _begin_write(conn: sqlite3.Connection) -> None:
        conn.execute("BEGIN IMMEDIATE")

    @staticmethod
    def _row_grant(conn: sqlite3.Connection, grant_id: str) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM grants WHERE grant_id = ?", (grant_id,)).fetchone()
        if row is None:
            raise AuthorityViolation(f"grant not registered: {grant_id}")
        return row

    @staticmethod
    def _limit_row(conn: sqlite3.Connection, grant_id: str, resource_class: str, dimension: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM grant_limits WHERE grant_id = ? AND resource_class = ? AND dimension = ?",
            (grant_id, resource_class, dimension),
        ).fetchone()
        if row is None:
            raise AuthorityViolation(f"grant {grant_id} has no authority for {resource_class}/{dimension}")
        return row

    @classmethod
    def _ancestry(cls, conn: sqlite3.Connection, grant_id: str) -> list[sqlite3.Row]:
        chain: list[sqlite3.Row] = []
        seen: set[str] = set()
        current: str | None = grant_id
        while current is not None:
            if current in seen:
                raise AuthorityViolation("grant ancestry contains a cycle")
            seen.add(current)
            row = cls._row_grant(conn, current)
            chain.append(row)
            parent = row["parent_grant_id"]
            current = str(parent) if parent is not None else None
        return chain

    @classmethod
    def _grant_expired(cls, grant_row: sqlite3.Row, now: datetime) -> bool:
        raw = grant_row["valid_until"]
        if raw is None:
            return False
        parsed = cls._parse_datetime(str(raw), "valid_until")
        if parsed is None:
            raise AuthorityViolation("stored grant validity is malformed")
        return now >= parsed

    @classmethod
    def _allocation_totals(
        cls,
        conn: sqlite3.Connection,
        grant_id: str,
        resource_class: str,
        dimension: str,
        pool: str,
    ) -> tuple[Decimal, Decimal]:
        rows = conn.execute(
            """
            SELECT reserved, committed
            FROM reservation_allocations
            WHERE grant_id = ? AND resource_class = ? AND dimension = ? AND pool = ?
            """,
            (grant_id, resource_class, dimension, pool),
        ).fetchall()
        reserved = _exact_sum([Decimal(row["reserved"]) for row in rows])
        committed = _exact_sum([Decimal(row["committed"]) for row in rows])
        return reserved, committed

    @classmethod
    def _idempotency_lookup(
        cls, conn: sqlite3.Connection, key: str, operation_kind: str, fingerprint: str
    ) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT operation_kind, fingerprint, result_json FROM idempotency_operations WHERE idempotency_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        if row["operation_kind"] != operation_kind or row["fingerprint"] != fingerprint:
            raise IdempotencyConflict("idempotency key is already bound to a conflicting operation")
        return cls._decode_result(row["result_json"])

    @classmethod
    def _record_idempotency(
        cls,
        conn: sqlite3.Connection,
        key: str,
        operation_kind: str,
        fingerprint: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        result_json = cls._encode_result(result)
        conn.execute(
            "INSERT INTO idempotency_operations(idempotency_key, operation_kind, fingerprint, result_json) VALUES (?, ?, ?, ?)",
            (key, operation_kind, fingerprint, result_json),
        )
        return cls._decode_result(result_json)

    @classmethod
    def _encode_result(cls, result: dict[str, Any]) -> str:
        def convert(value: Any) -> Any:
            if isinstance(value, Decimal):
                return {"__decimal__": cls._decimal_text(value)}
            if isinstance(value, dict):
                return {key: convert(nested) for key, nested in value.items()}
            if isinstance(value, list):
                return [convert(nested) for nested in value]
            return value

        return cls._canonical_json(convert(result))

    @classmethod
    def _decode_result(cls, raw: str) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, dict) and set(value) == {"__decimal__"}:
                return Decimal(value["__decimal__"])
            if isinstance(value, dict):
                return {key: convert(nested) for key, nested in value.items()}
            if isinstance(value, list):
                return [convert(nested) for nested in value]
            return value

        decoded = convert(json.loads(raw))
        if not isinstance(decoded, dict):
            raise ResourceLedgerError("stored idempotency result is malformed")
        return decoded

    @staticmethod
    def _require_id(value: Any, field: str) -> str:
        if not isinstance(value, str) or not value:
            raise ResourceLedgerError(f"{field} must be a non-empty string")
        return value

    @classmethod
    def _validate_scope_evidence(
        cls,
        evidence: Any,
        child_scope_ref: str,
        parent_scope_ref: str,
    ) -> dict[str, str]:
        if not isinstance(evidence, dict) or set(evidence) != _SCOPE_EVIDENCE_KEYS:
            raise AuthorityViolation(
                "different-scope child requires scope relation evidence with child_scope_ref, parent_scope_ref, evidence_ref"
            )
        child = evidence.get("child_scope_ref")
        parent = evidence.get("parent_scope_ref")
        evidence_ref = evidence.get("evidence_ref")
        if not all(isinstance(x, str) and x for x in (child, parent, evidence_ref)):
            raise AuthorityViolation("scope relation evidence fields must be non-empty strings")
        if child != child_scope_ref or parent != parent_scope_ref:
            raise AuthorityViolation("scope relation evidence does not match child/parent scope refs")
        return {
            "child_scope_ref": child,
            "parent_scope_ref": parent,
            "evidence_ref": evidence_ref,
        }

    def register_grant(self, grant: dict[str, Any]) -> dict[str, Any]:
        normalized, fingerprint = self._validate_grant(grant)
        if normalized["authority_source"]["authority_type"] not in _ROOT_AUTHORITY_TYPES:
            raise InvalidGrant("register_grant accepts root durable authority only")
        conn = self._connect()
        try:
            self._begin_write(conn)
            existing = conn.execute(
                "SELECT fingerprint FROM grants WHERE grant_id = ?", (normalized["artifact_id"],)
            ).fetchone()
            if existing is not None:
                if existing["fingerprint"] != fingerprint:
                    raise AuthorityViolation("grant id is already registered with different authority")
                conn.commit()
                return self.get_grant(normalized["artifact_id"])
            self._insert_grant(conn, normalized, fingerprint)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return self.get_grant(normalized["artifact_id"])

    def register_child_grant(
        self,
        grant: dict[str, Any],
        scope_relation_evidence: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        normalized, fingerprint = self._validate_grant(grant)
        if normalized["authority_source"]["authority_type"] != _PARENT_AUTHORITY_TYPE:
            raise InvalidGrant("register_child_grant requires PARENT_RESOURCE_GRANT authority")
        parent_id = normalized["parent_grant_ref"]
        if not isinstance(parent_id, str) or not parent_id:
            raise InvalidGrant("child grant requires parent_grant_ref")
        conn = self._connect()
        try:
            self._begin_write(conn)
            parent_row = self._row_grant(conn, parent_id)
            parent = json.loads(parent_row["grant_json"])
            child_scope = normalized["scope"]["scope_ref"]
            parent_scope = parent["scope"]["scope_ref"]
            evidence: dict[str, str] | None = None
            if child_scope != parent_scope:
                evidence = self._validate_scope_evidence(scope_relation_evidence, child_scope, parent_scope)
            elif scope_relation_evidence is not None:
                raise AuthorityViolation("equal-scope child does not require external scope relation evidence")

            existing = conn.execute(
                "SELECT fingerprint FROM grants WHERE grant_id = ?", (normalized["artifact_id"],)
            ).fetchone()
            if existing is not None:
                if existing["fingerprint"] != fingerprint:
                    raise AuthorityViolation("grant id is already registered with different authority")
                persisted = conn.execute(
                    "SELECT child_scope_ref, parent_scope_ref, evidence_ref FROM grant_scope_relation_evidence WHERE child_grant_id = ?",
                    (normalized["artifact_id"],),
                ).fetchone()
                if evidence is None:
                    if persisted is not None:
                        raise AuthorityViolation("stored equal-scope grant unexpectedly has scope relation evidence")
                else:
                    if persisted is None or dict(persisted) != evidence:
                        raise AuthorityViolation("grant is already registered with conflicting scope relation evidence")
                conn.commit()
                return self.get_grant(normalized["artifact_id"])

            self._enforce_child_narrowing(parent, normalized, evidence is not None)
            self._ancestry(conn, parent_id)
            self._insert_grant(conn, normalized, fingerprint)
            if evidence is not None:
                conn.execute(
                    """
                    INSERT INTO grant_scope_relation_evidence(
                        child_grant_id, child_scope_ref, parent_scope_ref, evidence_ref
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        normalized["artifact_id"],
                        evidence["child_scope_ref"],
                        evidence["parent_scope_ref"],
                        evidence["evidence_ref"],
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return self.get_grant(normalized["artifact_id"])

    @classmethod
    def _enforce_child_narrowing(
        cls,
        parent: dict[str, Any],
        child: dict[str, Any],
        different_scope_proven: bool,
    ) -> None:
        ps = parent["scope"]
        cs = child["scope"]
        if cs["scope_ref"] != ps["scope_ref"] and not different_scope_proven:
            raise AuthorityViolation("child scope is not proven equal to or narrower than parent scope")
        if not set(cs["resource_classes"]).issubset(ps["resource_classes"]):
            raise AuthorityViolation("child resource classes expand parent authority")
        for binding in ("candidate_ref", "route_ref"):
            parent_binding = ps[binding]
            child_binding = cs[binding]
            if parent_binding is not None and child_binding != parent_binding:
                raise AuthorityViolation(f"child {binding} expands or changes parent binding")

        parent_attempt = parent["attempt_limit"]
        child_attempt = child["attempt_limit"]
        if parent_attempt is not None and (child_attempt is None or child_attempt > parent_attempt):
            raise AuthorityViolation("child attempt authority expands parent authority")

        parent_until = cls._grant_datetime(parent["valid_until"], "parent.valid_until")
        child_until = cls._grant_datetime(child["valid_until"], "child.valid_until")
        if parent_until is not None and (child_until is None or child_until > parent_until):
            raise AuthorityViolation("child validity expands parent validity")

        parent_purposes = set(parent["finalization_policy"]["allowed_purposes"])
        child_purposes = set(child["finalization_policy"]["allowed_purposes"])
        if not child_purposes.issubset(parent_purposes):
            raise AuthorityViolation("child finalization purposes expand parent authority")

        parent_limits = {(x["resource_class"], x["dimension"]): x for x in parent["limits"]}
        for child_limit in child["limits"]:
            key = (child_limit["resource_class"], child_limit["dimension"])
            parent_limit = parent_limits.get(key)
            if parent_limit is None:
                raise AuthorityViolation("child resource key is absent from parent authority")
            if child_limit["limit_mode"] not in _MODE_NARROWING[parent_limit["limit_mode"]]:
                raise AuthorityViolation("child limit mode relaxes parent enforcement")
            if child_limit["limit_mode"] == "OBSERVATION_ONLY":
                continue
            if parent_limit["limit_mode"] == "OBSERVATION_ONLY":
                raise AuthorityViolation("observation-only parent cannot create spend authority")
            child_ordinary = Decimal(child_limit["ordinary_limit"])
            parent_ordinary = Decimal(parent_limit["ordinary_limit"])
            child_final = Decimal(child_limit["finalization_reserve"])
            parent_final = Decimal(parent_limit["finalization_reserve"])
            if _exact_compare(child_ordinary, parent_ordinary) > 0:
                raise AuthorityViolation("child ordinary capacity expands parent authority")
            if _exact_compare(child_final, parent_final) > 0:
                raise AuthorityViolation("child finalization reserve expands parent authority")

    @staticmethod
    def _insert_grant(conn: sqlite3.Connection, grant: dict[str, Any], fingerprint: str) -> None:
        scope = grant["scope"]
        conn.execute(
            """
            INSERT INTO grants(
                grant_id, fingerprint, grant_json, parent_grant_id, authority_type, scope_ref,
                candidate_ref, route_ref, attempt_limit, valid_until
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                grant["artifact_id"], fingerprint, ResourceLedger._canonical_json(grant), grant["parent_grant_ref"],
                grant["authority_source"]["authority_type"], scope["scope_ref"], scope["candidate_ref"],
                scope["route_ref"], grant["attempt_limit"], grant["valid_until"],
            ),
        )
        conn.executemany(
            "INSERT INTO grant_resource_classes(grant_id, resource_class) VALUES (?, ?)",
            [(grant["artifact_id"], item) for item in scope["resource_classes"]],
        )
        conn.executemany(
            """
            INSERT INTO grant_limits(
                grant_id, resource_class, dimension, limit_mode, ordinary_limit, finalization_reserve
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    grant["artifact_id"], item["resource_class"], item["dimension"], item["limit_mode"],
                    item["ordinary_limit"], item["finalization_reserve"],
                )
                for item in grant["limits"]
            ],
        )
        conn.executemany(
            "INSERT INTO grant_finalization_purposes(grant_id, purpose) VALUES (?, ?)",
            [(grant["artifact_id"], purpose) for purpose in grant["finalization_policy"]["allowed_purposes"]],
        )

    def get_grant(self, grant_id: str) -> dict[str, Any]:
        self._require_id(grant_id, "grant_id")
        conn = self._connect()
        try:
            row = self._row_grant(conn, grant_id)
            grant = json.loads(row["grant_json"])
        finally:
            conn.close()
        for item in grant["limits"]:
            if item["ordinary_limit"] is not None:
                item["ordinary_limit"] = Decimal(item["ordinary_limit"])
                item["finalization_reserve"] = Decimal(item["finalization_reserve"])
        return grant

    def get_scope_relation_evidence(self, grant_id: str) -> dict[str, str] | None:
        self._require_id(grant_id, "grant_id")
        conn = self._connect()
        try:
            self._row_grant(conn, grant_id)
            row = conn.execute(
                "SELECT child_scope_ref, parent_scope_ref, evidence_ref FROM grant_scope_relation_evidence WHERE child_grant_id = ?",
                (grant_id,),
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            conn.close()

    def get_resource_state(self, grant_id: str, resource_class: str, dimension: str) -> dict[str, Any]:
        self._require_id(grant_id, "grant_id")
        self._require_id(resource_class, "resource_class")
        self._require_id(dimension, "dimension")
        conn = self._connect()
        try:
            grant = self._row_grant(conn, grant_id)
            limit = self._limit_row(conn, grant_id, resource_class, dimension)
            now = datetime.now(timezone.utc)
            zero = Decimal("0")
            if limit["limit_mode"] == "OBSERVATION_ONLY":
                return {
                    "grant_id": grant_id,
                    "resource_class": resource_class,
                    "dimension": dimension,
                    "limit_mode": "OBSERVATION_ONLY",
                    "spend_authority": False,
                    "ordinary": {"authorized": zero, "reserved": zero, "committed": zero, "available": zero},
                    "finalization": {"authorized": zero, "reserved": zero, "committed": zero, "available": zero},
                    "exhaustion_state": "EXHAUSTED",
                    "grant_expired": self._grant_expired(grant, now),
                }
            ordinary_authorized = Decimal(limit["ordinary_limit"])
            final_authorized = Decimal(limit["finalization_reserve"])
            ordinary_reserved, ordinary_committed = self._allocation_totals(
                conn, grant_id, resource_class, dimension, "ORDINARY"
            )
            final_reserved, final_committed = self._allocation_totals(
                conn, grant_id, resource_class, dimension, "FINALIZATION"
            )
            ordinary_available = _exact_subtract(ordinary_authorized, ordinary_reserved, ordinary_committed)
            final_available = _exact_subtract(final_authorized, final_reserved, final_committed)
            if _exact_compare(ordinary_available, zero) < 0 or _exact_compare(final_available, zero) < 0:
                raise AuthorityViolation("stored allocation invariant is negative")
            if _exact_compare(ordinary_available, zero) == 0 and _exact_compare(final_available, zero) == 0:
                exhaustion = "EXHAUSTED"
            elif _exact_compare(ordinary_available, zero) == 0 and _exact_compare(final_available, zero) > 0:
                exhaustion = "ORDINARY_LIMIT_EXHAUSTED_FINALIZATION_ONLY"
            else:
                exhaustion = "NOT_EXHAUSTED"
            return {
                "grant_id": grant_id,
                "resource_class": resource_class,
                "dimension": dimension,
                "limit_mode": limit["limit_mode"],
                "spend_authority": True,
                "ordinary": {
                    "authorized": ordinary_authorized,
                    "reserved": ordinary_reserved,
                    "committed": ordinary_committed,
                    "available": ordinary_available,
                },
                "finalization": {
                    "authorized": final_authorized,
                    "reserved": final_reserved,
                    "committed": final_committed,
                    "available": final_available,
                },
                "exhaustion_state": exhaustion,
                "grant_expired": self._grant_expired(grant, now),
            }
        finally:
            conn.close()

    def reserve(
        self,
        grant_id: str,
        resource_class: str,
        dimension: str,
        quantity: Any,
        reservation_id: str,
        operation_id: str,
        idempotency_key: str,
        pool: str = "ORDINARY",
        purpose: str | None = None,
        expires_at: datetime | str | None = None,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        for value, name in [
            (grant_id, "grant_id"), (resource_class, "resource_class"), (dimension, "dimension"),
            (reservation_id, "reservation_id"), (operation_id, "operation_id"), (idempotency_key, "idempotency_key"),
        ]:
            self._require_id(value, name)
        amount = self._decimal(quantity, "quantity", allow_zero=False)
        if pool not in {"ORDINARY", "FINALIZATION"}:
            raise ResourceLedgerError("pool must be ORDINARY or FINALIZATION")
        if pool == "FINALIZATION":
            if purpose not in _FINALIZATION_PURPOSES:
                raise AuthorityViolation("FINALIZATION requires an authorized frozen purpose")
        elif purpose is not None:
            raise ResourceLedgerError("ordinary reservations do not carry a finalization purpose")
        now_dt = self._now(now)
        expires_dt = self._parse_datetime(expires_at, "expires_at", nullable=True)
        if expires_dt is not None and expires_dt <= now_dt:
            raise ResourceLedgerError("expires_at must be after reservation creation time")
        request = {
            "grant_id": grant_id,
            "resource_class": resource_class,
            "dimension": dimension,
            "quantity": self._decimal_text(amount),
            "reservation_id": reservation_id,
            "operation_id": operation_id,
            "pool": pool,
            "purpose": purpose,
            "expires_at": self._datetime_text(expires_dt) if expires_dt else None,
        }
        fingerprint = self._fingerprint(request)
        created_at_text = self._datetime_text(now_dt)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "RESERVE", fingerprint)
            if prior is not None:
                conn.commit()
                return prior

            existing = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
            if existing is not None:
                same = (
                    existing["grant_id"] == grant_id
                    and existing["resource_class"] == resource_class
                    and existing["dimension"] == dimension
                    and existing["quantity"] == self._decimal_text(amount)
                    and existing["operation_id"] == operation_id
                    and existing["pool"] == pool
                    and existing["purpose"] == purpose
                    and existing["expires_at"] == request["expires_at"]
                )
                if not same:
                    raise IdempotencyConflict("reservation_id is already bound to a conflicting request")
                result = self._reservation_result(existing)
                result = self._record_idempotency(conn, idempotency_key, "RESERVE", fingerprint, result)
                conn.commit()
                return result

            chain = self._ancestry(conn, grant_id)
            allocation_grants: list[sqlite3.Row] = []
            for grant_row in chain:
                if self._grant_expired(grant_row, now_dt):
                    raise GrantExpired(f"grant expired: {grant_row['grant_id']}")
                limit = self._limit_row(conn, grant_row["grant_id"], resource_class, dimension)
                if limit["limit_mode"] == "OBSERVATION_ONLY":
                    raise AuthorityViolation("OBSERVATION_ONLY creates no spend authority")
                if pool == "FINALIZATION":
                    allowed = conn.execute(
                        "SELECT 1 FROM grant_finalization_purposes WHERE grant_id = ? AND purpose = ?",
                        (grant_row["grant_id"], purpose),
                    ).fetchone()
                    if allowed is None:
                        raise AuthorityViolation("finalization purpose is not authorized throughout the grant chain")
                authorized = Decimal(
                    limit["ordinary_limit"] if pool == "ORDINARY" else limit["finalization_reserve"]
                )
                reserved, committed = self._allocation_totals(
                    conn, grant_row["grant_id"], resource_class, dimension, pool
                )
                used_after = _exact_sum([committed, reserved, amount])
                if _exact_compare(used_after, authorized) > 0:
                    raise InsufficientCapacity(
                        f"insufficient {pool.lower()} capacity at grant {grant_row['grant_id']}"
                    )
                allocation_grants.append(grant_row)

            conn.execute(
                """
                INSERT INTO reservations(
                    reservation_id, grant_id, resource_class, dimension, quantity, operation_id,
                    pool, purpose, created_at, expires_at, status, committed_quantity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'RESERVED', NULL)
                """,
                (
                    reservation_id, grant_id, resource_class, dimension, self._decimal_text(amount), operation_id,
                    pool, purpose, created_at_text, request["expires_at"],
                ),
            )
            for grant_row in allocation_grants:
                conn.execute(
                    """
                    INSERT INTO reservation_allocations(
                        reservation_id, grant_id, resource_class, dimension, pool, reserved, committed
                    ) VALUES (?, ?, ?, ?, ?, ?, '0')
                    """,
                    (
                        reservation_id, grant_row["grant_id"], resource_class, dimension, pool,
                        self._decimal_text(amount),
                    ),
                )
            created = conn.execute(
                "SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)
            ).fetchone()
            if created is None:
                raise ResourceLedgerError("reservation mutation did not materialize")
            result = self._record_idempotency(
                conn, idempotency_key, "RESERVE", fingerprint, self._reservation_result(created)
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @classmethod
    def _reservation_result(cls, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "reservation_id": row["reservation_id"],
            "grant_id": row["grant_id"],
            "resource_class": row["resource_class"],
            "dimension": row["dimension"],
            "quantity": Decimal(row["quantity"]),
            "operation_id": row["operation_id"],
            "pool": row["pool"],
            "purpose": row["purpose"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "status": row["status"],
            "committed_quantity": (
                Decimal(row["committed_quantity"]) if row["committed_quantity"] is not None else None
            ),
        }

    def commit(
        self,
        reservation_id: str,
        quantity: Any,
        idempotency_key: str,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        self._require_id(reservation_id, "reservation_id")
        self._require_id(idempotency_key, "idempotency_key")
        actual = self._decimal(quantity, "quantity")
        now_dt = self._now(now)
        request = {"reservation_id": reservation_id, "quantity": self._decimal_text(actual)}
        fingerprint = self._fingerprint(request)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "COMMIT", fingerprint)
            if prior is not None:
                conn.commit()
                return prior
            row = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
            if row is None:
                raise InvalidReservationTransition("reservation does not exist")
            if row["status"] == "COMMITTED":
                if _exact_compare(Decimal(row["committed_quantity"]), actual) != 0:
                    raise InvalidReservationTransition("reservation already committed with a different quantity")
                result = self._record_idempotency(
                    conn, idempotency_key, "COMMIT", fingerprint, self._reservation_result(row)
                )
                conn.commit()
                return result
            if row["status"] != "RESERVED":
                raise InvalidReservationTransition(f"cannot commit reservation in state {row['status']}")
            expires_raw = row["expires_at"]
            if expires_raw is not None:
                expires = self._parse_datetime(expires_raw, "expires_at")
                if expires is None:
                    raise ResourceLedgerError("stored reservation expiry is malformed")
                if expires <= now_dt:
                    self._expire_one(conn, reservation_id)
                    conn.commit()
                    raise InvalidReservationTransition("reservation has expired")
            reserved = Decimal(row["quantity"])
            if _exact_compare(actual, reserved) > 0:
                raise InvalidReservationTransition("committed quantity exceeds reserved authority")
            conn.execute(
                "UPDATE reservation_allocations SET reserved = '0', committed = ? WHERE reservation_id = ?",
                (self._decimal_text(actual), reservation_id),
            )
            conn.execute(
                "UPDATE reservations SET status = 'COMMITTED', committed_quantity = ? WHERE reservation_id = ?",
                (self._decimal_text(actual), reservation_id),
            )
            updated = conn.execute(
                "SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)
            ).fetchone()
            if updated is None:
                raise ResourceLedgerError("reservation commit did not materialize")
            result = self._record_idempotency(
                conn, idempotency_key, "COMMIT", fingerprint, self._reservation_result(updated)
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release(
        self,
        reservation_id: str,
        idempotency_key: str,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        self._require_id(reservation_id, "reservation_id")
        self._require_id(idempotency_key, "idempotency_key")
        if now is not None:
            self._now(now)
        request = {"reservation_id": reservation_id}
        fingerprint = self._fingerprint(request)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "RELEASE", fingerprint)
            if prior is not None:
                conn.commit()
                return prior
            row = conn.execute("SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)).fetchone()
            if row is None:
                raise InvalidReservationTransition("reservation does not exist")
            if row["status"] == "RELEASED":
                result = self._record_idempotency(
                    conn, idempotency_key, "RELEASE", fingerprint, self._reservation_result(row)
                )
                conn.commit()
                return result
            if row["status"] != "RESERVED":
                raise InvalidReservationTransition(f"cannot release reservation in state {row['status']}")
            conn.execute(
                "UPDATE reservation_allocations SET reserved = '0' WHERE reservation_id = ?", (reservation_id,)
            )
            conn.execute(
                "UPDATE reservations SET status = 'RELEASED' WHERE reservation_id = ?", (reservation_id,)
            )
            updated = conn.execute(
                "SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)
            ).fetchone()
            if updated is None:
                raise ResourceLedgerError("reservation release did not materialize")
            result = self._record_idempotency(
                conn, idempotency_key, "RELEASE", fingerprint, self._reservation_result(updated)
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _expire_one(conn: sqlite3.Connection, reservation_id: str) -> None:
        conn.execute(
            "UPDATE reservation_allocations SET reserved = '0' WHERE reservation_id = ?", (reservation_id,)
        )
        conn.execute(
            "UPDATE reservations SET status = 'EXPIRED' WHERE reservation_id = ? AND status = 'RESERVED'",
            (reservation_id,),
        )

    def expire_reservations(self, now: datetime | str) -> list[str]:
        now_dt = self._now(now)
        conn = self._connect()
        try:
            self._begin_write(conn)
            candidates = conn.execute(
                """
                SELECT reservation_id, expires_at
                FROM reservations
                WHERE status = 'RESERVED' AND expires_at IS NOT NULL
                ORDER BY reservation_id
                """
            ).fetchall()
            ids: list[str] = []
            for row in candidates:
                parsed = self._parse_datetime(row["expires_at"], "expires_at")
                if parsed is None:
                    raise ResourceLedgerError("stored reservation expiry is malformed")
                if parsed <= now_dt:
                    ids.append(row["reservation_id"])
            for reservation_id in ids:
                self._expire_one(conn, reservation_id)
            conn.commit()
            return ids
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def claim_attempt(
        self,
        grant_id: str,
        operation_id: str,
        idempotency_key: str,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        self._require_id(grant_id, "grant_id")
        self._require_id(operation_id, "operation_id")
        self._require_id(idempotency_key, "idempotency_key")
        now_dt = self._now(now)
        request = {"grant_id": grant_id, "operation_id": operation_id}
        fingerprint = self._fingerprint(request)
        conn = self._connect()
        try:
            self._begin_write(conn)
            prior = self._idempotency_lookup(conn, idempotency_key, "ATTEMPT", fingerprint)
            if prior is not None:
                conn.commit()
                return prior
            existing = conn.execute(
                "SELECT claim_id, created_at FROM attempt_claims WHERE grant_id = ? AND operation_id = ?",
                (grant_id, operation_id),
            ).fetchone()
            if existing is not None:
                result = {
                    "claim_id": existing["claim_id"],
                    "grant_id": grant_id,
                    "operation_id": operation_id,
                    "created_at": existing["created_at"],
                }
                result = self._record_idempotency(conn, idempotency_key, "ATTEMPT", fingerprint, result)
                conn.commit()
                return result
            chain = self._ancestry(conn, grant_id)
            bounded: list[sqlite3.Row] = []
            for grant_row in chain:
                if self._grant_expired(grant_row, now_dt):
                    raise GrantExpired(f"grant expired: {grant_row['grant_id']}")
                if grant_row["attempt_limit"] is None:
                    continue
                count_row = conn.execute(
                    "SELECT COUNT(*) AS n FROM attempt_allocations WHERE grant_id = ?",
                    (grant_row["grant_id"],),
                ).fetchone()
                if count_row is None:
                    raise ResourceLedgerError("attempt allocation count could not be read")
                claimed = int(count_row["n"])
                if claimed >= int(grant_row["attempt_limit"]):
                    raise InsufficientCapacity(f"attempt authority exhausted at grant {grant_row['grant_id']}")
                bounded.append(grant_row)
            cursor = conn.execute(
                "INSERT INTO attempt_claims(grant_id, operation_id, created_at) VALUES (?, ?, ?)",
                (grant_id, operation_id, self._datetime_text(now_dt)),
            )
            claim_id = int(cursor.lastrowid)
            for grant_row in bounded:
                conn.execute(
                    "INSERT INTO attempt_allocations(claim_id, grant_id) VALUES (?, ?)",
                    (claim_id, grant_row["grant_id"]),
                )
            result = {
                "claim_id": claim_id,
                "grant_id": grant_id,
                "operation_id": operation_id,
                "created_at": self._datetime_text(now_dt),
            }
            result = self._record_idempotency(conn, idempotency_key, "ATTEMPT", fingerprint, result)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
