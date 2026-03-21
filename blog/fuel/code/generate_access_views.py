#!/usr/bin/env python3
"""
generate_access_views.py — Create role-scoped views from classification metadata.

Reads field_classifications and role_access_tiers from a DuckDB database
and generates CREATE VIEW statements that enforce access control at the
schema level.

Fields above the role's sensitivity ceiling are:
  - masked (one level above ceiling — hashed with md5)
  - excluded (two or more levels above — not in the view at all)

From Ratchet Fuel Post 7: The Classification Engine
https://judgementalmonad.com/blog/fuel/07-the-classification-engine

Usage:
    python generate_access_views.py --db analytics.duckdb --role marketing_ops
    python generate_access_views.py --db analytics.duckdb --all-roles
"""

import argparse

import duckdb


def generate_view(con: duckdb.DuckDBPyConnection, table_name: str, role: str) -> str | None:
    """Generate a CREATE VIEW statement for the given role and table."""
    fields = con.execute("""
        SELECT
            fc.field_name,
            fc.sensitivity_level,
            so_field.rank AS field_rank,
            so_role.rank AS role_max_rank
        FROM field_classifications fc
        JOIN sensitivity_ordering so_field
            ON fc.sensitivity_level = so_field.level
        JOIN role_access_tiers rat
            ON rat.role = ?
        JOIN sensitivity_ordering so_role
            ON rat.max_sensitivity = so_role.level
        WHERE fc.table_name = ?
        ORDER BY fc.field_name
    """, [role, table_name]).fetchall()

    if not fields:
        return None

    select_parts = []
    for field_name, sens_level, field_rank, role_max_rank in fields:
        if field_rank <= role_max_rank:
            # Visible: include as-is
            select_parts.append(f"    {field_name}")
        elif field_rank == role_max_rank + 1:
            # One level above ceiling: mask with hash
            select_parts.append(
                f"    md5({field_name}::VARCHAR) AS {field_name}"
            )
        # else: excluded entirely — field does not appear in the view

    if not select_parts:
        return None

    view_name = f"{table_name}_{role}_v"
    select_clause = ",\n".join(select_parts)
    return f"CREATE OR REPLACE VIEW {view_name} AS\nSELECT\n{select_clause}\nFROM {table_name};"


def generate_all_views(db_path: str, role: str, execute: bool = True):
    """Generate views for all classified tables for the given role."""
    con = duckdb.connect(db_path)

    tables = con.execute("""
        SELECT DISTINCT table_name
        FROM field_classifications
    """).fetchall()

    for (table_name,) in tables:
        ddl = generate_view(con, table_name, role)
        if ddl:
            print(f"-- View for {role} on {table_name}")
            print(ddl)
            print()
            if execute:
                con.execute(ddl)
                print(f"-- Created: {table_name}_{role}_v\n")

    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate role-scoped access views from classification metadata"
    )
    parser.add_argument("--db", required=True, help="Path to DuckDB database")
    parser.add_argument("--role", help="Role to generate views for")
    parser.add_argument("--all-roles", action="store_true",
                        help="Generate views for all roles in role_access_tiers")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print DDL without executing")
    args = parser.parse_args()

    if args.all_roles:
        con = duckdb.connect(args.db)
        roles = [r[0] for r in con.execute(
            "SELECT role FROM role_access_tiers"
        ).fetchall()]
        con.close()
        for role in roles:
            print(f"\n{'='*60}")
            print(f"  Role: {role}")
            print(f"{'='*60}\n")
            generate_all_views(args.db, role, execute=not args.dry_run)
    elif args.role:
        generate_all_views(args.db, args.role, execute=not args.dry_run)
    else:
        parser.error("Either --role or --all-roles is required")
